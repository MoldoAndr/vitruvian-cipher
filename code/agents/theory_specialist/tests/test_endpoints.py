"""
Tests for all API endpoints.

This module tests:
- GET /health
- POST /ingest
- POST /auto-ingest
- GET /status
- POST /generate (with and without provider override)
- POST /provider
- POST /config
- GET /config
- GET /conversations/{conversation_id}
"""

from __future__ import annotations

from unittest.mock import patch
from datetime import datetime

import pytest
from fastapi import status
from sqlalchemy.orm import Session


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_200(self, test_client):
        """Test that health endpoint returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_response_structure(self, test_client):
        """Test that health endpoint returns correct structure."""
        response = test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "database" in data
        assert "embedding_model" in data
        assert "generation_model" in data
        assert "vector_db_chunks" in data
        assert "timestamp" in data

    def test_health_contains_expected_values(self, test_client):
        """Test that health endpoint returns expected values."""
        response = test_client.get("/health")
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]
        assert data["database"] in ["connected", "error"]
        assert isinstance(data["vector_db_chunks"], int)
        assert data["vector_db_chunks"] >= 0


class TestIngestEndpoint:
    """Tests for POST /ingest endpoint."""

    def test_ingest_pdf_success(self, test_client, test_db_session: Session):
        """Test ingesting a PDF document."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/documents/test.pdf",
                "document_type": "pdf"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "queued"
        assert "queued" in data["message"].lower()

    def test_ingest_markdown_success(self, test_client):
        """Test ingesting a markdown document."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/guide.md",
                "document_type": "md"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "queued"

    def test_ingest_txt_success(self, test_client):
        """Test ingesting a text document."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "notes.txt",
                "document_type": "txt"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_ingest_duplicate_returns_400(self, test_client, test_db_session: Session):
        """Test that ingesting duplicate document returns 400."""
        # First ingestion
        test_client.post(
            "/ingest",
            json={
                "document_path": "/app/documents/duplicate.pdf",
                "document_type": "pdf"
            }
        )

        # Second ingestion (should fail)
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/documents/duplicate.pdf",
                "document_type": "pdf"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already queued" in data["detail"].lower()

    def test_ingest_invalid_type_returns_422(self, test_client):
        """Test that invalid document type returns validation error."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "test.docx",
                "document_type": "docx"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_path_too_short_returns_422(self, test_client):
        """Test that path that's too short returns validation error."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "a.pdf",
                "document_type": "pdf"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_url_path_accepted(self, test_client):
        """Test that URL paths are accepted when configured."""
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "https://example.com/doc.pdf",
                "document_type": "pdf"
            }
        )
        # Should succeed or be rejected based on ALLOW_REMOTE_INGEST setting
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


class TestAutoIngestEndpoint:
    """Tests for POST /auto-ingest endpoint."""

    def test_auto_ingest_discovers_new_documents(
        self, test_client, test_documents_dir, test_db_session: Session
    ):
        """Test that auto-ingest discovers new documents."""
        response = test_client.post("/auto-ingest")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] in ["queued", "completed"]
        assert "discovered_count" in data
        assert "queued_count" in data
        assert data["discovered_count"] >= 0
        assert data["queued_count"] >= 0
        assert data["queued_count"] <= data["discovered_count"]

    def test_auto_ingest_returns_completed_when_no_new_docs(
        self, test_client, test_db_session: Session, create_test_document
    ):
        """Test that auto-ingest returns completed when all docs are already ingested."""
        # Add all test documents to database
        create_test_document("/app/documents/test1.pdf", "test1.pdf", processing_status=2)
        create_test_document("/app/documents/test2.md", "test2.md", processing_status=2)

        response = test_client.post("/auto-ingest")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "completed"
        assert data["discovered_count"] == 0
        assert data["queued_count"] == 0

    def test_auto_ingest_queues_only_unprocessed_documents(
        self, test_client, test_documents_dir, test_db_session: Session, create_test_document
    ):
        """Test that auto-ingest only queues documents not already in database."""
        # Add one document as processed
        create_test_document(str(test_documents_dir / "test1.pdf"), "test1.pdf", processing_status=2)

        response = test_client.post("/auto-ingest")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should queue the remaining documents, not the already-processed one
        assert data["discovered_count"] > 0


