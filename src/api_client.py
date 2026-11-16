"""HTTP client for the assistant backend: conversations, messages and chat."""

import httpx

API_URL = "http://127.0.0.1:8000"

# One client for the whole app, it reuses the connection between requests
http_client = httpx.Client(base_url=API_URL, timeout=5.0)


def create_conversation(title=None):
    """Create a conversation and return it as a dict."""
    response = http_client.post("/conversations", json={"title": title})
    response.raise_for_status()
    return response.json()


def get_latest_conversation():
    """Return the newest conversation, or None if there are none."""
    response = http_client.get("/conversations")
    response.raise_for_status()
    conversations = response.json()
    return conversations[0] if conversations else None


def get_messages(conversation_id, limit=None):
    """Return the conversation's messages, oldest first (only the last `limit` if given)."""
    params = {"limit": limit} if limit is not None else {}
    response = http_client.get(f"/conversations/{conversation_id}/messages", params=params)
    response.raise_for_status()
    return response.json()


def chat_stream(conversation_id, question, voice=False, image=None):
    """Ask the backend (with an optional base64 screenshot) and yield the answer text as it arrives."""
    url = f"/conversations/{conversation_id}/chat/stream"
    body = {"question": question, "voice": voice, "image": image}
    # No timeout: a long answer can take more than the client's default 5 seconds
    with http_client.stream("POST", url, json=body, timeout=None) as response:
        response.raise_for_status()
        yield from response.iter_text()


if __name__ == "__main__":
    conversation = get_latest_conversation() or create_conversation()
    for text in chat_stream(conversation["id"], "Cuéntame un chiste largo"):
        print(text, end="", flush=True)
    print()
