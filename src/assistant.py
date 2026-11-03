"""Claude client: send a question (optionally with a screenshot) and keep the chat history."""

import httpx
import re

import anthropic
from dotenv import load_dotenv

from src import api_client
from src.tts import Speaker

# Model settings
MODEL = "claude-opus-5-5"
LANGUAGE_PROMPT = "Always answer in Spanish."  # PROVISIONAL
# Added to the system prompt when the reply will be spoken
VOICE_PROMPT = (
    "Your reply will be read aloud by a text-to-speech engine, so write it to be heard, not read. "
    "Answer in 1 to 3 short sentences of plain conversational text: no markdown, lists, tables, "
    "code, URLs or emojis. If the question needs a longer answer, give the key point and offer "
    "to go into more detail."
)
MAX_TOKENS = 2048

# Conversation history, sent with every request so Claude keeps context
history = []
MAX_HISTORY_TURNS = 10  # 1 turn = question + answer
conversation_id = None # Current conversation in the backend (None = backend unreachable, not saved)

# Load ANTHROPIC_API_KEY from the .env file
load_dotenv()

# API client (reads the key from the environment)
client = anthropic.Anthropic()

# Voice output (starts its own worker thread)
speaker = Speaker()

# A sentence ends at . ! ? followed by a space, or at a line break
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def ask(question, image=None, voice=False):
    """Send a question (and optional image) to Claude, print the reply as it streams and return it (None on error).

    With voice=True the reply is also spoken sentence by sentence, and Claude is asked to keep it short.
    """
    content = [{"type": "text", "text": question}]
    if image:
        content.insert(0, image)  # Claude works best with the image before the text

    # Voice replies get the extra VOICE_PROMPT rules
    system_prompt = LANGUAGE_PROMPT
    if voice:
        system_prompt += "\n" + VOICE_PROMPT

    # Stream the reply as it arrives
    # On API errors print a message and stop, without touching the history
    try:
        with client.messages.stream(
            max_tokens=MAX_TOKENS,
            messages=history + [{"role": "user", "content": content}],
            model=MODEL,
            system=system_prompt,
        ) as stream:
            buffer = ""  # Streamed text not spoken yet
            for text in stream.text_stream:
                print(text, end="", flush=True)

                # Speak each sentence as soon as it is complete, keep the rest for later
                if voice:
                    buffer += text
                    sentences, buffer = _split_sentences(buffer)
                    for sentence in sentences:
                        if sentence.strip():
                            speaker.speak(sentence)

            # The last sentence may end without a space after the period
            if voice and buffer.strip():
                speaker.speak(buffer)
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


def _split_sentences(buffer):
    """Return (finished sentences, unfinished rest) from the streamed text."""
    parts = SENTENCE_END.split(buffer)
    return parts[:-1], parts[-1]


def load_history():
    """Continue the latest conversation from the backend, or start one if there are none."""
    global conversation_id
    try:
        conversation = api_client.get_latest_conversation() or api_client.create_conversation()
        conversation_id = conversation["id"]
        messages = api_client.get_messages(conversation_id, limit=MAX_HISTORY_TURNS * 2)
    except httpx.HTTPError as e:
        print("\n" + f"Backend not available, the chat won't be saved. Error: {e}")
        return

    history.extend({"role": m["role"], "content": m["content"]} for m in messages)
    # Assistant needs the history to start with a user message
    while history and history[0]["role"] != "user":
        history.pop(0)


def add_to_history(question, answer):
    """Keep the turn in memory (last N turns only) and save it in the backend."""
    if MAX_HISTORY_TURNS > 0:
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        del history[:-MAX_HISTORY_TURNS * 2]
    _save_turn(question, answer)


def _save_turn(question, answer):
    """Send a question/answer pair to the backend. If it fails the chat keeps working."""
    if conversation_id is None:
        return
    try:
        api_client.add_message(conversation_id, "user", question)
        api_client.add_message(conversation_id, "assistant", answer)
    except httpx.HTTPError as e:
        print("\n" + f"Could not save the messages: {e}")


def new_conversation():
    """Start a new conversation. The previous one stays saved in the backend."""
    global conversation_id
    history.clear()
    try:
        conversation_id = api_client.create_conversation()["id"]
    except httpx.HTTPError as e:
        conversation_id = None
        print("\n" + f"Could not create a conversation in the backend: {e}")
    print("New conversation started")
