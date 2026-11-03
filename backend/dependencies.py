"""Dependencies shared by the routers. FastAPI calls them before the endpoints that declare them."""

from typing import Annotated

from fastapi import Depends, HTTPException
from sqlmodel import Session

from backend.db import get_session
from backend.models import Conversation

# A database session, opened before the endpoint and closed after the response
SessionDep = Annotated[Session, Depends(get_session)]


def get_conversation_or_404(conversation_id: int, session: SessionDep) -> Conversation:
    """Load the conversation whose id is in the URL, or stop the request with a 404."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


# An existing conversation taken from {conversation_id} in the route
ConversationDep = Annotated[Conversation, Depends(get_conversation_or_404)]
