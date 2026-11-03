"""Endpoints to create, list and get conversations."""

from fastapi import APIRouter
from sqlmodel import delete, select 

from backend.dependencies import ConversationDep, SessionDep
from backend.models import Conversation, ConversationCreate, ConversationUpdate, Message

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


@router.patch("/{conversation_id}")
def update_conversation(conversation: ConversationDep, data: ConversationUpdate, session: SessionDep) -> Conversation:
    """Change the fields sent in the body (for now, only the title)."""
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    conversation.sqlmodel_update(changes)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation: ConversationDep, session: SessionDep):
    """Delete the conversation and all its messages."""
    session.delete(conversation)
    session.commit()