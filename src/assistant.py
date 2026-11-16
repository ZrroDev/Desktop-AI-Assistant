"""Desktop side of the chat: send questions to the backend, then print and speak the streamed answer."""

import re

import httpx

from src import api_client
from src.tts import Speaker

# Current conversation in the backend (None = not connected yet, ask() retries)
conversation_id = None

# Voice output (starts its own worker thread)
speaker = Speaker()

# A sentence ends at . ! ? followed by a space, or at a line break
SENTENCE_END = re.compile(r"(?<=[.!?])\s+|\n+")


def ask(question, image=None, voice=False):
    """Send a question (and optional screenshot) to the backend, print the answer as it streams and return it.

    With voice=True the answer is also spoken sentence by sentence. Returns None on error.
    """
    if conversation_id is None and not load_conversation():
        return

    answer = ""
    buffer = ""  # Streamed text not spoken yet
    try:
        for text in api_client.chat_stream(conversation_id, question, voice, image):
            print(text, end="", flush=True)
            answer += text
            if voice:
                buffer += text
                sentences, buffer = _split_sentences(buffer)
                for sentence in sentences:
                    if sentence.strip():
                        speaker.speak(sentence)
    except httpx.HTTPError as e:
        print("\n" + f"(Error talking to the backend: {e})")
        return

    if voice and buffer.strip():  # The last sentence may end without a space after the period
        speaker.speak(buffer)
    print()
    return answer or None


def load_conversation():
    """Continue the latest conversation in the backend, or start one if there are none. Return True if it worked."""
    global conversation_id
    try:
        conversation = api_client.get_latest_conversation() or api_client.create_conversation()
    except httpx.HTTPError as e:
        print("\n" + f"(Backend not available, start it with: uvicorn backend.main:app. Error: {e})")
        return False
    conversation_id = conversation["id"]
    return True


def _split_sentences(buffer):
    """Return (finished sentences, unfinished rest) from the streamed text."""
    parts = SENTENCE_END.split(buffer)
    return parts[:-1], parts[-1]


def new_conversation():
    """Start a new conversation. The previous one stays saved in the backend."""
    global conversation_id
    try:
        conversation_id = api_client.create_conversation()["id"]
    except httpx.HTTPError as e:
        conversation_id = None
        print("\n" + f"Could not create a conversation in the backend: {e}")
    print("New conversation started")
