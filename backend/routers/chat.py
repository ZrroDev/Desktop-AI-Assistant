"""Endpoints to ask the AI inside a conversation: the backend loads the history, calls the AI and saves the turn."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Field, Session, SQLModel, select

from backend.llm_service import LLMError, generate_answer, stream_answer
from backend.dependencies import ConversationDep, SessionDep
from backend.models import Message

MAX_HISTORY_TURNS = 10  # 1 turn = question + answer

router = APIRouter(prefix="/conversations/{conversation_id}/chat", tags=["chat"])


class ChatRequest(SQLModel):
    """Body of a chat request: the question, whether the answer will be spoken, and an optional screenshot."""

    question: str = Field(min_length=1)
    voice: bool = False
    image: str | None = None  # Screenshot as base64 PNG, used only for this question (never saved)


@router.post("")
def chat(conversation: ConversationDep, data: ChatRequest, session: SessionDep) -> Message:
    """Ask the AI with the conversation's last turns as context, save both messages and return the answer."""
    history = _load_history(conversation.id, session)

    try:
        answer = generate_answer(history, data.question, data.voice, data.image)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"Assistant API error: {e}")
    if not answer:
        raise HTTPException(status_code=502, detail="Assistant returned an empty answer")

    question_message = Message(conversation_id=conversation.id, role="user", content=data.question)
    answer_message = Message(conversation_id=conversation.id, role="assistant", content=answer)
    session.add_all([question_message, answer_message])
    session.commit()  # Both messages in one transaction: a turn is never saved by halves
    session.refresh(answer_message)
    return answer_message


@router.post("/stream")
def chat_stream(conversation: ConversationDep, data: ChatRequest, session: SessionDep):
    """Like /chat, but sends the answer as plain text while it is generated. The turn is saved at the end."""
    history = _load_history(conversation.id, session)

    conversation_id = conversation.id

    def generate():
        chunks = []
        for text in stream_answer(history, data.question, data.voice, data.image):
            chunks.append(text)
            yield text  # Sent to the client right away
        answer = "".join(chunks)
        if answer:
            session.add_all([
                Message(conversation_id=conversation_id, role="user", content=data.question),
                Message(conversation_id=conversation_id, role="assistant", content=answer),
            ])
            session.commit()

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


def _load_history(conversation_id, session: Session):
    """Return the conversation's last turns as role/content dicts, oldest first and starting with a user message."""
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(MAX_HISTORY_TURNS * 2)
    )

    history = [{"role": m.role, "content": m.content} for m in reversed(session.exec(query).all())]
    while history and history[0]["role"] != "user": # Assistant needs the history to start with "user"
        history.pop(0)
    return history
