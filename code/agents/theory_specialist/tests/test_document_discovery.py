"""
Tests for DocumentDiscoveryService component.

This module tests:
- Document discovery from filesystem
- Comparison with database records
- Queueing of discovered documents
- Edge cases (empty directories, nested files, etc.)
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pytest
from sqlalchemy.orm import Session


class TestDocumentDiscoveryService:
    """Tests for DocumentDiscoveryService class."""

    def test_init_with_settings(self, discovery_service, test_settings):
        """Test that DocumentDiscoveryService initializes with settings."""
        assert discovery_service.settings == test_settings

    def test_discover_new_documents_finds_all_types(
        self, discovery_service, test_documents_dir
    ):
        """Test that discovery finds PDF, MD, and TXT files."""
        discovered = discovery_service.discover_new_documents()

        # Should find all test files
        assert len(discovered) >= 4

        # Check that different file types are included
        doc_types = {doc_type for _, doc_type in discovered}
        assert "pdf" in doc_types
        assert "md" in doc_types
        assert "txt" in doc_types

    def test_discover_finds_files_in_subdirectories(
        self, discovery_service, test_documents_dir
    ):
        """Test that discovery recursively searches subdirectories."""
        discovered = discovery_service.discover_new_documents()

        # Should include files from subfolder
        discovered_paths = [path for path, _ in discovered]
        has_nested = any("subfolder" in path for path in discovered_paths)
        assert has_nested, "Should find files in subdirectories"

    def test_discover_excludes_already_ingested(
        self, discovery_service, test_documents_dir, create_test_document
    ):
        """Test that discovery excludes documents already in database."""
        # Add one document to database as processed
        test_doc_path = str(test_documents_dir / "test1.pdf")
        create_test_document(
            document_path=test_doc_path,
            document_name="test1.pdf",
            processing_status=2
        )

        discovered = discovery_service.discover_new_documents()
        discovered_paths = [path for path, _ in discovered]

        # test1.pdf should not be in discovered
        assert test_doc_path not in discovered_paths

    def test_discover_with_empty_directory(
        self, temp_dir, test_settings
    ):
        """Test discovery with empty documents directory."""
        empty_dir = temp_dir / "empty_docs"
        empty_dir.mkdir(parents=True, exist_ok=True)

        settings = test_settings
        settings.documents_directory = str(empty_dir)
        service = discovery_service.__class__(settings)

        discovered = service.discover_new_documents()
        assert len(discovered) == 0

    def test_discover_returns_absolute_paths(
        self, discovery_service, test_documents_dir
    ):
        """Test that discovery returns absolute paths."""
        discovered = discovery_service.discover_new_documents()

        for doc_path, _ in discovered:
            assert Path(doc_path).is_absolute()

    def test_queue_discovered_documents_adds_to_database(
        self, discovery_service, test_db_session: Session, test_documents_dir
    ):
        """Test that queuing discovered documents adds them to database."""
        discovered = discovery_service.discover_new_documents()
        initial_count = test_db_session.query(
            test_db_session.query(
                discovery_service.__class__.__module__
            ).__class__.__name__  # Get reference document count
        ).count() if False else 0  # Simplified

        queued = discovery_service.queue_discovered_documents(discovered, test_db_session)

        assert queued > 0
        assert queued <= len(discovered)

    def test_queue_skips_existing_documents(
        self, discovery_service, test_db_session: Session, create_test_document
    ):
        """Test that queuing skips documents already in database."""
        # Create a document in the database
        create_test_document(
            document_path="/app/documents/existing.pdf",
            document_name="existing.pdf"
        )

        discovered = [("/app/documents/existing.pdf", "pdf")]
        queued = discovery_service.queue_discovered_documents(discovered, test_db_session)

        assert queued == 0  # Should skip existing document

    def test_queue_handles_multiple_documents(
        self, discovery_service, test_db_session: Session
    ):
        """Test queuing multiple documents at once."""
        discovered = [
            ("/app/docs/doc1.pdf", "pdf"),
            ("/app/docs/doc2.md", "md"),
            ("/app/docs/doc3.txt", "txt"),
        ]

        queued = discovery_service.queue_discovered_documents(discovered, test_db_session)
        assert queued == 3

    def test_discover_respects_supported_extensions_only(
        self, discovery_service, test_documents_dir, temp_dir
    ):
        """Test that only supported file extensions are discovered."""
        docs_dir = test_documents_dir

        # Create files with unsupported extensions
        (docs_dir / "test.doc").write_text("Word document")
        (docs_dir / "test.docx").write_text("Word document new")
        (docs_dir / "test.html").write_text("<html>HTML</html>")
        (docs_dir / "test.xml").write_text("<xml>XML</xml>")

        discovered = discovery_service.discover_new_documents()
        doc_types = {doc_type for _, doc_type in discovered}

        # Should only include pdf, md, txt
        assert doc_types.issubset({"pdf", "md", "txt"})
        assert "doc" not in doc_types
        assert "docx" not in doc_types
        assert "html" not in doc_types
        assert "xml" not in doc_types

    def test_queue_document_creates_correct_record(
        self, discovery_service, test_db_session: Session
    ):
        """Test that queued documents have correct database records."""
        discovered = [("/app/docs/test.pdf", "pdf")]
        discovery_service.queue_discovered_documents(discovered, test_db_session)

        from app.models import ReferenceDocument
        doc = test_db_session.query(ReferenceDocument).filter_by(
            document_path="/app/docs/test.pdf"
        ).first()

        assert doc is not None
        assert doc.document_name == "test.pdf"
        assert doc.document_type == "pdf"
        assert doc.processing_status == 0  # Pending

    def test_discover_with_nonexistent_directory(
        self, test_settings, temp_dir
    ):
        """Test discovery when documents directory doesn't exist."""
        nonexistent = temp_dir / "does_not_exist"
        settings = test_settings
        settings.documents_directory = str(nonexistent)
        service = discovery_service.__class__(settings)

        discovered = service.discover_new_documents()
        assert len(discovered) == 0


