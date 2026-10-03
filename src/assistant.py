"""Terminal chat with Claude that can also send a screenshot of your screen."""

import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from src.screen_capture import capture_screen

# Model settings
MODEL = "claude-opus-5-5"
SYSTEM_PROMPT = "Always answer in Spanish."  # PROVISIONAL
MAX_TOKENS = 2048

# Conversation history, sent with every request so Claude keeps context
history = []
MAX_HISTORY_TURNS = 10  # 1 turn = question + answer

# Project root = folder above src/, no matter where the program is run from
PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = PROJECT_ROOT / "generated" / "history.json"
# TODO: when packaging the app, save it in the user data folder instead
# (platformdirs.user_data_dir), the install folder may be read-only

# Load ANTHROPIC_API_KEY from the .env file
load_dotenv()

# API client (reads the key from the environment)
client = anthropic.Anthropic()


def main():
    """Menu loop: ask, ask about the screen, clear history or quit."""
    load_history()

    while True:
        option = input("\n" + "Send question (1), Send screenshot + question (2), Clear Chat History (c), Exit (q)? ").strip().lower()

        if option == "1":
            question = input("\n" + "Your question: ")
            if question.strip():
                print("\n")
                ask(question)
            else:
                print("\n" + "Question is empty")
        elif option == "2":
            question = input("\n" + "Your question about the screenshot: ")
            if not question.strip():
                question = "Summarize what you see on my screen."
            print("\n")
            ask_about_screen(question)
        elif option == "c":
            clear_history()
            print("\n" + "Chat History was cleared")
        elif option == "q":
            break
        else:
            print("\n" + "Invalid option")


def ask(question):
    """Ask Claude a text-only question."""
    return _send(question, image=None)


def ask_about_screen(question):
    """Take a screenshot and ask Claude about it."""
    return _send(question, capture_screen())


def _send(question, image=None):
    """Send a question (and optional image) to Claude, print the reply as it streams and return it (None on error)."""
    content = [{"type": "text", "text": question}]
    if image:
        content.insert(0, image)  # Claude works best with the image before the text

    # Stream the reply as it arrives
    # On API errors print a message and stop, without touching the history
    try:
        with client.messages.stream(
            max_tokens=MAX_TOKENS,
            messages=history + [{"role": "user", "content": content}],
            model=MODEL,
            system=SYSTEM_PROMPT,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            print()
            response = stream.get_final_message()
    except anthropic.AuthenticationError:
        print("\n" + "(Error: invalid or missing API key. Check ANTHROPIC_API_KEY in .env)")
        return
    except anthropic.RateLimitError:
        print("\n" + "(Error: too many requests. Wait a moment and try again)")
        return
    except anthropic.APIConnectionError:
        print("\n" + "(Error: could not connect to the API. Check your internet connection)")
        return
    except anthropic.APIStatusError as e:
        print("\n" + f"(API error {e.status_code}: {e.message})")
        return

    # Keep only the text blocks of the reply
    answer = "".join(block.text for block in response.content if block.type == "text")

    # Don't save empty answers: the API rejects empty messages in the history
    if not answer:
        print(f"(No answer given. Reason: {response.stop_reason})")
        return

    add_to_history(question, answer)
    return answer


def load_history():
    """Restore the conversation saved in HISTORY_FILE, if there is one."""
    if not HISTORY_FILE.exists():
        return

    # A broken or unreadable file shouldn't stop the chat: start a new history
    try:
        with HISTORY_FILE.open(encoding="utf-8") as f:
            history.extend(json.load(f))
    except (json.JSONDecodeError, OSError) as e:
        print("\n" + f"Could not load history, starting a new one. Error: {e}")
        return

    # Trim in case MAX_HISTORY_TURNS was lowered since the last save
    del history[:-MAX_HISTORY_TURNS * 2]


def save_history():
    """Write the current history to HISTORY_FILE (overwrites it)."""
    # If saving fails the chat keeps working, the history is still in memory
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = HISTORY_FILE.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        tmp_file.replace(HISTORY_FILE)  # Atomic swap: the file is either old or new, never half-written
    except OSError as e:
        print("\n" + f"Could not save history: {e}")


def add_to_history(question, answer):
    """Save a question/answer pair, drop the oldest turns past the limit and write it to disk."""
    if MAX_HISTORY_TURNS <= 0:
        return

    # Only text is stored (no screenshots) so old images aren't resent every call
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    # Keep the last N turns (2 messages each); history always starts with "user"
    del history[:-MAX_HISTORY_TURNS * 2]

    save_history()


def clear_history():
    """Forget the whole conversation, also in HISTORY_FILE."""
    history.clear()
    save_history()


if __name__ == "__main__":
    main()
