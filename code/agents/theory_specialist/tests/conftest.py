"""
Pytest configuration and fixtures for testing the RAG system.

This module provides fixtures for:
- Test database (in-memory SQLite)
- Test client (FastAPI TestClient)
- Sample documents
- Mock RAG system components
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ============================================
# Setup test environment BEFORE importing app
# ============================================

# Set environment variables for testing BEFORE app imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CHROMA_PERSIST_DIRECTORY"] = "/tmp/test_chroma"
os.environ["DOCUMENTS_DIRECTORY"] = "/tmp/test_documents"
os.environ["MODELS_CACHE_DIRECTORY"] = "/tmp/test_models"
os.environ["EMBEDDING_MODEL_NAME"] = "BAAI/bge-small-en-v1.5"
os.environ["RERANKER_MODEL_NAME"] = "BAAI/bge-reranker-base"
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_URL"] = "http://127.0.0.1:11434"
os.environ["OLLAMA_MODEL"] = "phi3"
os.environ["INGESTION_INTERVAL_SECONDS"] = "1"
os.environ["INGESTION_BATCH_SIZE"] = "1"
os.environ["ALLOW_REMOTE_INGEST"] = "False"
os.environ["MAX_QUERY_LENGTH"] = "5000"

# NOW import app modules after environment is set
from app.config import Settings, get_settings
from app.database import Base, get_db, engine, SessionLocal
from app.document_discovery import DocumentDiscoveryService
from app.main import app


# ============================================
# Database Fixtures
# ============================================

@pytest.fixture(scope="function", autouse=True)
def setup_test_database(tmp_path):
    """
    Setup test database before each test function.
    This fixture patches the database module to use a temporary file-based SQLite.
    """
    # Import before patching
    import app.database
    import app.main

    # Store originals
    original_engine = app.database.engine
    original_session_local = app.database.SessionLocal

    # Create temporary file-based test database (needed for multi-connection sharing)
    test_db_path = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create test session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        class_=Session,
    )

    # Patch BEFORE any database operations
    app.database.engine = test_engine
    app.database.SessionLocal = TestingSessionLocal

    # Patch global settings to use test database URL
    original_settings = app.main._global_settings
    test_settings = app.main._global_settings.create_updated_copy(
        database_url=f"sqlite:///{test_db_path}"
    )
    app.main._global_settings = test_settings

    yield test_engine, TestingSessionLocal

    # Restore originals
    app.database.engine = original_engine
    app.database.SessionLocal = original_session_local
    app.main._global_settings = original_settings

    # Cleanup
    test_engine.dispose()
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def test_db_url() -> str:
    """Get in-memory SQLite database URL for testing."""
    return "sqlite:///:memory:"


@pytest.fixture
def test_engine(test_db_url: str):
    """Create a test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db_session() -> Generator[Session, None, None]:
    """
    Create a test database session.
    Note: Uses the patched SessionLocal from setup_test_database.
    """
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ============================================
# Settings & Temp Directory Fixtures
# ============================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings with temporary directories."""
    return Settings(
        database_url="sqlite:///:memory:",
        chroma_persist_directory=str(temp_dir / "chroma"),
        documents_directory=str(temp_dir / "documents"),
        models_cache_directory=str(temp_dir / "models"),
        embedding_model_name="BAAI/bge-small-en-v1.5",
        reranker_model_name="BAAI/bge-reranker-base",
        ollama_url="http://127.0.0.1:11434",
        ollama_model="phi3",
        llm_provider="ollama",
        ingestion_interval_seconds=1,
        ingestion_batch_size=1,
        allow_remote_ingest=False,
        max_query_length=5000,
    )


@pytest.fixture
def test_documents_dir(temp_dir: Path) -> Path:
    """Create and populate test documents directory."""
    docs_dir = temp_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Create sample test files
    test_files = {
        "test1.pdf": "Sample PDF content for testing cryptographic algorithms like RSA and AES.",
        "test2.md": "# Cryptography Basics\n\nThis is a test markdown file about cryptography.",
        "test3.txt": "This is a plain text file about symmetric and asymmetric encryption.",
    }

    for filename, content in test_files.items():
        (docs_dir / filename).write_text(content)

    # Create subdirectory with file
    subdir = docs_dir / "subfolder"
    subdir.mkdir(exist_ok=True)
    (subdir / "test4.pdf").write_text("Nested document about hash functions.")

    return docs_dir


# ============================================
# Database Dependency Override
# ============================================

