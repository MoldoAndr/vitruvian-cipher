"""
Pydantic schemas for request and response payloads.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_model: str
    generation_model: str
    vector_db_chunks: int
    timestamp: dt.datetime


class IngestRequest(BaseModel):
    document_path: str = Field(..., min_length=3)
    document_type: str = Field(..., pattern="^(pdf|md|txt)$")

    @validator("document_path")
    def validate_path(cls, value: str) -> str:  # noqa: D417
        # Accept local paths or HTTP(S) URLs
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("/"):
            return value
        # Allow relative paths under documents directory
        return value


class IngestResponse(BaseModel):
    status: str
    message: str
    next_status_check: str = "/status"


class StatusResponse(BaseModel):
    total_reference_documents: int
    processed_documents: int
    in_progress_documents: int
    pending_documents: int
    total_chunks_in_vector_db: int
    currently_processing: Optional[str]
    timestamp: dt.datetime


class GenerateRequest(BaseModel):
    query: str = Field(..., min_length=3)
    conversation_id: Optional[str] = None


class ProviderUpdateRequest(BaseModel):
    provider: str = Field(..., min_length=3)
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_api_key: Optional[str] = None
    ollama_use_chat: Optional[bool] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    openai_base_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    gemini_base_url: Optional[str] = None


class ProviderUpdateResponse(BaseModel):
    status: str
    provider: str
    generation_model: str
    base_url: Optional[str] = None


class SourceChunk(BaseModel):
    chunk_id: str
    relevance_score: float
    preview: str
    metadata: dict


class GenerateResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    conversation_id: str
    message_id: int


class ConversationMessage(BaseModel):
    id: int
    role: str
    content: str
    created_at: dt.datetime


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    created_at: dt.datetime
    messages: List[ConversationMessage]
