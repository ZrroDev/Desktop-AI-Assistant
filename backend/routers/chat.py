"""Endpoint to ask Claude inside a conversation: the backend loads the history and saves the turn."""

import anthropic
from fastapi import APIRouter, HTTPException
from sqlmodel import Field, SQLModel, select

from backend.llm_service import generate_answer
from backend.dependencies import ConversationDep, SessionDep
from backend.models import Message

MAX_HISTORY_TURNS = 10 # 1 turn = question + answer

router = APIRouter(prefix="/conversations/{conversation_id}/chat", tags=["chat"])


class ChatRequest(SQLModel):
    question: str = Field(min_length=1)
    voice: bool = False


@router.post("")
def chat(conversation: ConversationDep, data: ChatRequest, session: SessionDep) -> Message:
    """Ask Claude with the conversation's last turns as context, save both messages and return the answer."""
    query = (
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(MAX_HISTORY_TURNS * 2)
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(session.exec(query).all())]
    while history and history[0]["role"] != "user": # Assistant needs the history to start with "user"
        history.pop()

    try:
        answer = generate_answer(history, data.question, data.voice)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Assistant API error: {e}")
    if not answer:
        raise HTTPException(status_code=502, detail="Assistant returned an empty answer")

    question_message = Message(conversation_id=conversation.id, role="user", content=data.question)
    answer_message = Message(conversation_id=conversation.id, role="assistant", content=answer)
    session.add_all([question_message, answer_message])
    session.commit() # Both messages in one transaction: a turn is never saved by halves
    session.refresh(answer_message)
    return answer_message
