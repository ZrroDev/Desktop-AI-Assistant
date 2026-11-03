"""Database connection: the engine, table creation and one session per request."""

from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

# Project root = folder above backend/, no matter where the server is run from
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "generated" / "assistant.db"
# TODO: when packaging the app, save it in the user data folder instead
# (platformdirs.user_data_dir), the install folder may be read-only

# One engine for the whole app; it opens connections only when they are needed.
# To switch to Postgres, change the URL (and drop connect_args, it is SQLite only).
# check_same_thread=False: FastAPI runs requests on several threads, SQLite blocks that by default
engine = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})


def create_db():
    """Create the database file and any missing tables (existing tables are left as they are)."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    """Give each request its own database session and close it afterwards."""
    with Session(engine) as session:
        yield session  # FastAPI resumes here once the response is sent, closing the session


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores foreign keys unless each connection turns them on."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
