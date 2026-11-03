from typing import Annotated
from fastapi import Depends, HTTPException
from sqlmodel import Session
from backend.db import get_session
from backend.models import Conversation

SessionDep = Annotated[Session, Depends(get_session)]

def get_conversation_or_404(conversation_id: int, session: SessionDep) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

ConversationDep = Annotated[Conversation, Depends(get_conversation_or_404)]