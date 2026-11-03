"""FastAPI app: creates the database on startup and registers the routers.

Run from the project root with: uvicorn backend.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend import models  # noqa: F401  (registers the tables before create_db)
from backend.db import create_db
from backend.routers import conversations, messages


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Code before yield runs on startup, code after it on shutdown."""
    create_db()
    yield


app = FastAPI(title="Desktop AI Assistant API", lifespan=lifespan)
app.include_router(conversations.router)
app.include_router(messages.router)


@app.get("/health")
def health():
    """Check that the server is up."""
    return {"status": "ok"}
