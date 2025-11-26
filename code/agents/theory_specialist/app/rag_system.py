"""
RAG system implementation: document ingestion, retrieval, and generation.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import chromadb
import numpy as np
import requests
from chromadb import Collection
from chromadb.config import Settings as ChromaSettings
from fastembed import TextEmbedding
from langchain.text_splitter import RecursiveCharacterTextSplitter
from markdown import markdown
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .models import DocumentChunk, ReferenceDocument
from .ollama_client import OllamaClient
from .reranker import OnnxCrossEncoder

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    similarity: float


class RAGSystem:
    """
    Encapsulates embedding, retrieval, reranking, and generation logic.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._ensure_directories()

        self.embedding_model = TextEmbedding(
            model_name=self.settings.embedding_model_name,
            cache_dir=self.settings.models_cache_directory,
            threads=None,
        )
        self.reranker = OnnxCrossEncoder(
            model_name=self.settings.reranker_model_name,
            cache_dir=self.settings.models_cache_directory,
        )

        self.chroma_client = chromadb.PersistentClient(
            path=self.settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection: Collection = self.chroma_client.get_or_create_collection(
            name="cryptography_chunks",
            metadata={"hnsw:space": "cosine"},
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        self.ollama = OllamaClient(
            base_url=self.settings.ollama_url,
            model=self.settings.ollama_model,
            timeout=self.settings.ollama_request_timeout,
        )

        logger.info(
            "RAG system initialized with embedding=%s, reranker=%s, ollama_model=%s",
            self.settings.embedding_model_name,
            self.settings.reranker_model_name,
            self.settings.ollama_model,
        )

    # ------------------------------------------------------------------ #
    # Document ingestion
    # ------------------------------------------------------------------ #
    def process_reference_document(
        self, session: Session, document: ReferenceDocument
    ) -> int:
        """
        Load, chunk, embed, and persist a reference document.

        Returns the number of chunks created.
        """
        logger.info("Processing document %s", document.document_path)

        text_sections, file_size = self._load_document_sections(document)
        if not text_sections:
            raise ValueError("Document contains no textual content.")

        chunk_entries = self._chunk_sections(document, text_sections)
        if not chunk_entries:
            raise ValueError("No chunks produced after text splitting.")

        text_chunks = [entry["text"] for entry in chunk_entries]
        embeddings_list = list(
            self.embedding_model.embed(
                text_chunks,
                batch_size=self.settings.embedding_batch_size,
            )
        )

        # Remove previous chunks for idempotent processing
        self.collection.delete(where={"ref_doc_id": document.id})
        session.query(DocumentChunk).filter(
            DocumentChunk.reference_doc_id == document.id
        ).delete(synchronize_session=False)
        session.flush()

        ids: list[str] = []
        metadatas: list[dict] = []
        documents: list[str] = []
        chunk_models: list[DocumentChunk] = []
        for idx, (chunk, embedding) in enumerate(zip(chunk_entries, embeddings_list)):
            chunk_id = f"{document.id}_{idx}"
            ids.append(chunk_id)
            metadatas.append(
                {
                    "ref_doc_id": document.id,
                    "chunk_index": idx,
                    "source": document.document_name,
                    "source_page": chunk.get("page"),
                    "text": chunk["text"],
                }
            )
            documents.append(chunk["text"])
            chunk_models.append(
                DocumentChunk(
                    reference_doc_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk["text"],
                    token_count=len(chunk["text"].split()),
                    embedding_vector=json.dumps(np.asarray(embedding, dtype=float).tolist()),
                    embedding_model=self.settings.embedding_model_name,
                    source_title=document.document_name,
                    source_page=chunk.get("page"),
                )
            )

        if not ids:
            raise ValueError("No chunks generated for ingestion.")

        embedding_payload = [np.asarray(emb, dtype=float).tolist() for emb in embeddings_list]
        self.collection.add(
            ids=ids,
            embeddings=embedding_payload,
            metadatas=metadatas,
            documents=documents,
        )

        for model in chunk_models:
            session.add(model)

        document.file_size = file_size
        document.chunks_count = len(ids)
        document.processing_status = 2
        document.processed_at = dt.datetime.utcnow()
        document.error_message = None

        logger.info(
            "Document %s processed with %d chunks",
            document.document_name,
            len(ids),
        )
        return len(ids)

    # ------------------------------------------------------------------ #
    # Retrieval & generation
    # ------------------------------------------------------------------ #
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        top_k = top_k or self.settings.retrieval_top_k
        query_embedding = next(
            iter(
                self.embedding_model.embed(
                    [query],
                    batch_size=1,
                )
            )
        )

        query_vector = np.asarray(query_embedding, dtype=float).tolist()

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["metadatas", "distances", "documents"],
        )

        retrieved: list[RetrievedChunk] = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        for chunk_id, distance, metadata, document in zip(
            ids, distances, metadatas, documents
        ):
            if not metadata:
                metadata = {}
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=document or metadata.get("text", ""),
                    metadata=metadata,
                    similarity=1.0 - float(distance),
                )
            )

        return retrieved

    def rerank(self, query: str, chunks: Iterable[RetrievedChunk]) -> List[RetrievedChunk]:
        chunk_list = list(chunks)
        if not chunk_list:
            return []

        scores = self.reranker.score(query, [chunk.text for chunk in chunk_list])

        reranked: list[tuple[RetrievedChunk, float]] = []
        for chunk, score in zip(chunk_list, scores):
            if score >= self.settings.reranker_threshold:
                chunk.metadata["reranker_score"] = float(score)
                reranked.append((chunk, float(score)))

        reranked.sort(key=lambda item: item[1], reverse=True)
        top_chunks = [chunk for chunk, _ in reranked[: self.settings.reranker_top_k]]
        return top_chunks

    def generate_answer(self, query: str, chunks: List[RetrievedChunk]) -> str:
        if not chunks:
            return (
                "I do not have enough relevant context to answer this question yet. "
                "Please ingest more cryptography documents and try again."
            )

        context_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source", "unknown source")
            page = chunk.metadata.get("source_page")
            prefix = f"Source {idx}: {source}"
            if page:
                prefix += f" (page {page})"
            excerpt = chunk.text.strip()
            context_parts.append(f"{prefix}\n{excerpt}")

        context_text = "\n\n---\n\n".join(context_parts)
        system_prompt = (
            "You are a meticulous cryptography expert. "
            "Answer the user's question using ONLY the provided context. "
            "Cite the relevant sources inline using (Source X). "
            "If the context is insufficient, say so explicitly."
        )
        prompt = (
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            "Answer (use complete sentences and focus on cryptography theory):"
        )

        return self.ollama.generate(prompt=prompt, system=system_prompt)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_directories(self) -> None:
        Path(self.settings.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.settings.models_cache_directory).mkdir(parents=True, exist_ok=True)
        Path(self.settings.documents_directory).mkdir(parents=True, exist_ok=True)
        if self.settings.database_url.startswith("sqlite"):
            _, path = self.settings.database_url.split("sqlite:///", 1)
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    def _load_document_sections(
        self, document: ReferenceDocument
    ) -> tuple[list[dict], int]:
        if document.document_path.startswith(("http://", "https://")):
            payload = self._download_url(document.document_path)
            file_size = len(payload)
            buffer = io.BytesIO(payload)
            return self._parse_document_buffer(
                buffer, document.document_type, document.document_name
            ), file_size

        resolved_path = self._resolve_local_path(document.document_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"Document not found: {resolved_path}")

        if document.document_type == "pdf":
            with resolved_path.open("rb") as handle:
                buffer = io.BytesIO(handle.read())
                file_size = buffer.getbuffer().nbytes
                return self._parse_document_buffer(
                    buffer, document.document_type, document.document_name
                ), file_size

        with resolved_path.open("r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
        file_size = len(text.encode("utf-8"))
        sections = self._parse_text_document(
            text, document.document_type, document.document_name
        )
        return sections, file_size

    def _parse_document_buffer(
        self, buffer: io.BytesIO, doc_type: str, filename: str
    ) -> list[dict]:
        if doc_type != "pdf":
            text = buffer.getvalue().decode("utf-8", errors="ignore")
            return self._parse_text_document(text, doc_type, filename)

        reader = PdfReader(buffer)
        sections: list[dict] = []
        for idx, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            cleaned = self._clean_text(raw_text)
            if cleaned:
                sections.append({"page": idx, "text": cleaned})
        return sections

    def _parse_text_document(
        self, text: str, doc_type: str, filename: str
    ) -> list[dict]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []

        if doc_type == "md":
            html = markdown(cleaned)
            # Basic HTML to text conversion
            text_only = re.sub("<[^<]+?>", " ", html)
            text_only = self._clean_text(text_only)
        else:
            text_only = cleaned

        return [{"page": None, "text": text_only, "filename": filename}]

    def _chunk_sections(
        self, document: ReferenceDocument, sections: list[dict]
    ) -> list[dict]:
        chunks: list[dict] = []
        for section in sections:
            text = section.get("text") or ""
            if not text.strip():
                continue
            fragment_chunks = self.splitter.split_text(text)
            for chunk_text in fragment_chunks:
                normalized = self._clean_text(chunk_text)
                if len(normalized) < 48:
                    continue
                chunks.append(
                    {
                        "text": normalized,
                        "page": section.get("page"),
                    }
                )
        return chunks

    def _resolve_local_path(self, document_path: str) -> Path:
        path = Path(document_path)
        if path.is_absolute():
            return path
        return Path(self.settings.documents_directory) / path

    @staticmethod
    def _download_url(url: str) -> bytes:
        logger.debug("Downloading %s", url)
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.content

    @staticmethod
    def _clean_text(text: str) -> str:
        normalized = re.sub(r"\s+", " ", text)
        return normalized.strip()
