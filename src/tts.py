"""Text-to-speech: speaks sentences one by one in a background thread."""

import queue
import re
import threading

import pyttsx3

# Voice settings
VOICE_RATE = 180           # Words per minute (pyttsx3 default is 200, too fast in Spanish)
VOICE_KEYWORD = "spanish"  # Text to look for in the installed voice names
LEAD_SILENCE_MS = 200      # Silence before each sentence so the audio device wakes up before the first syllable


class Speaker:
    """Queue of sentences spoken in order by a worker thread.

    The pyttsx3 engine is created inside the worker thread: on Windows (SAPI5)
    it must be used from the same thread that created it.
    """

    def __init__(self):
        self.sentences = queue.Queue()  # Sentences waiting to be spoken
        threading.Thread(target=self._run, daemon=True).start()

    def speak(self, text):
        """Clean the markdown out of a sentence and queue it. Returns at once, the worker speaks it."""
        text = self._clean_for_speech(text)
        if text.strip():  # Skip lines that were only markdown (e.g. "---" or "**")
            self.sentences.put(text)

    def wait(self):
            """Block until every queued sentence has been spoken."""
            self.sentences.join()

    # --- Internal ---

    def _run(self):
        """Worker thread: speak each queued sentence with a fresh engine."""
        while True:
            text = self.sentences.get()  # Blocks until there is a sentence
            try:
                # pyttsx3 on Windows only speaks on the first runAndWait() of an engine,
                # so each sentence gets a new one
                engine = pyttsx3.init()
                engine.setProperty("rate", VOICE_RATE)
                self._pick_voice(engine)
                engine.say(f'<silence msec="{LEAD_SILENCE_MS}"/>{text}')  # SAPI (Windows) tag
                engine.runAndWait()
                engine.stop()
                del engine  # Drop it so the next init() builds a new one instead of reusing this
            finally:
                self.sentences.task_done()  # Done with this sentence, even if the engine failed

    def _pick_voice(self, engine):
        """Use the first installed voice whose name contains VOICE_KEYWORD."""
        for voice in engine.getProperty("voices"):
            if VOICE_KEYWORD in voice.name.lower():
                engine.setProperty("voice", voice.id)
                return
        print(f"No '{VOICE_KEYWORD}' voice found, using the default one")

    @staticmethod
    def _clean_for_speech(text):
        """Remove the markdown symbols the voice would read out loud."""
        text = re.sub(r"^\s*[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)  # Horizontal rules (---)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)  # List bullets (before \*+, which would eat them)
        text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)     # Headings
        text = re.sub(r"\*+", "", text)                                # Bold and italics
        text = re.sub(r"`+", "", text)                                 # Inline code and code blocks
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)          # Links: keep the text, drop the URL
        return text


if __name__ == "__main__":
    speaker = Speaker()
    speaker.speak("Hola, soy tu asistente.")
    speaker.speak("Esta es la segunda frase.")
    speaker.speak("Y esta la tercera.")
    input("Press Enter to quit!\n")  # The thread is daemon: without this the program ends before speaking