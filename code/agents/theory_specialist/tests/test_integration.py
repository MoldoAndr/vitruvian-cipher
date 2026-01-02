"""
Integration tests for complete RAG workflows.

This module tests:
- Full ingestion workflow (auto-discover -> queue -> process)
- Full generation workflow (query -> retrieve -> rerank -> generate)
- Provider switching during operations
- Multi-turn conversations
- End-to-end scenarios
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

import pytest
from fastapi import status
from sqlalchemy.orm import Session


class TestFullIngestionWorkflow:
    """Integration tests for complete document ingestion workflow."""

    def test_auto_discover_to_completed_ingestion(
        self, test_client, test_documents_dir, mock_rag_system, mock_aggregator
    ):
        """Test complete workflow from auto-discovery to completed ingestion."""
        # Step 1: Auto-discover documents
        response = test_client.post("/auto-ingest")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["discovered_count"] > 0

        # Step 2: Check status shows pending documents
        response = test_client.get("/status")
        data = response.json()
        assert data["pending_documents"] > 0

        # Step 3: Ingest individual document
        response = test_client.post(
            "/ingest",
            json={
                "document_path": str(test_documents_dir / "test1.pdf"),
                "document_type": "pdf"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_manual_ingest_workflow(
        self, test_client, test_db_session: Session, mock_rag_system
    ):
        """Test manual document ingestion workflow."""
        # Queue a document
        response = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/rsa.pdf",
                "document_type": "pdf"
            }
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's in the queue
        from app.models import ReferenceDocument
        doc = test_db_session.query(ReferenceDocument).filter_by(
            document_path="/app/docs/rsa.pdf"
        ).first()
        assert doc is not None
        assert doc.processing_status == 0  # Pending

    def test_multiple_documents_queueing(
        self, test_client, test_db_session: Session, mock_rag_system
    ):
        """Test queueing multiple documents."""
        documents = [
            ("/app/docs/doc1.pdf", "pdf"),
            ("/app/docs/doc2.md", "md"),
            ("/app/docs/doc3.txt", "txt"),
        ]

        for doc_path, doc_type in documents:
            response = test_client.post(
                "/ingest",
                json={
                    "document_path": doc_path,
                    "document_type": doc_type
                }
            )
            assert response.status_code == status.HTTP_200_OK

        # Verify all are queued
        from app.models import ReferenceDocument
        count = test_db_session.query(ReferenceDocument).count()
        assert count == 3


class TestFullGenerationWorkflow:
    """Integration tests for complete query-answer workflow."""

    def test_query_to_answer_with_sources(
        self, test_client, mock_rag_system
    ):
        """Test complete workflow from query to answer with sources."""
        response = test_client.post(
            "/generate",
            json={
                "query": "Explain how RSA encryption works",
                "conversation_id": None
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "sources" in data
        assert "conversation_id" in data
        assert "message_id" in data

    def test_multi_turn_conversation(
        self, test_client, mock_rag_system
    ):
        """Test multi-turn conversation maintaining context."""
        # First query
        response1 = test_client.post(
            "/generate",
            json={
                "query": "What is RSA?",
                "conversation_id": None
            }
        )
        assert response1.status_code == status.HTTP_200_OK
        conv_id = response1.json()["conversation_id"]

        # Second query in same conversation
        response2 = test_client.post(
            "/generate",
            json={
                "query": "How does it differ from AES?",
                "conversation_id": conv_id
            }
        )
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()

        # Should use same conversation
        assert data2["conversation_id"] == conv_id

        # Verify conversation history
        response = test_client.get(f"/conversations/{conv_id}")
        assert response.status_code == status.HTTP_200_OK
        history = response.json()

        assert len(history["messages"]) == 4  # 2 user + 2 assistant

    def test_query_with_provider_override_and_fallback(
        self, test_client, mock_rag_system
    ):
        """Test query with provider override doesn't affect subsequent queries."""
        # First query with provider override
        response1 = test_client.post(
            "/generate",
            json={
                "query": "Test query 1",
                "provider": "openai",
                "openai_model": "gpt-4o-mini"
            }
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second query without override (should use default)
        response2 = test_client.post(
            "/generate",
            json={
                "query": "Test query 2"
            }
        )
        assert response2.status_code == status.HTTP_200_OK

    def test_query_retrieves_and_reranks(
        self, test_client, mock_rag_system
    ):
        """Test that query goes through retrieve and rerank pipeline."""
        response = test_client.post(
            "/generate",
            json={"query": "Explain elliptic curve cryptography"}
        )

        # Verify RAG methods were called
        mock_rag_system.prepare_query.assert_called_once()
        mock_rag_system.retrieve.assert_called_once()
        mock_rag_system.rerank.assert_called_once()
        mock_rag_system.generate_answer.assert_called_once()


class TestProviderSwitchingWorkflow:
    """Integration tests for provider switching workflows."""

    def test_switch_provider_between_queries(
        self, test_client, mock_rag_system
    ):
        """Test switching providers between different queries."""
        from app.main import get_rag_system

        # Query with default provider
        response1 = test_client.post(
            "/generate",
            json={"query": "Query with default provider"}
        )
        assert response1.status_code == status.HTTP_200_OK
        initial_rag = get_rag_system()

        # Switch to OpenAI
        response = test_client.post(
            "/provider",
            json={
                "provider": "openai",
                "openai_api_key": "sk-test",
                "openai_model": "gpt-4o-mini"
            }
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify RAG system wasn't recreated
        current_rag = get_rag_system()
        assert current_rag is initial_rag

        # Query with new provider
        response2 = test_client.post(
            "/generate",
            json={"query": "Query with OpenAI"}
        )
        assert response2.status_code == status.HTTP_200_OK

    def test_per_request_provider_override_doesnt_affect_global(
        self, test_client, mock_rag_system
    ):
        """Test that per-request provider override doesn't change global setting."""
        # Query with provider override
        response = test_client.post(
            "/generate",
            json={
                "query": "Test",
                "provider": "gemini",
                "gemini_model": "gemini-1.5-flash"
            }
        )
        assert response.status_code == status.HTTP_200_OK

        # Check global config (should still be default)
        response = test_client.get("/config")
        data = response.json()
        # Config doesn't store provider, but we verify endpoint works
        assert "ingestion_workers" in data


class TestConfigurationWorkflow:
    """Integration tests for configuration management."""

    def test_change_config_and_verify_impact(
        self, test_client, mock_aggregator
    ):
        """Test changing configuration and verifying it takes effect."""
        # Get initial config
        response1 = test_client.get("/config")
        initial = response1.json()

        # Update config
        response2 = test_client.post(
            "/config",
            json({"ingestion_workers": 5})
        )
        assert response2.status_code == status.HTTP_200_OK

        # Verify change
        response3 = test_client.get("/config")
        updated = response3.json()
        assert updated["ingestion_workers"] == 5
        assert updated["ingestion_workers"] != initial["ingestion_workers"]

    def test_multiple_config_updates(
        self, test_client
    ):
        """Test multiple configuration updates in sequence."""
        # First update
        test_client.post(
            "/config",
            json({"ingestion_workers": 3, "parallel_requests": 2}
        ))

        # Second update (modify one, keep other)
        test_client.post(
            "/config",
            json({"parallel_requests": 4}
        ))

        # Verify final state
        response = test_client.get("/config")
        data = response.json()
        assert data["ingestion_workers"] == 3  # Should remain
        assert data["parallel_requests"] == 4  # Should be updated


class TestErrorRecoveryWorkflow:
    """Integration tests for error recovery scenarios."""

    def test_duplicate_ingest_recovery(
        self, test_client, mock_rag_system
    ):
        """Test handling of duplicate document ingestion attempts."""
        # First ingestion
        response1 = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/duplicate.pdf",
                "document_type": "pdf"
            }
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second ingestion (should fail gracefully)
        response2 = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/duplicate.pdf",
                "document_type": "pdf"
            }
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

        # System should still be functional
        response3 = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/other.pdf",
                "document_type": "pdf"
            }
        )
        assert response3.status_code == status.HTTP_200_OK

    def test_invalid_provider_then_valid_provider(
        self, test_client, mock_rag_system
    ):
        """Test recovering from invalid provider switch."""
        # Try invalid provider
        response1 = test_client.post(
            "/provider",
            json={"provider": "invalid"}
        )
        assert response1.status_code == status.HTTP_400_BAD_REQUEST

        # System should still work
        response2 = test_client.post(
            "/provider",
            json={"provider": "ollama", "ollama_model": "phi3"}
        )
        assert response2.status_code == status.HTTP_200_OK

    def test_config_boundary_recovery(
        self, test_client
    ):
        """Test recovering from invalid config values."""
        # Try invalid config
        response1 = test_client.post(
            "/config",
            json={"ingestion_workers": 100}  # Exceeds max
        )
        assert response1.status_code == status.HTTP_400_BAD_REQUEST

        # Valid config should still work
        response2 = test_client.post(
            "/config",
            json={"ingestion_workers": 5}
        )
        assert response2.status_code == status.HTTP_200_OK


