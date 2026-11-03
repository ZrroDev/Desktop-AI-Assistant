from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend import models  # noqa: F401  (registers the tables)
from backend.db import create_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()  # startup
    yield
    # Shutdown 

app = FastAPI(title="Desktop AI Assistant API")

@app.get("/health")
def health():
    return {"status": "ok"}
