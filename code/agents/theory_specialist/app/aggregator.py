"""
Document ingestion scheduler powered by APScheduler.
"""

from __future__ import annotations

import logging
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .database import SessionLocal
from .models import ReferenceDocument
from .rag_system import RAGSystem

logger = logging.getLogger(__name__)


class DocumentAggregator:
    """
    Periodically processes queued documents and feeds them to the RAG system.
    """

    def __init__(
        self,
        rag_system: RAGSystem,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.rag_system = rag_system
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._lock = threading.Lock()

    def start(self) -> None:
        if self.scheduler.running:
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
        logger.info("Document aggregator started (interval=%ss)", interval)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Document aggregator stopped.")

    def _process_queue(self) -> None:
        if not self._lock.acquire(blocking=False):
            return
        try:
            processed = 0
            while processed < self.settings.ingestion_batch_size:
                with SessionLocal() as session:
                    document = (
                        session.query(ReferenceDocument)
                        .filter(ReferenceDocument.processing_status == 0)
                        .order_by(ReferenceDocument.document_name.asc())
                        .first()
                    )
                    if not document:
                        return

                    document.processing_status = 1
                    document.error_message = None
                    session.commit()
                    session.refresh(document)

                    logger.info("Aggregator picked document %s", document.document_name)

                    try:
                        chunk_count = self.rag_system.process_reference_document(
                            session, document
                        )
                        session.commit()
                        logger.info(
                            "Document %s ingested (%d chunks)",
                            document.document_name,
                            chunk_count,
                        )
                        processed += 1
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.exception(
                            "Failed processing document %s: %s",
                            document.document_name,
                            exc,
                        )
                        session.rollback()
                        self._mark_failed(session, document.id, str(exc))
                        break
        finally:
            self._lock.release()

    @staticmethod
    def _mark_failed(session: Session, doc_id: int, error: str) -> None:
        document = session.get(ReferenceDocument, doc_id)
        if not document:
            return
        document.processing_status = 0
        document.processed_at = None
        document.error_message = error[:1000]
        document.chunks_count = 0
        session.commit()
