"""Database tables and the request bodies the API accepts."""

from datetime import datetime, timezone
from typing import Literal

from sqlmodel import Field, SQLModel


def utc_now():
    """Current time in UTC, used as the default for created_at."""
    return datetime.now(timezone.utc)


# --- Tables (table=True) ---

class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)  # None until the database assigns it
    title: str = "New conversation"
    created_at: datetime = Field(default_factory=utc_now)  # default_factory: evaluated on every new row


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", ondelete="CASCADE", index=True)
    role: str  # "user" or "assistant", validated by MessageCreate
    content: str
    created_at: datetime = Field(default_factory=utc_now)


# --- Request bodies (no table=True: validated only, never stored as they are) ---

class ConversationCreate(SQLModel):
    title: str | None = None  # Optional: the default title is used if missing


class ConversationUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1)  # Only the fields sent are changed


class MessageCreate(SQLModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)  # The Claude API rejects empty messages