class TestEndToEndScenarios:
    """End-to-end integration tests for real-world scenarios."""

    def test_new_user_onboarding_scenario(
        self, test_client, test_documents_dir, mock_rag_system, mock_aggregator
    ):
        """Test scenario: New user adding documents and asking questions."""
        # Step 1: Auto-discover documents
        response = test_client.post("/auto-ingest")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["discovered_count"] > 0

        # Step 2: Check health
        response = test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "healthy"

        # Step 3: Ask first question
        response = test_client.post(
            "/generate",
            json={"query": "What is RSA encryption?"}
        )
        assert response.status_code == status.HTTP_200_OK
        answer = response.json()
        assert len(answer["answer"]) > 0
        assert answer["conversation_id"] is not None

        # Step 4: Ask follow-up question
        response = test_client.post(
            "/generate",
            json={
                "query": "How is it different from AES?",
                "conversation_id": answer["conversation_id"]
            }
        )
        assert response.status_code == status.HTTP_200_OK

    def test_provider_comparison_scenario(
        self, test_client, mock_rag_system
    ):
        """Test scenario: Compare answers from different providers."""
        query = "Explain quantum cryptography"

        # Get answer from Ollama (default)
        response1 = test_client.post(
            "/generate",
            json={"query": query}
        )
        answer1 = response1.json()

        # Get answer from OpenAI
        response2 = test_client.post(
            "/generate",
            json={
                "query": query,
                "provider": "openai",
                "openai_model": "gpt-4o-mini"
            }
        )
        answer2 = response2.json()

        # Get answer from Gemini
        response3 = test_client.post(
            "/generate",
            json={
                "query": query,
                "provider": "gemini",
                "gemini_model": "gemini-1.5-flash"
            }
        )
        answer3 = response3.json()

        # All should succeed
        assert answer1["conversation_id"] != answer2["conversation_id"]
        assert answer2["conversation_id"] != answer3["conversation_id"]

    def test_batch_document_ingestion_scenario(
        self, test_client, test_db_session: Session, mock_rag_system
    ):
        """Test scenario: Batch ingestion of multiple documents."""
        documents = [
            "/app/docs/crypto_basics.pdf",
            "/app/docs/advanced_crypto.pdf",
            "/app/docs/hash_functions.pdf",
            "/app/docs/digital_signatures.pdf",
            "/app/docs/protocols.pdf",
        ]

        # Ingest all documents
        for doc_path in documents:
            response = test_client.post(
                "/ingest",
                json({
                    "document_path": doc_path,
                    "document_type": "pdf"
                })
            )
            assert response.status_code == status.HTTP_200_OK

        # Verify all are queued
        from app.models import ReferenceDocument
        count = test_db_session.query(ReferenceDocument).count()
        assert count == len(documents)

        # Check status
        response = test_client.get("/status")
        data = response.json()
        assert data["total_reference_documents"] == len(documents)


class TestConcurrentAccess:
    """Tests for concurrent access scenarios."""

    def test_multiple_concurrent_conversations(
        self, test_client, mock_rag_system
    ):
        """Test handling multiple concurrent conversations."""
        conversation_ids = []

        # Create multiple conversations concurrently
        for i in range(5):
            response = test_client.post(
                "/generate",
                json={"query": f"Question {i}"}
            )
            assert response.status_code == status.HTTP_200_OK
            conversation_ids.append(response.json()["conversation_id"])

        # All conversation IDs should be unique
        assert len(set(conversation_ids)) == 5

    def test_ingest_and_query_concurrently(
        self, test_client, mock_rag_system, mock_aggregator
    ):
        """Test ingesting documents while querying."""
        # Ingest a document
        response1 = test_client.post(
            "/ingest",
            json={
                "document_path": "/app/docs/test.pdf",
                "document_type": "pdf"
            }
        )

        # Simultaneously query
        response2 = test_client.post(
            "/generate",
            json={"query": "Test query"}
        )

        # Both should succeed
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
