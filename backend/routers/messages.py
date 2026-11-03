from fastapi import APIRouter, HTTPException
from sqlmodel import select

from backend.dependencies import ConversationDep, SessionDep
from backend.models import Message, MessageCreate

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])

@router.post("", status_code=201)
def add_message(conversation: ConversationDep, data: MessageCreate, session: SessionDep) -> Message:
    message = Message(conversation_id=conversation.id, role=data.role, content=data.content)
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

@router.get("")
def list_messages(conversation: ConversationDep, session: SessionDep, limit: int | None = None) -> list[Message]:
    query = (
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.id.desc())
    )
    if limit is not None:
        query = query.limit(limit)
    messages = session.exec(query).all()
    return list(reversed(messages))  # oldest first

@router.get("/{message_id}")
def get_message(message_id: int, conversation: ConversationDep, session: SessionDep) -> Message:
    message = session.get(Message, message_id)
    if not message or message.conversation_id != conversation.id:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
