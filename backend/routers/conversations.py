from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.db import get_session
from backend.models import Conversation, ConversationCreate

router = APIRouter(prefix="/conversations", tags=["conversations"])
SessionDep = Annotated[Session, Depends(get_session)]

@router.post("", status_code=201)
def create_conversation(data: ConversationCreate, session: SessionDep) -> Conversation:
    conversation = Conversation()
    if data.title:
        conversation.title = data.title
    session.add(conversation)
    session.commit()
    session.refresh(conversation)  # reload it to get the id the database assigned
    return conversation

@router.get("")
def list_conversations(session: SessionDep) -> list[Conversation]:
    return session.exec(select(Conversation).order_by(Conversation.created_at.desc())).all()

@router.get("/{conversation_id}")
def get_conversation(conversation_id: int, session: SessionDep) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