@pytest.fixture
def test_client(test_db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.

    This fixture ensures all API endpoints use the test database
    instead of the production database.
    """
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ============================================
# Mock RAG System Fixtures
# ============================================

@pytest.fixture
def mock_rag_system(monkeypatch):
    """
    Mock the RAG system to avoid loading heavy models during tests.

    This patch replaces the actual RAGSystem initialization with a mock
    that has minimal behavior for testing.
    """
    from unittest.mock import MagicMock, Mock

    mock_rag = MagicMock()

    # Mock collection
    mock_collection = MagicMock()
    mock_collection.count.return_value = 100
    mock_collection.query.return_value = {
        "ids": [["1_1", "1_2", "1_3"]],
        "distances": [[0.3, 0.4, 0.5]],
        "metadatas": [[
            {"source": "test.pdf", "source_page": 1, "text": "Sample text"},
            {"source": "test.pdf", "source_page": 2, "text": "More text"},
            {"source": "test.pdf", "source_page": 3, "text": "Even more text"},
        ]],
        "documents": [["Sample text", "More text", "Even more text"]],
    }
    mock_rag.collection = mock_collection

    # Mock embedding model
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [[0.1, 0.2, 0.3]]
    mock_rag.embedding_model = mock_embedding

    # Mock reranker
    mock_reranker = MagicMock()
    mock_reranker.score.return_value = [0.9, 0.7, 0.5]
    mock_rag.reranker = mock_reranker

    # Mock LLM client
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "This is a test answer about cryptography."
    mock_rag.llm = mock_llm

    # Mock settings
    from app.config import get_settings
    mock_rag.settings = get_settings()

    # Mock methods
    mock_rag.validate_document_path = Mock(return_value=None)
    mock_rag.process_reference_document = Mock(return_value=5)
    mock_rag.prepare_query = Mock()
    mock_rag.prepare_query.return_value = Mock(
        original_query="test query",
        normalized_query="test query",
        query_for_retrieval="test query",
        corrections=[]
    )

    from app.rag_system import RetrievedChunk
    retrieve_payload = (
        [
            RetrievedChunk(
                chunk_id="1_1",
                text="Sample text",
                metadata={"source": "test.pdf", "source_page": 1},
                similarity=0.7
            ),
            RetrievedChunk(
                chunk_id="1_2",
                text="More text",
                metadata={"source": "test.pdf", "source_page": 2},
                similarity=0.6
            ),
        ],
        "vector"
    )
    mock_rag.retrieve = Mock(return_value=retrieve_payload)
    mock_rag.retrieve_with_fallback = Mock(return_value=retrieve_payload)

    mock_rag.rerank = Mock(return_value=[
        RetrievedChunk(
            chunk_id="1_1",
            text="Sample text",
            metadata={"source": "test.pdf", "source_page": 1, "reranker_score": 0.9},
            similarity=0.7
        ),
    ])

    mock_rag.generate_answer = Mock(return_value="Test answer about RSA algorithm.")

    # Patch the get_rag_system function
    import app.main
    monkeypatch.setattr(app.main, "get_rag_system", lambda: mock_rag)
    monkeypatch.setattr(app.main, "_global_rag_system", mock_rag)

    return mock_rag


@pytest.fixture
def mock_aggregator(monkeypatch):
    """Mock the document aggregator to avoid background task scheduling."""
    from unittest.mock import MagicMock

    mock_agg = MagicMock()
    mock_agg.start = Mock()
    mock_agg.shutdown = Mock()

    import app.main
    monkeypatch.setattr(app.main, "get_aggregator", lambda: mock_agg)
    monkeypatch.setattr(app.main, "_global_aggregator", mock_agg)

    return mock_agg


# ============================================
# Document Discovery Service Fixtures
# ============================================

@pytest.fixture
def discovery_service(test_settings: Settings) -> DocumentDiscoveryService:
    """Create a DocumentDiscoveryService instance with test settings."""
    return DocumentDiscoveryService(settings=test_settings)


# ============================================
# Helper Functions
# ============================================

@pytest.fixture
def create_test_document(test_db_session: Session, test_documents_dir: Path):
    """
    Helper function to create a test document in the database.

    Returns a function that creates documents with given parameters.
    """
    from app.models import ReferenceDocument
    import datetime as dt

    def _create(
        document_path: str,
        document_name: str,
        document_type: str = "pdf",
        processing_status: int = 0,
    ):
        doc = ReferenceDocument(
            document_path=document_path,
            document_name=document_name,
            document_type=document_type,
            processing_status=processing_status,
            created_at=dt.datetime.utcnow(),
        )
        test_db_session.add(doc)
        test_db_session.commit()
        test_db_session.refresh(doc)
        return doc

    return _create


@pytest.fixture
def create_test_conversation(test_db_session: Session):
    """
    Helper function to create a test conversation.

    Returns a function that creates conversations.
    """
    from app.models import Conversation, Message
    import datetime as dt

    def _create(
        conversation_id: str | None = None,
        with_messages: bool = False,
    ):
        conv = Conversation(conversation_id=conversation_id)
        test_db_session.add(conv)
        test_db_session.commit()
        test_db_session.refresh(conv)

        if with_messages:
            user_msg = Message(
                conversation_id=conv.conversation_id,
                role="user",
                content="Test question about RSA?",
            )
            asst_msg = Message(
                conversation_id=conv.conversation_id,
                role="assistant",
                content="RSA is an asymmetric encryption algorithm...",
            )
            test_db_session.add(user_msg)
            test_db_session.add(asst_msg)
            test_db_session.commit()

        return conv

    return _create
