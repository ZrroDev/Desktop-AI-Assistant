"""Tests for the /conversations/{id}/chat endpoint, with the AI replaced by a fake."""

import pytest

from backend.llm_service import LLMError
from backend.routers import chat


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the real AI call with a fake that answers instantly and records what it receives."""
    calls = []

    def fake_generate_answer(history, question, voice=False):
        calls.append({"history": history, "question": question, "voice": voice})
        return f"Answer to: {question}"

    monkeypatch.setattr(chat, "generate_answer", fake_generate_answer)
    return calls


def test_chat_returns_and_saves_the_turn(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/chat", json={"question": "Hello"})

    assert response.status_code == 200
    assert response.json()["content"] == "Answer to: Hello"
    messages = client.get(f"/conversations/{conversation_id}/messages").json()
    assert [(m["role"], m["content"]) for m in messages] == [("user", "Hello"), ("assistant", "Answer to: Hello")]


def test_chat_stream_sends_text_and_saves_the_turn(client, monkeypatch):
    def fake_stream_answer(history, question, voice=False):
        yield "Answer "
        yield "to: "
        yield question

    monkeypatch.setattr(chat, "stream_answer", fake_stream_answer)
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/chat/stream", json={"question": "Hello"})

    assert response.text == "Answer to: Hello"
    messages = client.get(f"/conversations/{conversation_id}/messages").json()
    assert [m["content"] for m in messages] == ["Hello", "Answer to: Hello"]


def test_chat_sends_previous_turns_as_history(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    client.post(f"/conversations/{conversation_id}/chat", json={"question": "First"})
    client.post(f"/conversations/{conversation_id}/chat", json={"question": "Second"})

    assert fake_llm[1]["history"] == [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Answer to: First"},
    ]


def test_chat_passes_voice_flag_to_the_ai(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]
    client.post(f"/conversations/{conversation_id}/chat", json={"question": "speaked question", "voice": True})

    assert fake_llm[0]["voice"] is True


def test_chat_on_missing_conversation_returns_404(client, fake_llm):
    response = client.post(f"/conversations/0/chat", json={"question": "Hello"})

    assert response.status_code == 404
    assert fake_llm == []  # The AI is never called


def test_chat_with_empty_question_returns_422(client, fake_llm):
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/chat", json={"question": ""}, )

    assert response.status_code == 422
    assert fake_llm == []


def test_chat_with_empty_answer_returns_502(client, monkeypatch):
    monkeypatch.setattr(chat, "generate_answer", lambda history, question, voice=False: "")

    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/chat", json={"question": "Hello"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Assistant returned an empty answer"
    assert client.get(f"/conversations/{conversation_id}/messages").json() == []  # Nothing saved


def test_chat_when_ai_fails_returns_502(client, monkeypatch):
    def failing_generate_answer(history, question, voice=False):
        raise LLMError("AI is down")

    monkeypatch.setattr(chat, "generate_answer", failing_generate_answer)
    conversation_id = client.post("/conversations", json={}).json()["id"]

    response = client.post(f"/conversations/{conversation_id}/chat", json={"question": "Hello"})

    assert response.status_code == 502