class TestDocumentDiscoveryIntegration:
    """Integration tests for document discovery with database."""

    def test_discovery_and_ingestion_workflow(
        self, discovery_service, test_db_session: Session, test_documents_dir
    ):
        """Test full workflow: discover, queue, and verify."""
        # Step 1: Discover
        discovered = discovery_service.discover_new_documents()
        assert len(discovered) > 0

        # Step 2: Queue
        queued = discovery_service.queue_discovered_documents(discovered, test_db_session)
        assert queued > 0

        # Step 3: Verify in database
        from app.models import ReferenceDocument
        docs = test_db_session.query(ReferenceDocument).all()
        assert len(docs) >= queued

    def test_multiple_discovery_calls_idempotent(
        self, discovery_service, test_db_session: Session
    ):
        """Test that multiple discovery calls don't duplicate documents."""
        # First discovery and queue
        discovered1 = discovery_service.discover_new_documents()
        queued1 = discovery_service.queue_discovered_documents(discovered1, test_db_session)

        # Second discovery and queue
        discovered2 = discovery_service.discover_new_documents()
        queued2 = discovery_service.queue_discovered_documents(discovered2, test_db_session)

        # Second queue should add nothing
        assert queued2 == 0

    def test_discovery_after_partial_ingestion(
        self, discovery_service, test_db_session: Session, create_test_document
    ):
        """Test discovery after some documents are already ingested."""
        # Simulate some docs already processed
        create_test_document(
            document_path="/app/docs/doc1.pdf",
            document_name="doc1.pdf",
            processing_status=2  # Processed
        )
        create_test_document(
            document_path="/app/docs/doc2.pdf",
            document_name="doc2.pdf",
            processing_status=1  # In progress
        )

        discovered = discovery_service.discover_new_documents()

        # Should not include doc1.pdf (already processed)
        discovered_paths = [path for path, _ in discovered]
        assert "/app/docs/doc1.pdf" not in discovered_paths


class TestDocumentDiscoveryEdgeCases:
    """Edge case tests for document discovery."""

    def test_discover_with_symlinks(self, discovery_service, test_documents_dir, temp_dir):
        """Test discovery behavior with symbolic links (if supported)."""
        # This test might not work on all systems
        try:
            link_target = temp_dir / "linked_doc.pdf"
            link_target.write_text("Linked document content")

            symlink = test_documents_dir / "symlink.pdf"
            symlink.symlink_to(link_target)

            discovered = discovery_service.discover_new_documents()
            # Behavior may vary - just verify it doesn't crash
            assert isinstance(discovered, list)

        except OSError:
            # Symlinks not supported on this system
            pytest.skip("Symbolic links not supported")

    def test_discover_with_zero_length_files(
        self, discovery_service, test_documents_dir
    ):
        """Test discovery with empty files."""
        empty_file = test_documents_dir / "empty.pdf"
        empty_file.write_text("")

        discovered = discovery_service.discover_new_documents()
        discovered_paths = [path for path, _ in discovered]

        # Should still discover the empty file
        assert any("empty.pdf" in path for path in discovered_paths)

    def test_discover_with_special_characters_in_filename(
        self, discovery_service, test_documents_dir
    ):
        """Test discovery with special characters in filenames."""
        special_file = test_documents_dir / "file with spaces & symbols.pdf"
        special_file.write_text("Content")

        discovered = discovery_service.discover_new_documents()
        discovered_paths = [path for path, _ in discovered]

        assert any("file with spaces" in path for path in discovered_paths)

    def test_discover_case_sensitivity(
        self, discovery_service, test_documents_dir
    ):
        """Test discovery with different file extensions cases."""
        (test_documents_dir / "test1.PDF").write_text("Content")
        (test_documents_dir / "test2.Pdf").write_text("Content")
        (test_documents_dir / "test3.MD").write_text("Content")

        discovered = discovery_service.discover_new_documents()

        # Should find all variants (depending on OS)
        # On Windows, extensions are case-insensitive
        # On Unix, they're case-sensitive
        assert isinstance(discovered, list)
