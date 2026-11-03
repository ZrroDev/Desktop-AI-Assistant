from pathlib import Path
from sqlmodel import Session
from sqlmodel import SQLModel, create_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "generated" / "assistant.db"

engine = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})

def create_db():
    """Create the database file and any missing tables."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    """Give each request its own database session and close it afterwards."""
    with Session(engine) as session:
        yield session
