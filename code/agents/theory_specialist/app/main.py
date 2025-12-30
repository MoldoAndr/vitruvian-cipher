"""
FastAPI entrypoint implementing the Cryptography RAG API.
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
from contextlib import asynccontextmanager
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import StarletteHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .aggregator import DocumentAggregator
from .config import get_settings
from .database import Base, engine, get_db
from .llm_client import build_llm_client
from .models import Conversation, Message, ReferenceDocument
from .rag_system import RAGSystem, RetrievedChunk
from .schemas import (
    ConversationHistoryResponse,
    ConversationMessage,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    ProviderUpdateRequest,
    ProviderUpdateResponse,
    SourceChunk,
    StatusResponse,
)


logger = logging.getLogger("cryptography_rag")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Global state (protected by locks)
_global_settings = get_settings()
_global_rag_system: Optional[RAGSystem] = None
_global_aggregator: Optional[DocumentAggregator] = None
provider_lock = threading.Lock()
settings_lock = threading.RLock()  # Use RLock for re-entrant locking


def get_rag_system() -> RAGSystem:
    """Get the global RAG system instance."""
    global _global_rag_system
    if _global_rag_system is None:
        with settings_lock:
            if _global_rag_system is None:
                _global_rag_system = RAGSystem(settings=_global_settings)
    return _global_rag_system


def get_aggregator() -> DocumentAggregator:
    """Get the global aggregator instance."""
    global _global_aggregator
    if _global_aggregator is None:
        with settings_lock:
            if _global_aggregator is None:
                _global_aggregator = DocumentAggregator(
                    rag_system=get_rag_system(),
                    settings=_global_settings
                )
    return _global_aggregator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    Base.metadata.create_all(bind=engine)
    aggregator = get_aggregator()
    aggregator.start()
    logger.info("Application startup complete.")
    yield
    # Shutdown
    aggregator.shutdown()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title="Cryptography RAG System",
    version="1.0.0",
    description="Retrieval-Augmented Generation system for cryptography theory.",
    lifespan=lifespan,
)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: RequestValidationError,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.error("Validation error: %s", exc.errors())
    body = getattr(exc, "body", None)
    if body is not None:
        logger.error("Request body: %s", body)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body},
    )


def _resolve_document_name(document_path: str) -> str:
    if document_path.startswith(("http://", "https://")):
        parsed = urlparse(document_path)
        return (parsed.path.split("/")[-1] or "remote_document").strip()
    return document_path.split("/")[-1] or document_path


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    rag_system = get_rag_system()
    try:
        db.execute(func.count(ReferenceDocument.id))
        database_status = "connected"
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Health check database failure: %s", exc)
        database_status = "error"

    try:
        vector_chunks = rag_system.collection.count()
        status_str = "healthy"
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Health check vector DB failure: %s", exc)
        status_str = "degraded"
        vector_chunks = 0

    provider = (_global_settings.llm_provider or "ollama").lower().strip()
    if provider == "openai":
        generation_model = _global_settings.openai_model
    elif provider == "gemini":
        generation_model = _global_settings.gemini_model
    else:
        generation_model = _global_settings.ollama_model

    return HealthResponse(
        status=status_str,
        database=database_status,
        embedding_model=_global_settings.embedding_model_name,
        generation_model=generation_model,
        vector_db_chunks=vector_chunks,
        timestamp=dt.datetime.utcnow(),
    )


@app.post("/provider", response_model=ProviderUpdateResponse)
def update_provider(payload: ProviderUpdateRequest) -> ProviderUpdateResponse:
    provider = payload.provider.strip().lower().replace(" ", "-")
    if provider in ("ollama_cloud", "ollama-cloud"):
        provider = "ollama-cloud"
    if provider not in ("ollama", "ollama-cloud", "gemini", "openai"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider. Use ollama, ollama-cloud, gemini, or openai.",
        )

    global _global_settings, _global_rag_system

    # Build update dictionary with only non-None values
    updates = {"llm_provider": provider}
    if payload.ollama_url is not None:
        updates["ollama_url"] = payload.ollama_url
    if payload.ollama_model is not None:
        updates["ollama_model"] = payload.ollama_model
    if payload.ollama_api_key is not None:
        updates["ollama_api_key"] = payload.ollama_api_key
    if payload.ollama_use_chat is not None:
        updates["ollama_use_chat"] = payload.ollama_use_chat
    if payload.openai_api_key is not None:
        updates["openai_api_key"] = payload.openai_api_key
    if payload.openai_model is not None:
        updates["openai_model"] = payload.openai_model
    if payload.openai_base_url is not None:
        updates["openai_base_url"] = payload.openai_base_url
    if payload.gemini_api_key is not None:
        updates["gemini_api_key"] = payload.gemini_api_key
    if payload.gemini_model is not None:
        updates["gemini_model"] = payload.gemini_model
    if payload.gemini_base_url is not None:
        updates["gemini_base_url"] = payload.gemini_base_url

    # Auto-correct URL for ollama-cloud
    if provider == "ollama-cloud":
        current_url = updates.get("ollama_url", _global_settings.ollama_url)
        if current_url.startswith(
            ("http://127.0.0.1", "http://localhost", "http://ollama")
        ):
            updates["ollama_url"] = "https://ollama.com"

    with provider_lock:
        # Create new settings instance instead of mutating
        new_settings = _global_settings.create_updated_copy(**updates)
        _global_settings = new_settings

        # Rebuild RAG system with new settings
        rag_system = RAGSystem(settings=new_settings)
        _global_rag_system = rag_system

    if provider == "openai":
        generation_model = new_settings.openai_model
        base_url = new_settings.openai_base_url
    elif provider == "gemini":
        generation_model = new_settings.gemini_model
        base_url = new_settings.gemini_base_url
    else:
        generation_model = new_settings.ollama_model
        base_url = new_settings.ollama_url

    return ProviderUpdateResponse(
        status="updated",
        provider=provider,
        generation_model=generation_model,
        base_url=base_url,
    )


@app.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_200_OK)
def ingest_document(
    payload: IngestRequest, db: Session = Depends(get_db)
) -> IngestResponse:
    rag_system = get_rag_system()
    try:
        rag_system.validate_document_path(payload.document_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None

    document_name = _resolve_document_name(payload.document_path)
    reference = ReferenceDocument(
        document_path=payload.document_path,
        document_name=document_name,
        document_type=payload.document_type,
    )
    db.add(reference)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document already queued: {payload.document_path}",
        ) from None

    logger.info("Queued document for ingestion: %s", payload.document_path)
    return IngestResponse(
        status="queued",
        message=f"Document added to processing queue: {payload.document_path}",
    )


@app.get("/status", response_model=StatusResponse)
def status_overview(db: Session = Depends(get_db)) -> StatusResponse:
    rag_system = get_rag_system()
    total_docs = db.query(func.count(ReferenceDocument.id)).scalar() or 0
    processed_docs = (
        db.query(func.count(ReferenceDocument.id))
        .filter(ReferenceDocument.processing_status == 2)
        .scalar()
        or 0
    )
    in_progress_docs = (
        db.query(func.count(ReferenceDocument.id))
        .filter(ReferenceDocument.processing_status == 1)
        .scalar()
        or 0
    )
    pending_docs = (
        db.query(func.count(ReferenceDocument.id))
        .filter(ReferenceDocument.processing_status == 0)
        .scalar()
        or 0
    )
    current_doc = (
        db.query(ReferenceDocument)
        .filter(ReferenceDocument.processing_status == 1)
        .order_by(ReferenceDocument.document_name.asc())
        .first()
    )

    try:
        total_chunks = rag_system.collection.count()
    except Exception:  # pylint: disable=broad-except
        total_chunks = 0

    return StatusResponse(
        total_reference_documents=total_docs,
        processed_documents=processed_docs,
        in_progress_documents=in_progress_docs,
        pending_documents=pending_docs,
        total_chunks_in_vector_db=total_chunks,
        currently_processing=current_doc.document_name if current_doc else None,
        timestamp=dt.datetime.utcnow(),
    )


def _get_or_create_conversation(
    db: Session, conversation_id: Optional[str]
) -> Conversation:
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.conversation_id == conversation_id)
            .first()
        )
        if conversation:
            return conversation
        # If conversation_id is provided but doesn't exist, create it with that ID
        conversation = Conversation(conversation_id=conversation_id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    # No conversation_id provided, create a new one
    conversation = Conversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def _format_sources(chunks: List[RetrievedChunk]) -> List[SourceChunk]:
    sources: list[SourceChunk] = []
    for chunk in chunks:
        metadata = dict(chunk.metadata)
        rerank_score = metadata.get("reranker_score", chunk.similarity)
        sources.append(
            SourceChunk(
                chunk_id=chunk.chunk_id,
                relevance_score=float(rerank_score),
                preview=chunk.text[:300],
                metadata=metadata,
            )
        )
    return sources


@app.post("/generate", response_model=GenerateResponse)
def generate_answer(
    payload: GenerateRequest, db: Session = Depends(get_db)
) -> GenerateResponse:
    # Validate query length
    if len(payload.query) > _global_settings.max_query_length:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Query exceeds maximum length of {_global_settings.max_query_length} characters.",
        )

    logger.info(
        "Received /generate request: query='%s', conversation_id='%s'",
        payload.query[:200],  # Log truncated query
        payload.conversation_id,
    )
    rag_system = get_rag_system()

    conversation = _get_or_create_conversation(db, payload.conversation_id)

    user_message = Message(
        conversation_id=conversation.conversation_id,
        role="user",
        content=payload.query,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    query_context = rag_system.prepare_query(payload.query)
    retrieved, _strategy = rag_system.retrieve(
        query_context.query_for_retrieval,
        top_k=_global_settings.retrieval_top_k,
    )
    reranked = rag_system.rerank(query_context.query_for_retrieval, retrieved)

    # Improved reranker fallback: only use unranked if reranking produced results
    # but all were below threshold, AND we have at least some relevant chunks
    if not reranked and retrieved:
        # Use vector scores as fallback filter
        filtered_retrieved = [
            chunk for chunk in retrieved
            if chunk.similarity >= _global_settings.min_source_score
        ]
        reranked = filtered_retrieved[: _global_settings.reranker_top_k]

    answer = rag_system.generate_answer(payload.query, reranked)

    assistant_message = Message(
        conversation_id=conversation.conversation_id,
        role="assistant",
        content=answer,
        retrieved_chunk_ids=[chunk.chunk_id for chunk in reranked],
        relevance_scores=[
            float(chunk.metadata.get("reranker_score", chunk.similarity))
            for chunk in reranked
        ],
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    return GenerateResponse(
        answer=answer,
        sources=_format_sources(reranked),
        conversation_id=conversation.conversation_id,
        message_id=assistant_message.id,
    )


@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationHistoryResponse,
)
def conversation_history(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(
        _global_settings.default_conversation_page_size,
        ge=1,
        le=_global_settings.max_conversation_page_size,
    ),
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    conversation = (
        db.query(Conversation)
        .filter(Conversation.conversation_id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # Paginate messages
    total_messages = len(conversation.messages)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_messages = conversation.messages[start_idx:end_idx]

    messages = [
        ConversationMessage(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        for message in paginated_messages
    ]

    return ConversationHistoryResponse(
        conversation_id=conversation.conversation_id,
        created_at=conversation.created_at,
        messages=messages,
    )
