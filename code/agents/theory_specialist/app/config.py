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
    ollama_url: str = Field(default="http://127.0.0.1:11434")
    ollama_model: str = Field(default="phi3")
    ollama_request_timeout: int = Field(default=60)

    chunk_size: int = Field(default=300)
    chunk_overlap: int = Field(default=50)
    retrieval_top_k: int = Field(default=10)
    reranker_top_k: int = Field(default=3)
    reranker_threshold: float = Field(default=0.5)

    ingestion_interval_seconds: int = Field(default=5)
    ingestion_batch_size: int = Field(default=1)

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
    return settings
