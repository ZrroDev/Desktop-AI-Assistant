"""Global keyboard shortcut that works even when the terminal is not focused."""

from collections.abc import Callable

from pynput import keyboard

# pynput format: modifiers in <>, joined with +.
# Avoid <ctrl>+<alt>: on Spanish keyboards AltGr sends Ctrl+Alt (@, #, ...).
HOTKEY = "<ctrl>+<shift>+<space>"


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


# Manual test: py -m src.hotkeys, then press HOTKEY with another window focused
if __name__ == "__main__":
    listener = start_hotkey(_on_hotkey_test)
    print(f"Listening for {HOTKEY}")
    input("Press Enter to exit\n")
    listener.stop()
