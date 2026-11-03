from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

def utc_now():
    return datetime.now(timezone.utc)

class ConversationCreate(SQLModel):
    title: str | None = None

class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = "New conversation"
    created_at: datetime = Field(default_factory=utc_now)

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key=Conversation.id, index=True)
    role: str  # "User" or "Assistant"
    content: str
    created_at: datetime = Field(default_factory=utc_now)
