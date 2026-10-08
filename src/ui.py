"""Small input window opened with the global hotkey to ask the assistant."""

import queue
import tkinter as tk

from src.hotkeys import start_hotkey

POLL_INTERVAL_MS = 100  # How often the Tk thread checks the hotkey queue


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

        self.include_capture = tk.BooleanVar(value=True)
        tk.Checkbutton(self.root, text="Incluir captura", variable=self.include_capture).pack()

        tk.Button(self.root, text="Enviar", command=self.on_submit).pack()

        # Key bindings
        self.root.bind("<Return>", self.on_submit)
        self.root.bind("<Escape>", self.on_escape)

        # Events sent from the hotkey thread to the Tk thread
        self.events = queue.Queue()

        # Start hidden: the hotkey shows it
        self.root.withdraw()

    # --- Lifecycle ---

    def run(self):
        """Start the hotkey listener and the Tk main loop (blocks until quit)."""
        self.listener = start_hotkey(lambda: self.events.put("show"))
        self.root.protocol("WM_DELETE_WINDOW", self.quit)  # Window X closes the app
        self._poll()
        self.root.mainloop()

    def quit(self):
        """Stop the hotkey listener and close the window, ending mainloop."""
        self.listener.stop()
        self.root.destroy()

    # --- Window actions ---

    def show(self):
        """Bring the window to the front, ready to type."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_set()

    def on_submit(self, event=None):
        """Read the question and the capture option, then hide the window."""
        question = self.entry.get().strip()
        if not question:
            print("Question is empty")
            return

        # Provisional: step 3 will send this to the assistant
        print("question: " + question)
        print(f"include capture? {self.include_capture.get()}")

        self.entry.delete(0, tk.END)
        self.root.withdraw()

    def on_escape(self, event=None):
        """Discard the question and hide the window."""
        self.entry.delete(0, tk.END)
        self.root.withdraw()

    # --- Internal ---

    def _poll(self):
        """Handle pending hotkey events, then reschedule itself."""
        while True:
            try:
                self.events.get_nowait()
                self.show()
            except queue.Empty:
                break
        self.root.after(POLL_INTERVAL_MS, self._poll)


if __name__ == "__main__":
    InputWindow().run()
