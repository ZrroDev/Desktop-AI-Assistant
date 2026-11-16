"""Shared fixtures for the backend tests. Each test gets its own empty in-memory database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.db import _enable_foreign_keys, get_session
from backend.main import app
from backend.routers import chat


@pytest.fixture
def client():
    """TestClient whose endpoints use a fresh in-memory database instead of assistant.db."""
    # In-memory database: created empty for each test, gone when the test ends
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", _enable_foreign_keys)
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    # Endpoints that ask for get_session get the test database instead
    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def fake_llm(monkeypatch):
    """Replace the real AI call with a fake that answers instantly and records what it receives."""
    calls = []

    def fake_generate_answer(history, question, voice=False, image=None):
        calls.append({"history": history, "question": question, "voice": voice, "image": image})
        return f"Answer to: {question}"

    monkeypatch.setattr(chat, "generate_answer", fake_generate_answer)
    return calls
