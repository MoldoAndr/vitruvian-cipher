"""
SQLAlchemy models for the Cryptography RAG system.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def default_uuid() -> str:
    return str(uuid.uuid4())


class ReferenceDocument(Base):
    __tablename__ = "reference_documents"
    __table_args__ = (
        UniqueConstraint("document_path", name="uq_reference_documents_document_path"),
        CheckConstraint(
            "processing_status in (0, 1, 2)",
            name="ck_reference_documents_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_path: Mapped[str] = mapped_column(String(512), nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    processing_status: Mapped[int] = mapped_column(Integer, default=0, index=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    processed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(String(1024))
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="reference_document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ReferenceDocument id={self.id} name={self.document_name} status={self.processing_status}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference_doc_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reference_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_vector: Mapped[Optional[str]] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    source_title: Mapped[Optional[str]] = mapped_column(String(255))
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    reference_document: Mapped[ReferenceDocument] = relationship(
        back_populates="chunks"
    )

    __table_args__ = (
        UniqueConstraint(
            "reference_doc_id",
            "chunk_index",
            name="uq_document_chunks_doc_chunk_index",
        ),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk doc={self.reference_doc_id} idx={self.chunk_index}>"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=default_uuid
    )
    title: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def touch(self) -> None:
        self.updated_at = dt.datetime.utcnow()

    def __repr__(self) -> str:
        return f"<Conversation id={self.conversation_id}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("conversations.conversation_id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_chunk_ids: Mapped[Optional[list[str]]] = mapped_column(SQLiteJSON)
    relevance_scores: Mapped[Optional[list[float]]] = mapped_column(SQLiteJSON)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False, index=True
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("role in ('user', 'assistant')", name="ck_messages_role"),
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role}>"


@event.listens_for(Message, "before_insert")
def _update_conversation_timestamp(mapper, connection, target):  # type: ignore[no-untyped-def]
    """
    Ensure the parent conversation timestamp stays current.
    """
    connection.execute(
        Conversation.__table__.update()
        .where(Conversation.conversation_id == target.conversation_id)
        .values(updated_at=dt.datetime.utcnow())
    )