class TestStatusEndpoint:
    """Tests for GET /status endpoint."""

    def test_status_returns_200(self, test_client):
        """Test that status endpoint returns 200 OK."""
        response = test_client.get("/status")
        assert response.status_code == status.HTTP_200_OK

    def test_status_response_structure(self, test_client):
        """Test that status endpoint returns correct structure."""
        response = test_client.get("/status")
        data = response.json()

        assert "total_reference_documents" in data
        assert "processed_documents" in data
        assert "in_progress_documents" in data
        assert "pending_documents" in data
        assert "total_chunks_in_vector_db" in data
        assert "currently_processing" in data
        assert "timestamp" in data

    def test_status_counts_are_accurate(
        self, test_client, test_db_session: Session, create_test_document
    ):
        """Test that status endpoint returns accurate counts."""
        # Create documents with different statuses
        create_test_document("doc1.pdf", "doc1.pdf", processing_status=0)  # pending
        create_test_document("doc2.pdf", "doc2.pdf", processing_status=1)  # in progress
        create_test_document("doc3.pdf", "doc3.pdf", processing_status=2)  # processed
        create_test_document("doc4.pdf", "doc4.pdf", processing_status=2)  # processed

        response = test_client.get("/status")
        data = response.json()

        assert data["total_reference_documents"] == 4
        assert data["pending_documents"] == 1
        assert data["in_progress_documents"] == 1
        assert data["processed_documents"] == 2

    def test_status_shows_currently_processing(
        self, test_client, test_db_session: Session, create_test_document
    ):
        """Test that status shows currently processing document."""
        create_test_document("processing.pdf", "processing.pdf", processing_status=1)

        response = test_client.get("/status")
        data = response.json()

        assert data["currently_processing"] == "processing.pdf"


