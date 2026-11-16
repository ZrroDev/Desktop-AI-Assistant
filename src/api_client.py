"""HTTP client for the assistant backend: conversations and messages."""

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


def add_message(conversation_id, role, content):
    """Save one message in the conversation and return it."""
    body = {
        "role": role,
        "content": content
    }
    response = http_client.post(f"/conversations/{conversation_id}/messages", json=body)
    response.raise_for_status()
    return response.json()


def chat_stream(conversation_id, question, voice=False):
    """Ask the backend and yield the answer text as it arrives."""
    url = f"/conversations/{conversation_id}/chat/stream"
    with http_client.stream("POST", url, json={"question": question, "voice": voice}, timeout=None) as response:
        response.raise_for_status()
        yield from response.iter_text()


if __name__ == "__main__":
    conversation = get_latest_conversation() or create_conversation()
    for text in chat_stream(conversation["id"], "Cuéntame un chiste largo"):
        print(text, end="", flush=True)
    print()
