"""Terminal chat with Claude that can also send a screenshot of your screen."""

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

# Load ANTHROPIC_API_KEY from the .env file
load_dotenv()

# API client (reads the key from the environment)
client = anthropic.Anthropic()


def main():
    """Menu loop: ask, ask about the screen, clear history or quit."""
    while True:
        option = input("Send question (1), Send screenshot + question (2), Clear Chat History (c), Exit (q)? ").strip().lower()

        if option == "1":
            question = input("Your question: ")
            if question.strip():
                print(ask(question))
            else:
                print("Question is empty")
        elif option == "2":
            question = input("Your question about the screenshot: ")
            if not question.strip():
                question = "Summarize what you see on my screen."
            print(ask_about_screen(question))
        elif option == "c":
            clear_history()
            print("Chat History was cleared")
        elif option == "q":
            break
        else:
            print("Invalid option")


def ask(question):
    """Ask Claude a text-only question."""
    return _send(question, image=None)


def ask_about_screen(question):
    """Take a screenshot and ask Claude about it."""
    return _send(question, capture_screen())


def _send(question, image=None):
    """Send a question (and optional image) to Claude with the chat history."""
    content = [{"type": "text", "text": question}]
    if image:
        content.insert(0, image)  # Claude works best with the image before the text

    response = client.messages.create(
        max_tokens=MAX_TOKENS,
        messages=history + [{"role": "user", "content": content}],
        model=MODEL,
        system=SYSTEM_PROMPT,
    )

    # Keep only the text blocks of the reply
    answer = "".join(block.text for block in response.content if block.type == "text")

    # Don't save empty answers: the API rejects empty messages in the history
    if not answer:
        return f"(No answer given. Reason: {response.stop_reason})"

    add_to_history(question, answer)
    return answer


def add_to_history(question, answer):
    """Save a question/answer pair and drop the oldest turns past the limit."""
    if MAX_HISTORY_TURNS <= 0:
        return

    # Only text is stored (no screenshots) so old images aren't resent every call
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    # Keep the last N turns (2 messages each); history always starts with "user"
    del history[:-MAX_HISTORY_TURNS * 2]


def clear_history():
    """Forget the whole conversation."""
    history.clear()


if __name__ == "__main__":
    main()