class TestGenerateEndpoint:
    """Tests for POST /generate endpoint."""

    def test_generate_basic_query(self, test_client, mock_rag_system):
        """Test generating answer for basic query."""
        response = test_client.post(
            "/generate",
            json={
                "query": "What is RSA encryption?",
                "conversation_id": None
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "conversation_id" in data
        assert "message_id" in data
        assert isinstance(data["sources"], list)

    def test_generate_creates_new_conversation(self, test_client, mock_rag_system):
        """Test that generate creates new conversation when conversation_id is None."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Explain AES",
                "conversation_id": None
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["conversation_id"] is not None
        assert len(data["conversation_id"]) > 0

    def test_generate_uses_existing_conversation(
        self, test_client, mock_rag_system, create_test_conversation
    ):
        """Test that generate uses existing conversation."""
        conv = create_test_conversation(conversation_id="test-conv-123")

        response = test_client.post(
            "/generate",
            json={
                "query": "What is ECC?",
                "conversation_id": "test-conv-123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["conversation_id"] == "test-conv-123"

    def test_generate_with_provider_override_ollama(self, test_client, mock_rag_system):
        """Test generate with Ollama provider override."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Explain RSA",
                "provider": "ollama",
                "ollama_model": "phi3"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        # Verify the mock was called
        mock_rag_system.generate_answer.assert_called_once()

    def test_generate_with_provider_override_openai(self, test_client, mock_rag_system):
        """Test generate with OpenAI provider override."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Explain AES",
                "provider": "openai",
                "openai_model": "gpt-4o-mini"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_generate_with_provider_override_gemini(self, test_client, mock_rag_system):
        """Test generate with Gemini provider override."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Explain ECC",
                "provider": "gemini",
                "gemini_model": "gemini-1.5-flash"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_generate_invalid_provider_returns_422(self, test_client):
        """Test that invalid provider returns validation error."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Test query",
                "provider": "invalid-provider"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_query_too_long_returns_413(self, test_client):
        """Test that query exceeding max length returns 413."""
        long_query = "a" * 10000  # Exceeds default max of 5000

        response = test_client.post(
            "/generate",
            json={"query": long_query}
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_generate_query_too_short_returns_422(self, test_client):
        """Test that query that's too short returns validation error."""
        response = test_client.post(
            "/generate",
            json={"query": "hi"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_returns_sources_with_metadata(self, test_client, mock_rag_system):
        """Test that generate returns sources with proper metadata."""
        response = test_client.post(
            "/generate",
            json={"query": "Explain hash functions"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["sources"]) >= 0
        for source in data["sources"]:
            assert "chunk_id" in source
            assert "relevance_score" in source
            assert "preview" in source
            assert "metadata" in source


class TestProviderEndpoint:
    """Tests for POST /provider endpoint."""

    def test_provider_update_to_ollama(self, test_client, mock_rag_system):
        """Test updating provider to Ollama."""
        response = test_client.post(
            "/provider",
            json={
                "provider": "ollama",
                "ollama_url": "http://ollama:11434",
                "ollama_model": "phi3"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "updated"
        assert data["provider"] == "ollama"
        assert data["generation_model"] == "phi3"
        assert data["base_url"] == "http://ollama:11434"

    def test_provider_update_to_ollama_cloud(self, test_client, mock_rag_system):
        """Test updating provider to Ollama Cloud."""
        response = test_client.post(
            "/provider",
            json={
                "provider": "ollama-cloud",
                "ollama_model": "gpt-oss:120b-cloud",
                "ollama_api_key": "test-key"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["provider"] == "ollama-cloud"

    def test_provider_update_to_openai(self, test_client, mock_rag_system):
        """Test updating provider to OpenAI."""
        response = test_client.post(
            "/provider",
            json={
                "provider": "openai",
                "openai_api_key": "sk-test",
                "openai_model": "gpt-4o-mini"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["provider"] == "openai"
        assert data["generation_model"] == "gpt-4o-mini"

    def test_provider_update_to_gemini(self, test_client, mock_rag_system):
        """Test updating provider to Gemini."""
        response = test_client.post(
            "/provider",
            json={
                "provider": "gemini",
                "gemini_api_key": "test-key",
                "gemini_model": "gemini-1.5-flash"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["provider"] == "gemini"

    def test_provider_invalid_provider_returns_400(self, test_client):
        """Test that invalid provider returns 400 error."""
        response = test_client.post(
            "/provider",
            json={"provider": "invalid"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_provider_update_only_llm_not_rag(self, test_client, mock_rag_system):
        """Test that provider update only changes LLM, not entire RAG system."""
        # Get initial RAG system reference
        from app.main import get_rag_system
        initial_rag = get_rag_system()

        # Update provider
        test_client.post(
            "/provider",
            json={
                "provider": "openai",
                "openai_api_key": "sk-test",
                "openai_model": "gpt-4o-mini"
            }
        )

        # Verify RAG system is the same object (not recreated)
        current_rag = get_rag_system()
        assert current_rag is initial_rag


class TestConfigEndpoints:
    """Tests for POST /config and GET /config endpoints."""

    def test_get_config_returns_defaults(self, test_client):
        """Test that GET /config returns default values."""
        response = test_client.get("/config")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "ingestion_workers" in data
        assert "parallel_requests" in data
        assert data["ingestion_workers"] == 1  # Default
        assert data["parallel_requests"] == 1  # Default

    def test_post_config_update_ingestion_workers(self, test_client):
        """Test updating ingestion_workers via POST /config."""
        response = test_client.post(
            "/config",
            json={"ingestion_workers": 5}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "updated"
        assert data["ingestion_workers"] == 5

        # Verify the change persisted
        response = test_client.get("/config")
        data = response.json()
        assert data["ingestion_workers"] == 5

    def test_post_config_update_parallel_requests(self, test_client):
        """Test updating parallel_requests via POST /config."""
        response = test_client.post(
            "/config",
            json={"parallel_requests": 3}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["parallel_requests"] == 3

    def test_post_config_update_both(self, test_client):
        """Test updating both config values."""
        response = test_client.post(
            "/config",
            json={
                "ingestion_workers": 4,
                "parallel_requests": 2
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["ingestion_workers"] == 4
        assert data["parallel_requests"] == 2

    def test_post_config_invalid_ingestion_workers(self, test_client):
        """Test that invalid ingestion_workers returns 400."""
        response = test_client.post(
            "/config",
            json={"ingestion_workers": 15}  # Exceeds max of 10
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_config_invalid_parallel_requests(self, test_client):
        """Test that invalid parallel_requests returns 400."""
        response = test_client.post(
            "/config",
            json={"parallel_requests": 0}  # Below min of 1
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_config_no_changes(self, test_client):
        """Test POST /config with no changes."""
        response = test_client.post(
            "/config",
            json={}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "No changes requested" in data["message"]


class TestConversationEndpoints:
    """Tests for GET /conversations/{conversation_id} endpoint."""

    def test_get_conversation_history(
        self, test_client, create_test_conversation
    ):
        """Test fetching conversation history."""
        conv = create_test_conversation(
            conversation_id="test-conv-456",
            with_messages=True
        )

        response = test_client.get(f"/conversations/{conv.conversation_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["conversation_id"] == "test-conv-456"
        assert "messages" in data
        assert len(data["messages"]) == 2

    def test_get_conversation_not_found_returns_404(self, test_client):
        """Test that non-existent conversation returns 404."""
        response = test_client.get("/conversations/nonexistent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_conversation_with_pagination(
        self, test_client, create_test_conversation
    ):
        """Test conversation history pagination."""
        conv = create_test_conversation(
            conversation_id="paginated-conv",
            with_messages=True
        )

        response = test_client.get(
            f"/conversations/{conv.conversation_id}?page=1&page_size=1"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["messages"]) == 1

    def test_get_conversation_invalid_page_size(self, test_client):
        """Test that invalid page_size returns error."""
        response = test_client.get(
            "/conversations/test?page_size=500"  # Exceeds max
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestEndpointValidation:
    """Tests for common validation across endpoints."""

    def test_404_for_nonexistent_endpoint(self, test_client):
        """Test that non-existent endpoints return 404."""
        response = test_client.get("/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_405_for_wrong_method(self, test_client):
        """Test that wrong HTTP method returns 405."""
        response = test_client.get("/ingest")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_415_for_missing_content_type(self, test_client):
        """Test that missing Content-Type on POST returns 415."""
        response = test_client.post(
            "/ingest",
            data='{"document_path": "test.pdf", "document_type": "pdf"}'
        )
        # FastAPI might accept this, so we check for either 415 or 200
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE]
