"""Tests for the /conversations/{id}/messages endpoints: list (with limit) and get.

Messages are only created by the chat endpoints, so the tests use /chat with the fake AI.
"""


def _chat(client, conversation_id, question):
    """Ask through /chat, which saves two messages: the question and the fake answer."""
    client.post(f"/conversations/{conversation_id}/chat", json={"question": question})


def test_get_message(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    _chat(client, conversation_id, "Hello")
    message_id = client.get(f"/conversations/{conversation_id}/messages").json()[0]["id"]

    response = client.get(f"/conversations/{conversation_id}/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["role"] == "user"
    assert response.json()["content"] == "Hello"


def test_messages_of_missing_conversation_returns_404(client):
    response = client.get("/conversations/99/messages")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_list_messages_with_limit(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    for question in ["first", "second"]:
        _chat(client, conversation_id, question)  # 4 messages in total

    response = client.get(f"/conversations/{conversation_id}/messages", params={"limit": 2})

    # Only the last turn, still in chronological order
    assert [m["content"] for m in response.json()] == ["second", "Answer to: second"]


def test_get_message_from_another_conversation_returns_404(client, fake_llm):
    """A message can only be read through the conversation it belongs to."""
    first_id = client.post("/conversations", json={}).json()["id"]
    second_id = client.post("/conversations", json={}).json()["id"]
    _chat(client, first_id, "Hello")
    message_id = client.get(f"/conversations/{first_id}/messages").json()[0]["id"]

    response = client.get(f"/conversations/{second_id}/messages/{message_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"
