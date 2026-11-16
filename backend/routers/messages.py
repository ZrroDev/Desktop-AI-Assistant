"""Endpoints for the messages of one conversation.

Every route starts with /conversations/{conversation_id}/messages, and ConversationDep
returns 404 before the endpoint runs if that conversation doesn't exist.
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from backend.dependencies import ConversationDep, SessionDep
from backend.models import Message

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])


@router.get("")
def list_messages(conversation: ConversationDep, session: SessionDep, limit: int | None = None) -> list[Message]:
    """List the conversation's messages, oldest first. With ?limit=N only the last N are returned."""
    # Sorted by id, not created_at: ids never tie and follow the insertion order.
    # Newest first so limit keeps the last N, then reversed back to chronological order.
    query = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
    )
    if limit is not None:
        query = query.limit(limit)
    messages = session.exec(query).all()
    return list(reversed(messages))


@router.get("/{message_id}")
def get_message(message_id: int, conversation: ConversationDep, session: SessionDep) -> Message:
    """Get one message, only if it belongs to this conversation."""
    message = session.get(Message, message_id)
    if not message or message.conversation_id != conversation.id:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
