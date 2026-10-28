"""Global keyboard shortcut that works even when the terminal is not focused."""

from collections.abc import Callable

from pynput import keyboard

# pynput format: modifiers in <>, joined with +.
# Avoid <ctrl>+<alt>: on Spanish keyboards AltGr sends Ctrl+Alt (@, #, ...).
HOTKEY = "<ctrl>+<shift>+<space>"

PTT_KEY = keyboard.Key.ctrl_r  # Hold to talk; right Ctrl is rarely used alone


def start_hotkey(callback: Callable[[], None]) -> keyboard.GlobalHotKeys:
    """Start listening for HOTKEY in a background thread and return the listener.

    callback runs in the listener's thread, not the main one: keep it fast
    (e.g. just put an event in a queue) or Windows may drop the keyboard hook.
    Call .stop() on the returned listener to stop listening.
    """
    listener = keyboard.GlobalHotKeys({HOTKEY: callback})
    listener.start()
    return listener


def _on_hotkey_test():
    """Callback used only by the manual test below."""
    print("Shortcut detected!")


class PushToTalk:
    """Calls on_down when PTT_KEY is pressed and on_up when it is released."""
    
    def __init__(self, on_down: Callable[[], None], on_up: Callable[[], None]):
        self._on_down = on_down
        self._on_up = on_up
        self._active = False
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)

    def start(self):
        """Start listening in a background thread. Returns at once."""
        self._listener.start()

    def stop(self):
        """Stop listening."""
        self._listener.stop()

    def _on_press(self, key):
        if key == PTT_KEY and not self._active:
            self._active = True
            self._on_down()

    def _on_release(self, key):
        if key == PTT_KEY and self._active:
            self._active = False
            self._on_up()


# Manual test: py -m src.hotkeys, then press HOTKEY with another window focused
if __name__ == "__main__":
    ptt = PushToTalk(lambda: print("Grabando..."), lambda: print("Soltado"))
    ptt.start()
    print(f"Mantén {PTT_KEY} para hablar")
    input("Press Enter to exit\n")
    ptt.stop()