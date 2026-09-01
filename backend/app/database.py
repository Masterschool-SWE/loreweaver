"""Database engine, session dependency, and table creation."""
from pathlib import Path
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import DATABASE_URL

# Make sure the folder for the SQLite file exists (no-op for non-sqlite URLs).
if DATABASE_URL.startswith("sqlite"):
    Path("data").mkdir(parents=True, exist_ok=True)

# check_same_thread=False lets the SQLite connection be shared across FastAPI threads.
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


def create_db_and_tables() -> None:
    """Create all tables declared on SQLModel subclasses (idempotent)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session
