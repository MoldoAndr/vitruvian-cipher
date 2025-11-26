"""
Database utilities for the Cryptography RAG system.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings


settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

Base = declarative_base()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope for DB operations.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pylint: disable=broad-except
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.
    """
    with session_scope() as session:
        yield session

