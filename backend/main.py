from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend import models  # noqa: F401  (registers the tables)
from backend.db import create_db
from backend.routers import conversations, messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()  # startup
    yield
    # Shutdown 

app = FastAPI(title="Desktop AI Assistant API", lifespan=lifespan)
app.include_router(conversations.router)
app.include_router(messages.router)

@app.get("/health")
def health():
    return {"status": "ok"}
