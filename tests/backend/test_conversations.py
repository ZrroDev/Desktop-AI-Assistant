"""Tests for the /conversations endpoints: create, list, get, rename and delete."""

def test_create_conversation_with_default_title(client):
    response = client.post("/conversations", json={})

    assert response.status_code == 201
    assert response.json()["title"] == "New conversation"


def test_create_conversation_with_custom_title(client):
    response = client.post("/conversations", json={"title": "Custom Title"})

    assert response.status_code == 201
    assert response.json()["title"] == "Custom Title"


def test_list_conversations_returns_newest_first(client):
    client.post("/conversations", json={"title": "First"})
    client.post("/conversations", json={"title": "Second"})

    response = client.get("/conversations")

    assert response.status_code == 200
    assert [c["title"] for c in response.json()] == ["Second", "First"]


def test_list_conversations_empty(client):
    response = client.get("/conversations")

    assert response.status_code == 200
    assert response.json() == []


def test_get_created_conversation(client):
    conversation_id = client.post("/conversations", json={"title": "Created Conversation"}).json()["id"]

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Created Conversation"


def test_get_missing_conversation_returns_404(client):
    response = client.get("/conversations/99")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_update_with_empty_body_keeps_title(client):
    conversation_id = client.post("/conversations", json={"title": "Original Title"}).json()["id"]

    client.patch(f"/conversations/{conversation_id}", json={})

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Original Title"


def test_update_conversation_title(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    client.patch(f"/conversations/{conversation_id}", json={"title": "Updated Title"})

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_conversation(client):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.delete(f"/conversations/{conversation_id}")

    assert response.status_code == 204

    response = client.get(f"/conversations/{conversation_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
