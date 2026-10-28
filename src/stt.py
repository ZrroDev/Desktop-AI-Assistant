"""Speech-to-text: record from the microphone and transcribe locally with faster-whisper."""

import importlib
import os
from pathlib import Path
import sys
import time

from faster_whisper import WhisperModel
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000  # Whisper expects 16 kHz mono audio
MODEL_SIZE = "medium"  # "small"/"base" are faster but less accurate in Spanish; medium is fast enough on GPU
LANGUAGE = "es"


# --- Model loading ---

def _add_cuda_dll_dirs() -> None:
    """Let Windows find the CUDA DLLs installed with requirements-gpu.txt.

    pip puts them in site-packages/nvidia/<package>/bin, which is not on the
    DLL search path. Does nothing if the packages are not installed.
    """
    if sys.platform != "win32":
        return
    for package_name in ("nvidia.cublas", "nvidia.cudnn"):
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            continue

        # __path__, not __file__: these packages may have no __init__.py
        dll_dir = Path(package.__path__[0]) / "bin"
        if not dll_dir.is_dir():
            continue
        os.add_dll_directory(str(dll_dir))
        # CTranslate2 loads cuBLAS with the classic Windows search, which reads PATH (this process only)
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ["PATH"]


def _load_model() -> WhisperModel:
    """Load the model on the NVIDIA GPU if it works, otherwise on the CPU."""
    _add_cuda_dll_dirs()
    try:
        gpu_model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")
        # Warm-up: a missing DLL only fails when the encoder runs, not when the model loads.
        # No vad_filter here, or the silence would be skipped and the encoder would never run
        segments, _ = gpu_model.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language=LANGUAGE)
        list(segments)  # segments is a lazy generator: consuming it does the work
        print("Speech-to-text on GPU")
        return gpu_model
    except (RuntimeError, ValueError) as error:
        print(f"GPU not available, using CPU ({error})")
        return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


# Loaded once on import, it takes a few seconds
model = _load_model()


# --- Recording and transcription ---

class Recorder:
    """Records from the default microphone between start() and stop().

    sounddevice calls _callback from its own audio thread with small chunks of
    audio while the stream is open; stop() joins them into a single array.
    """

    def __init__(self):
        self._chunks = []  # Audio chunks of the current recording, in order
        self._stream = None  # Open sd.InputStream while recording, else None

    def start(self):
        """Open the microphone and start collecting audio. Returns at once."""
        self._chunks = []
        self._stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=self._callback)
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Close the microphone and return everything recorded as a flat float32 array."""
        if self._stream is None:  # stop() without start(): nothing recorded
            return np.zeros(0, dtype=np.float32)

        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._chunks).flatten()  # Chunks of shape (frames, 1) -> one (samples,) array

    def _callback(self, indata, frames, time_info, status):
        """Audio thread: store a chunk. Keep it fast, nothing else runs here."""
        # copy() is required: sounddevice reuses the indata buffer for the next chunk
        self._chunks.append(indata.copy())


def transcribe(audio: np.ndarray) -> str:
    """Return the text spoken in `audio`, or an empty string if nobody spoke."""
    # vad_filter skips the silent parts before transcribing
    segments, _ = model.transcribe(audio, language=LANGUAGE, vad_filter=True)
    return "".join(segment.text for segment in segments).strip()


# Manual test: py -m src.stt, press Enter, speak, press Enter again
if __name__ == "__main__":
    recorder = Recorder()
    input("Enter para hablar")  # input() only waits here, the typed text is ignored
    recorder.start()
    input("Enter para parar")
    audio = recorder.stop()
    print("Transcribiendo...")
    start = time.perf_counter()
    text = transcribe(audio)
    elapsed = time.perf_counter() - start
    print(f"{text}  ({elapsed:.2f} s)")
