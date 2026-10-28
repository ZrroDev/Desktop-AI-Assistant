"""Small input window opened with the global hotkey to ask the assistant."""

import queue
import threading
import tkinter as tk

from src.assistant import ask, clear_history, load_history, speaker
from src.hotkeys import PushToTalk, start_hotkey
from src.screen_capture import capture_screen
from src.stt import SAMPLE_RATE, Recorder, transcribe

POLL_INTERVAL_MS = 100  # How often the Tk thread checks the hotkey queue

MIN_RECORDING_SECONDS = 0.3  # Shorter presses (e.g. right Ctrl + C) are ignored

class InputWindow:
    """Hidden window that shows up on the hotkey to type a question.

    Tkinter must only be touched from the main thread. The hotkey callback runs
    in pynput's thread, so it only puts an event in self.events; _poll reads
    that queue from the main thread and shows the window.
    """

    def __init__(self):
        # Window
        self.root = tk.Tk()
        self.root.title("Asistente")
        self.root.attributes("-topmost", True)  # Always above other windows

        # Widgets
        self.entry = tk.Entry(self.root, width=100)
        self.entry.pack()
        self.entry.focus_set()

        tk.Button(self.root, text="Borrar historial de chat", command=self.on_clear_history).pack()

        self.voice_response = tk.BooleanVar(value=True)
        tk.Checkbutton(self.root, text="Respuesta por voz", variable=self.voice_response).pack()

        self.include_capture = tk.BooleanVar(value=True)
        tk.Checkbutton(self.root, text="Incluir captura", variable=self.include_capture).pack()

        tk.Button(self.root, text="Enviar", command=self.on_submit).pack()

        # Key bindings
        self.root.bind("<Return>", self.on_submit)
        self.root.bind("<Escape>", self.on_escape)

        # Events sent from the hotkey thread to the Tk thread
        self.events = queue.Queue()

        # Screenshot taken on the hotkey, sent with the next question
        self.pending_image = None

        # Set while Claude is answering
        self.busy = threading.Event()

        # Microphone recording for push-to-talk
        self.recorder = Recorder() 

        # Start hidden: the hotkey shows it
        self.root.withdraw()

    # --- Lifecycle ---

    def run(self):
        """Load the chat history, start the hotkey listener and the Tk main loop (blocks until quit)."""
        load_history()
        self.listener = start_hotkey(lambda: self.events.put("show"))
        self.ptt = PushToTalk(lambda: self.events.put("ptt_down"), lambda: self.events.put("ptt_up"))
        self.ptt.start()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)  # Window X closes the app
        self._poll()
        self.root.mainloop()

    def quit(self):
        """Stop the hotkey listener and close the window, ending mainloop."""
        self.listener.stop()
        self.ptt.stop()
        self.root.destroy()

    # --- Window actions ---

    def show(self):
        """Bring the window to the front, ready to type."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_set()

    def on_submit(self, event=None):
        """Send the question (and the screenshot, if checked) to Claude, then hide the window."""
        # Only one question at a time: keep the text and screenshot to send
        if self.busy.is_set():
            print("Wait, there is an answer incoming")
            return

        question = self.entry.get().strip()
        if not question:
            print("Question is empty")
            return

        # Read the checkboxes here: Tk variables can only be used from the main thread
        voice = self.voice_response.get()
        image = self.pending_image if self.include_capture.get() else None
        self.pending_image = None  # Each screenshot is used only once

        self.busy.set()  # Cleared by _ask_in_background when the answer ends

        # Ask in a background thread so the window doesn't freeze while Claude answers;
        # the reply streams to the terminal (and is spoken if voice). daemon=True: it won't keep the app alive on quit
        threading.Thread(target=self._ask_in_background, args=(question, image, voice), daemon=True).start()

        self.entry.delete(0, tk.END)
        self.root.withdraw()

    def on_escape(self, event=None):
        """Discard the question and hide the window."""
        self.entry.delete(0, tk.END)
        self.root.withdraw()
        self.pending_image = None

    def on_clear_history(self):
        """Forget the conversation, unless Claude is still answering."""
        if self.busy.is_set():
            print("History cannot be cleared while the assistant is busy")
            return
        clear_history()

    # --- Internal ---

    def _ask_in_background(self, question, image, voice):
        """Runs in a worker thread: ask Claude, then mark the assistant as free."""
        try:
            ask(question, image, voice)
            if voice:
                speaker.wait()
        finally:
            self.busy.clear()

    def _poll(self):
        """Handle pending hotkey events, then reschedule itself."""
        while True:
            try:
                event = self.events.get_nowait()
                if event == "show":
                    self.pending_image = capture_screen()  # Before show(), so the window isn't in it
                    self.show()
                elif event == "ptt_down":
                    if not self.busy.is_set():
                        self.recorder.start()
                elif event == "ptt_up":
                    audio = self.recorder.stop()
                    if audio.size < MIN_RECORDING_SECONDS * SAMPLE_RATE:
                        print("No audio recorded")
                    else:
                        voice = self.voice_response.get()
                        self.busy.set()
                        threading.Thread(target=self._voice_in_background, args=(audio, voice), daemon=True).start()
            except queue.Empty:
                break
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _voice_in_background(self, audio, voice):
        """Runs in a worker thread: transcribe the recording, then ask Claude."""
        try:
            text = transcribe(audio)
            if not text:  # Only silence or noise
                return
            print(f"> {text}")
            self._ask_in_background(text, None, voice)  # Its finally clears busy
        finally:
            self.busy.clear()

if __name__ == "__main__":
    InputWindow().run()
