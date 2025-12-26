"""
Configuration handling for the Cryptography RAG system.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        default=f"sqlite:///{ROOT_DIR / 'data' / 'rag_system.db'}"
    )
    chroma_persist_directory: str = Field(
        default=str(ROOT_DIR / "data" / "chromadb")
    )
    documents_directory: str = Field(default=str(ROOT_DIR / "documents"))
    models_cache_directory: str = Field(default=str(ROOT_DIR / "models"))

    embedding_model_name: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_batch_size: int = Field(default=32)
    reranker_model_name: str = Field(default="BAAI/bge-reranker-base")
    reranker_batch_size: int = Field(default=16)
    ollama_url: str = Field(default="http://127.0.0.1:11434")
    ollama_model: str = Field(default="phi3")
    ollama_request_timeout: int = Field(default=180)
    ollama_api_key: str = Field(default="")
    ollama_use_chat: bool = Field(default=True)

    chunk_size: int = Field(default=300)
    chunk_overlap: int = Field(default=50)
    retrieval_top_k: int = Field(default=10)
    reranker_top_k: int = Field(default=3)
    reranker_threshold: float = Field(default=0.5)
    max_context_chars: int = Field(default=6000)
    max_chunk_chars: int = Field(default=1500)

    # Answer policy
    answer_style: str = Field(default="abstractive")
    allow_general_knowledge: bool = Field(default=True)
    require_citations: bool = Field(default=True)
    min_cited_sources: int = Field(default=1)
    min_source_score: float = Field(default=0.35)

    generation_temperature: float = Field(default=0.2)
    generation_top_p: float = Field(default=0.9)
    generation_top_k: int = Field(default=40)
    generation_max_tokens: int = Field(default=900)
    continuation_max_tokens: int = Field(default=300)
    continuation_max_attempts: int = Field(default=2)

    extractive_max_sentences: int = Field(default=6)

    ingestion_interval_seconds: int = Field(default=5)
    ingestion_batch_size: int = Field(default=1)
    ingestion_worker_enabled: bool = Field(default=True)
    ingestion_max_failures: int = Field(default=3)
    ingestion_backoff_base_seconds: int = Field(default=30)
    ingestion_backoff_max_seconds: int = Field(default=1800)

    allow_remote_ingest: bool = Field(default=False)
    allowed_remote_hosts: str = Field(default="")
    max_document_bytes: int = Field(default=25_000_000)
    pdf_use_pdfplumber: bool = Field(default=True)

    enable_lexical_retrieval: bool = Field(default=True)
    lexical_top_k: int = Field(default=10)
    lexical_weight: float = Field(default=0.35)
    vector_weight: float = Field(default=0.65)

    query_correction_enabled: bool = Field(default=True)
    query_correction_cutoff: float = Field(default=0.84)
    query_cache_size: int = Field(default=128)
    domain_terms_path: str = Field(default="")

    llm_provider: str = Field(default="ollama")
    openai_api_key: str = Field(default="")
    openai_base_url: str = Field(default="https://api.openai.com")
    openai_model: str = Field(default="gpt-4o-mini")
    gemini_api_key: str = Field(default="")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com")
    gemini_model: str = Field(default="gemini-1.5-flash")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    settings = Settings()
    # Ensure local caches are used for model downloads.
    os.environ.setdefault("FASTEMBED_CACHE_PATH", settings.models_cache_directory)
    os.environ.setdefault("HF_HOME", settings.models_cache_directory)
    os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "false")
    os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "false")
    return settings
