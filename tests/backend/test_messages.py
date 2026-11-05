"""Tests for the /conversations/{id}/messages endpoints: add, list (with limit), get and validation."""

def test_create_message(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/messages", json={"role": "user", "content": "Message content"})

    assert response.status_code == 201
    assert response.json()["content"] == "Message content"


def test_get_created_message(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    message_id = client.post(f"/conversations/{conversation_id}/messages", json={"role": "user", "content": "Message content"}).json()["id"]

    response = client.get(f"/conversations/{conversation_id}/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["content"] == "Message content"


def test_message_on_missing_conversations_returns_404(client):
    response = client.post("/conversations/99/messages", json={"role": "user", "content": "Message content"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_list_messages_with_limit(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    for text in ["first", "second", "third"]:
        client.post(f"/conversations/{conversation_id}/messages", json={"role": "user", "content": f"{text} message"})

    response = client.get(f"/conversations/{conversation_id}/messages", params={"limit": 2})

    assert [m["content"] for m in response.json()] == ["second message", "third message"]


def test_get_message_from_another_conversation_returns_404(client):
    """A message can only be read through the conversation it belongs to."""
    first_id = client.post("/conversations", json={}).json()["id"]
    second_id = client.post("/conversations", json={}).json()["id"]
    message_id = client.post(f"/conversations/{first_id}/messages", json={"role": "user", "content": "Message content"}).json()["id"]

    response = client.get(f"/conversations/{second_id}/messages/{message_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"


def test_validate_message_role(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    response = client.post(f"/conversations/{conversation_id}/messages", json={"role": "undefined", "content": "Message content"})

    assert response.status_code == 422


def test_validate_message_content(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    response = client.post(f"/conversations/{conversation_id}/messages", json={"role": "user", "content": ""})

    assert response.status_code == 422
