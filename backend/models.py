from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from typing import Literal

def utc_now():
    return datetime.now(timezone.utc)

class ConversationCreate(SQLModel):
    title: str | None = None

class MessageCreate(SQLModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = "New conversation"
    created_at: datetime = Field(default_factory=utc_now)

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=utc_now)
