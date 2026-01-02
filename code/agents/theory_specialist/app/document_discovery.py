"""
Automatic document discovery service.

Scans the documents folder and identifies files that are not yet ingested
into the database for automatic ingestion.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .database import SessionLocal
from .models import ReferenceDocument

logger = logging.getLogger(__name__)


class DocumentDiscoveryService:
    """
    Service for automatically discovering documents in the filesystem
    that are not yet ingested into the database.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def discover_new_documents(self) -> List[Tuple[str, str]]:
        """
        Scan the documents directory and return documents not in the database.

        Returns:
            List of tuples (document_path, document_type) for new documents.
        """
        documents_dir = Path(self.settings.documents_directory).resolve()
        if not documents_dir.exists():
            logger.warning("Documents directory does not exist: %s", documents_dir)
            return []

        # Get all document paths from database
        with SessionLocal() as session:
            existing_paths = {
                doc.document_path
                for doc in session.query(ReferenceDocument.document_path).all()
            }

        # Supported file extensions
        supported_extensions = {
            ".pdf": "pdf",
            ".md": "md",
            ".txt": "txt",
        }

        new_documents = []

        # Scan for new documents
        for ext, doc_type in supported_extensions.items():
            for file_path in documents_dir.rglob(f"*{ext}"):
                if file_path.is_file():
                    # Store relative path if under documents dir
                    try:
                        rel_path = str(file_path.relative_to(documents_dir))
                    except ValueError:
                        # File is not under documents_dir (shouldn't happen with rglob from root)
                        rel_path = str(file_path)

                    # Full path for ingestion
                    full_path = str(file_path)

                    # Check if already in database (try both relative and full path)
                    if full_path not in existing_paths and rel_path not in existing_paths:
                        new_documents.append((full_path, doc_type))
                        logger.debug("Discovered new document: %s", rel_path)

        logger.info("Discovered %d new documents", len(new_documents))
        return new_documents

    def queue_discovered_documents(
        self, documents: List[Tuple[str, str]], db: Session
    ) -> int:
        """
        Queue discovered documents for ingestion.

        Args:
            documents: List of tuples (document_path, document_type)
            db: Database session

        Returns:
            Number of documents successfully queued.
        """
        queued_count = 0

        for doc_path, doc_type in documents:
            # Check if already exists
            existing = (
                db.query(ReferenceDocument)
                .filter(ReferenceDocument.document_path == doc_path)
                .first()
            )
            if existing:
                logger.debug("Document already exists in database: %s", doc_path)
                continue

            # Create document name from path
            document_name = Path(doc_path).name

            reference = ReferenceDocument(
                document_path=doc_path,
                document_name=document_name,
                document_type=doc_type,
            )
            db.add(reference)
            queued_count += 1
            logger.info("Queued document for auto-ingestion: %s", document_name)

        try:
            db.commit()
        except Exception as exc:
            logger.error("Failed to queue discovered documents: %s", exc)
            db.rollback()
            return 0

        return queued_count
