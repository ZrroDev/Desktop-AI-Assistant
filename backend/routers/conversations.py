"""Endpoints to create, list and get conversations."""

from fastapi import APIRouter
from sqlmodel import select

from backend.dependencies import ConversationDep, SessionDep
from backend.models import Conversation, ConversationCreate

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", status_code=201)
def create_conversation(data: ConversationCreate, session: SessionDep) -> Conversation:
    """Create a conversation, with the default title if none is given."""
    conversation = Conversation()
    if data.title:
        conversation.title = data.title
    session.add(conversation)
    session.commit()
    session.refresh(conversation)  # Reload it to get the id the database assigned
    return conversation


@router.get("")
def list_conversations(session: SessionDep) -> list[Conversation]:
    """List all conversations, newest first."""
    return session.exec(select(Conversation).order_by(Conversation.created_at.desc())).all()


@router.get("/{conversation_id}")
def get_conversation(conversation: ConversationDep) -> Conversation:
    """Get one conversation (ConversationDep already returns 404 if it doesn't exist)."""
    return conversation
