from pynput import keyboard

HOTKEY = "<ctrl>+<shift>+<space>"


def start_hotkey(callback):
    listener = keyboard.GlobalHotKeys({HOTKEY: callback})
    listener.start()
    return listener


def on_hotkey():
    print("Shortcut detected!")


if __name__ == "__main__":
    start_hotkey(on_hotkey)
    input("Press Enter to exit\n")

