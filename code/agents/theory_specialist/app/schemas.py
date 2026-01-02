"""
Pydantic schemas for request and response payloads.
"""

from __future__ import annotations

import datetime as dt
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_model: str
    generation_model: str
    vector_db_chunks: int
    timestamp: dt.datetime


class IngestRequest(BaseModel):
    document_path: str = Field(..., min_length=3, max_length=2048)
    document_type: str = Field(..., pattern="^(pdf|md|txt)$")

    @field_validator("document_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
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
    query: str = Field(..., min_length=3, max_length=5000)
    conversation_id: Optional[str] = None
    provider: Optional[str] = Field(None, max_length=50)
    ollama_url: Optional[str] = Field(None, max_length=128)
    ollama_model: Optional[str] = Field(None, max_length=128)
    openai_model: Optional[str] = Field(None, max_length=128)
    gemini_model: Optional[str] = Field(None, max_length=128)

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v:
            return v
        v = v.strip().lower().replace(" ", "-")
        valid_providers = {"ollama", "ollama-cloud", "gemini", "openai"}
        if v not in valid_providers:
            raise ValueError(
                f"Invalid provider. Use one of: {', '.join(sorted(valid_providers))}"
            )
        return v


class ProviderUpdateRequest(BaseModel):
    provider: str = Field(..., min_length=3, max_length=50)
    ollama_url: Optional[str] = Field(None, max_length=512)
    ollama_model: Optional[str] = Field(None, max_length=128)
    ollama_api_key: Optional[str] = Field(None, max_length=512)
    ollama_use_chat: Optional[bool] = None
    openai_api_key: Optional[str] = Field(None, max_length=512)
    openai_model: Optional[str] = Field(None, max_length=128)
    openai_base_url: Optional[str] = Field(None, max_length=512)
    gemini_api_key: Optional[str] = Field(None, max_length=512)
    gemini_model: Optional[str] = Field(None, max_length=128)
    gemini_base_url: Optional[str] = Field(None, max_length=512)

    @field_validator("ollama_url", "openai_base_url", "gemini_base_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


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


class AutoIngestResponse(BaseModel):
    status: str
    discovered_count: int
    queued_count: int
    message: str
    next_status_check: str = "/status"


class ConfigUpdateRequest(BaseModel):
    ingestion_workers: Optional[int] = Field(None, ge=1, le=10)
    parallel_requests: Optional[int] = Field(None, ge=1, le=10)


class ConfigUpdateResponse(BaseModel):
    status: str
    ingestion_workers: int
    parallel_requests: int
    message: str
