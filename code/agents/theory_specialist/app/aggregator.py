"""
Document ingestion scheduler powered by APScheduler.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .database import SessionLocal
from .models import ReferenceDocument
from .rag_system import RAGSystem

logger = logging.getLogger(__name__)


class DocumentAggregator:
    """
    Periodically processes queued documents and feeds them to the RAG system.

    Thread-safe implementation with proper error handling and state management.
    """

    def __init__(
        self,
        rag_system: RAGSystem,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.rag_system = rag_system
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._lock = threading.RLock()  # Use RLock for reentrant locking
        self._is_running = False

    def start(self) -> None:
        """Start the document aggregator scheduler."""
        with self._lock:
            if self._is_running:
                logger.info("Document aggregator already running.")
                return
            if self.scheduler.running:
                logger.info("Document aggregator scheduler already started.")
                return

            interval = self.settings.ingestion_interval_seconds
            self.scheduler.add_job(
                self._process_queue,
                "interval",
                seconds=interval,
                max_instances=1,
                coalesce=True,
            )
            self.scheduler.start()
            self._is_running = True
            logger.info("Document aggregator started (interval=%ss)", interval)

    def shutdown(self) -> None:
        """Stop the document aggregator scheduler."""
        with self._lock:
            if not self._is_running:
                return
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("Document aggregator stopped.")
            self._is_running = False

    def _process_queue(self) -> None:
        """Process pending documents from the queue."""
        # Use non-blocking attempt to prevent concurrent processing
        if not self._lock.acquire(blocking=False):
            logger.debug("Aggregator busy, skipping this cycle.")
            return

        try:
            processed = 0
            batch_size = self.settings.ingestion_batch_size

            while processed < batch_size:
                # Use a separate session for each document to avoid long transactions
                with SessionLocal() as session:
                    try:
                        # Find next pending document with row-level locking
                        document = (
                            session.query(ReferenceDocument)
                            .filter(ReferenceDocument.processing_status == 0)
                            .order_by(ReferenceDocument.document_name.asc())
                            .first()
                        )
                        if not document:
                            logger.debug("No pending documents to process.")
                            return

                        # Mark as in-progress
                        document.processing_status = 1
                        document.error_message = None
                        session.commit()
                        session.refresh(document)

                        logger.info(
                            "Aggregator processing document %s (id=%d)",
                            document.document_name,
                            document.id,
                        )

                        # Process the document
                        chunk_count = self.rag_system.process_reference_document(
                            session, document
                        )
                        session.commit()
                        logger.info(
                            "Document %s ingested successfully (%d chunks)",
                            document.document_name,
                            chunk_count,
                        )
                        processed += 1

                    except (ValueError, OSError) as exc:
                        # Handle expected errors (file not found, invalid format, etc.)
                        logger.warning(
                            "Document %s processing failed (non-database error): %s",
                            document.document_name if document else "unknown",
                            exc,
                        )
                        session.rollback()
                        self._mark_failed(session, document.id, str(exc))
                        break  # Stop processing on non-database errors

                    except DatabaseError as exc:
                        # Handle database-specific errors
                        logger.error(
                            "Database error processing document %s: %s",
                            document.document_name if document else "unknown",
                            exc,
                        )
                        session.rollback()
                        break  # Stop processing on database errors

                    except Exception as exc:  # pylint: disable=broad-except
                        # Handle unexpected errors
                        logger.exception(
                            "Unexpected error processing document %s: %s",
                            document.document_name if document else "unknown",
                            exc,
                        )
                        session.rollback()
                        self._mark_failed(session, document.id, f"Unexpected error: {exc}")
                        break

        finally:
            self._lock.release()

    def _mark_failed(self, session: Session, doc_id: int, error: str) -> None:
        """Mark a document as failed with an error message."""
        try:
            document = session.get(ReferenceDocument, doc_id)
            if not document:
                logger.warning("Document %d not found when marking as failed.", doc_id)
                return

            document.processing_status = 0  # Reset to pending for retry
            document.processed_at = None
            document.error_message = error[:1000]  # Truncate to column size
            document.chunks_count = 0
            session.commit()
            logger.info("Document %s marked as failed: %s", document.document_name, error[:100])
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to mark document %d as failed: %s", doc_id, exc)
            try:
                session.rollback()
            except Exception:
                pass
