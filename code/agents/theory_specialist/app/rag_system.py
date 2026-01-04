"""
RAG system implementation: document ingestion, retrieval, and generation.
"""

from __future__ import annotations

import datetime as dt
import difflib
import io
import json
import logging
import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from urllib.parse import urlparse

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
from .database import SessionLocal
from .lexical_index import LexicalDocument, LexicalIndex, LexicalResult
from .llm_client import build_llm_client
from .models import DocumentChunk, ReferenceDocument
from .reranker import OnnxCrossEncoder
from .web_search import SearchResult, WebSearchManager

logger = logging.getLogger(__name__)

DEFAULT_DOMAIN_TERMS = {
    "rsa",
    "aes",
    "des",
    "3des",
    "ecc",
    "ecdsa",
    "ecdh",
    "diffie-hellman",
    "dh",
    "hmac",
    "hash",
    "signature",
    "cipher",
    "encryption",
    "decryption",
    "public",
    "private",
    "symmetric",
    "asymmetric",
    "key",
    "modulus",
    "prime",
    "factorization",
    "discrete",
    "logarithm",
    "padding",
    "oaep",
    "pkcs",
    "tls",
    "ssl",
    "nonce",
    "iv",
}

COMMON_CORRECTIONS = {
    "pilons": "pillars",
    "encript": "encrypt",
    "encryptiong": "encryption",
    "decript": "decrypt",
    "chiper": "cipher",
    "cypher": "cipher",
    "symetric": "symmetric",
    "asymetric": "asymmetric",
}

STOPWORDS = {
    "what",
    "is",
    "are",
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "for",
    "with",
    "on",
    "by",
    "about",
    "explain",
    "define",
    "describe",
    "give",
    "me",
    "does",
    "do",
    "it",
    "as",
    "that",
}

GENERIC_QUERY_TERMS = {
    "properties",
    "property",
    "summary",
    "summarize",
    "main",
    "overview",
    "explain",
    "define",
    "definition",
    "basics",
    "introduction",
    "cryptography",
    "algorithm",
    "scheme",
    "system",
    "protocol",
    "method",
    "technique",
}

DEFINITION_TRIGGERS = (
    "what is",
    "what are",
    "define",
    "definition of",
    "summarize",
    "main properties",
    "overview",
    "explain",
    "describe",
)

DEFINITION_KEYWORDS = (
    "algorithm",
    "scheme",
    "cryptosystem",
    "cipher",
    "standard",
    "public-key",
    "symmetric",
    "asymmetric",
    "block cipher",
    "stream cipher",
    "signature",
    "encryption",
    "decryption",
    "key exchange",
    "hash",
    "message authentication",
    "mac",
)

NOISE_PATTERNS = [
    re.compile(r"\btable of contents\b", re.IGNORECASE),
    re.compile(r"\bindex\b", re.IGNORECASE),
    re.compile(r"\bchapter\b", re.IGNORECASE),
    re.compile(r"\bsection\b", re.IGNORECASE),
    re.compile(r"\bISBN\b", re.IGNORECASE),
    re.compile(r"\bpublisher\b", re.IGNORECASE),
    re.compile(r"\bcopyright\b", re.IGNORECASE),
]

REFERENCE_SECTION_RE = re.compile(
    r"\n(?:references?|sources?)\s*:.*",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    similarity: float


@dataclass
class QueryContext:
    original_query: str
    normalized_query: str
    query_for_retrieval: str
    corrections: List[str]


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

        self.llm = build_llm_client(self.settings)

        self._domain_terms = self._load_domain_terms()
        self._lexical_lock = threading.Lock()
        self.lexical_index = LexicalIndex([])
        self._cache_lock = threading.Lock()
        self._query_embedding_cache: OrderedDict[str, List[float]] = OrderedDict()
        self._web_search_manager: Optional[WebSearchManager] = None
        self._build_lexical_index()

        logger.info(
            "RAG system initialized with embedding=%s, reranker=%s",
            self.settings.embedding_model_name,
            self.settings.reranker_model_name,
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
                    embedding_vector=json.dumps(
                        np.asarray(embedding, dtype=float).tolist()
                    ),
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
        self.refresh_lexical_index()
        return len(ids)

    def refresh_lexical_index(self) -> None:
        if not self.settings.enable_lexical_retrieval:
            return
        self._build_lexical_index()

    # ------------------------------------------------------------------ #
    # Retrieval & generation
    # ------------------------------------------------------------------ #
    def prepare_query(self, query: str) -> QueryContext:
        normalized = " ".join(query.split())
        corrections: List[str] = []
        query_for_retrieval = normalized

        if self.settings.query_correction_enabled and normalized:
            tokens = LexicalIndex.tokenize(normalized)
            corrected_tokens: List[str] = []
            for token in tokens:
                if token in COMMON_CORRECTIONS:
                    corrected = COMMON_CORRECTIONS[token]
                    corrections.append(f"{token} -> {corrected}")
                    corrected_tokens.append(corrected)
                    continue
                if (
                    token in self._domain_terms
                    or len(token) < 4
                    or any(char.isdigit() for char in token)
                ):
                    corrected_tokens.append(token)
                    continue
                matches = difflib.get_close_matches(
                    token,
                    self._domain_terms,
                    n=1,
                    cutoff=self.settings.query_correction_cutoff,
                )
                if matches:
                    corrected_tokens.append(matches[0])
                    corrections.append(f"{token} -> {matches[0]}")
                else:
                    corrected_tokens.append(token)

            if corrections:
                query_for_retrieval = " ".join(corrected_tokens)

        return QueryContext(
            original_query=query,
            normalized_query=normalized,
            query_for_retrieval=query_for_retrieval,
            corrections=corrections,
        )

    def retrieve(
        self, query: str, top_k: Optional[int] = None
    ) -> Tuple[List[RetrievedChunk], str]:
        top_k = top_k or self.settings.retrieval_top_k
        query_vector = self._get_query_embedding(query)

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
            vector_score = 1.0 - float(distance)
            metadata["vector_score"] = vector_score
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=document or metadata.get("text", ""),
                    metadata=metadata,
                    similarity=vector_score,
                )
            )

        if not self.settings.enable_lexical_retrieval:
            return retrieved, "vector"

        lexical_results = self.lexical_index.search(query, self.settings.lexical_top_k)
        if not lexical_results:
            return retrieved, "vector"

        max_lex_score = max((result.score for result in lexical_results), default=0.0)
        lex_score_map = {
            result.chunk_id: (result, result.score / max_lex_score if max_lex_score else 0.0)
            for result in lexical_results
        }

        merged: dict[str, RetrievedChunk] = {chunk.chunk_id: chunk for chunk in retrieved}
        for chunk_id, (result, norm_score) in lex_score_map.items():
            if chunk_id in merged:
                merged[chunk_id].metadata["lexical_score"] = norm_score
                continue
            merged[chunk_id] = RetrievedChunk(
                chunk_id=result.chunk_id,
                text=result.text,
                metadata=dict(result.metadata),
                similarity=0.0,
            )
            merged[chunk_id].metadata["lexical_score"] = norm_score

        combined: list[Tuple[RetrievedChunk, float]] = []
        for chunk in merged.values():
            vector_score = float(chunk.metadata.get("vector_score", 0.0))
            lexical_score = float(chunk.metadata.get("lexical_score", 0.0))
            combined_score = (
                self.settings.vector_weight * vector_score
                + self.settings.lexical_weight * lexical_score
            )
            chunk.metadata["combined_score"] = combined_score
            combined.append((chunk, combined_score))

        combined.sort(key=lambda item: item[1], reverse=True)
        merged_chunks = [chunk for chunk, _ in combined[:top_k]]
        return merged_chunks, "hybrid"

    def retrieve_with_fallback(
        self,
        query: str,
        top_k: Optional[int] = None,
        session: Optional[Session] = None,
    ) -> Tuple[List[RetrievedChunk], str]:
        top_k = top_k or self.settings.retrieval_top_k
        retrieved, method = self.retrieve(query, top_k)

        if not self._should_use_web_search(query, retrieved):
            return retrieved, method

        logger.info("Web search fallback triggered for query: '%s'", query)
        try:
            manager = self._get_web_search_manager()
            web_results = manager.search(
                query=query,
                max_results=self.settings.web_search_top_k,
                session=session,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Web search failed: %s", exc)
            return retrieved, method

        if not web_results:
            return retrieved, method

        web_chunks = self._convert_web_results_to_chunks(web_results)
        merged = self._merge_local_and_web_results(
            local_chunks=retrieved,
            web_chunks=web_chunks,
            top_k=top_k,
        )
        return merged, f"{method}+web"

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
        if reranked:
            return [chunk for chunk, _ in reranked[: self.settings.reranker_top_k]]
        return chunk_list[: self.settings.reranker_top_k]

    def _get_web_search_manager(self) -> WebSearchManager:
        if self._web_search_manager is None or self._web_search_manager.settings is not self.settings:
            self._web_search_manager = WebSearchManager(self.settings)
        return self._web_search_manager

    def _should_use_web_search(
        self,
        query: str,
        retrieved: List[RetrievedChunk],
    ) -> bool:
        if not self.settings.enable_web_search:
            return False

        if self._is_out_of_domain(query):
            return True

        if not retrieved:
            return True

        top_score = self._fallback_score(retrieved[0])
        if top_score < self.settings.web_search_fallback_threshold:
            return True

        if self._is_definition_query(query):
            if not self._has_definition_evidence(query, retrieved):
                return True

        return False

    def _is_out_of_domain(self, query: str) -> bool:
        tokens = LexicalIndex.tokenize(query)
        if not tokens:
            return False
        for token in tokens:
            if token in self._domain_terms:
                return False
        lowered = query.lower()
        if "crypto" in lowered:
            return False
        return True

    def _fallback_score(self, chunk: RetrievedChunk) -> float:
        return float(
            chunk.metadata.get(
                "combined_score",
                chunk.metadata.get("vector_score", chunk.similarity),
            )
        )

    def _convert_web_results_to_chunks(
        self,
        web_results: List[SearchResult],
    ) -> List[RetrievedChunk]:
        chunks: List[RetrievedChunk] = []
        min_score = self.settings.web_search_min_relevance_score

        for result in web_results:
            if min_score > 0 and result.score < min_score:
                continue
            text = f"{result.title}\n\n{result.snippet}".strip()
            if not text:
                continue
            chunk_id = f"web_{hash(result.url)}"
            metadata = {
                "source": result.url,
                "source_type": "web",
                "web_title": result.title,
                "web_provider": result.source,
                "web_score": result.score,
                "is_web_result": True,
            }
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=text,
                    metadata=metadata,
                    similarity=result.score,
                )
            )
        return chunks

    def _merge_local_and_web_results(
        self,
        local_chunks: List[RetrievedChunk],
        web_chunks: List[RetrievedChunk],
        top_k: int,
    ) -> List[RetrievedChunk]:
        if not local_chunks:
            return web_chunks[:top_k]
        if not web_chunks:
            return local_chunks[:top_k]

        local_count = max(1, int(top_k * 0.6))
        web_count = max(1, top_k - local_count)

        top_local = local_chunks[:local_count]
        top_web = sorted(web_chunks, key=lambda c: c.similarity, reverse=True)[:web_count]
        merged = top_local + top_web
        return merged[:top_k]

    def generate_answer(self, query: str, chunks: List[RetrievedChunk]) -> str:
        if self.settings.answer_style == "extractive":
            extractive = self._build_extractive_answer(query, chunks)
            if extractive:
                return extractive

        selected = self._select_context_chunks(chunks)
        if not selected:
            if self.settings.allow_general_knowledge:
                return self._generate_general_answer(query)
            return (
                "I do not have enough relevant context to answer this question yet. "
                "Please ingest more cryptography documents and try again."
            )

        allow_general = self.settings.allow_general_knowledge
        if self._is_definition_query(query):
            if not self._has_definition_evidence(query, selected) and allow_general:
                return self._generate_general_answer(query)
            allow_general = False

        return self._generate_abstractive_answer(query, selected, allow_general)

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

    def validate_document_path(self, document_path: str) -> None:
        if document_path.startswith(("http://", "https://")):
            if not self.settings.allow_remote_ingest:
                raise ValueError("Remote ingestion is disabled.")
            parsed = urlparse(document_path)
            host = (parsed.hostname or "").lower()
            allowed_hosts = {
                item.strip().lower()
                for item in self.settings.allowed_remote_hosts.split(",")
                if item.strip()
            }
            if allowed_hosts and host not in allowed_hosts:
                raise ValueError(f"Remote host not allowed: {host}")
            return

        self._resolve_local_path(document_path)

    def _load_document_sections(
        self, document: ReferenceDocument
    ) -> tuple[list[dict], int]:
        if document.document_path.startswith(("http://", "https://")):
            if not self.settings.allow_remote_ingest:
                raise ValueError("Remote ingestion is disabled.")
            parsed = urlparse(document.document_path)
            host = (parsed.hostname or "").lower()
            allowed_hosts = {
                item.strip().lower()
                for item in self.settings.allowed_remote_hosts.split(",")
                if item.strip()
            }
            if allowed_hosts and host not in allowed_hosts:
                raise ValueError(f"Remote host not allowed: {host}")

            payload = self._download_url(document.document_path)
            file_size = len(payload)
            buffer = io.BytesIO(payload)
            return self._parse_document_buffer(
                buffer, document.document_type, document.document_name
            ), file_size

        resolved_path = self._resolve_local_path(document.document_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"Document not found: {resolved_path}")
        file_size = resolved_path.stat().st_size
        if file_size > self.settings.max_document_bytes:
            raise ValueError(
                f"Document exceeds size limit of {self.settings.max_document_bytes} bytes."
            )

        if document.document_type == "pdf":
            with resolved_path.open("rb") as handle:
                buffer = io.BytesIO(handle.read())
                return self._parse_document_buffer(
                    buffer, document.document_type, document.document_name
                ), file_size

        with resolved_path.open("r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
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

        return self._parse_pdf_buffer(buffer, filename)

    def _parse_pdf_buffer(self, buffer: io.BytesIO, filename: str) -> list[dict]:
        buffer.seek(0)
        sections: list[dict] = []
        if self.settings.pdf_use_pdfplumber:
            try:
                import pdfplumber
            except ImportError:
                pdfplumber = None

            if pdfplumber is not None:
                try:
                    sections = self._extract_pdf_with_pdfplumber(buffer)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning(
                        "pdfplumber extraction failed for %s: %s", filename, exc
                    )

        if not sections:
            buffer.seek(0)
            sections = self._extract_pdf_with_pypdf(buffer)
        return sections

    def _extract_pdf_with_pdfplumber(self, buffer: io.BytesIO) -> list[dict]:
        import pdfplumber

        buffer.seek(0)
        pages: list[dict] = []
        with pdfplumber.open(buffer) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text(x_tolerance=1, y_tolerance=2) or ""
                pages.append({"page": idx, "text": text})
        return self._clean_pdf_sections(pages)

    def _extract_pdf_with_pypdf(self, buffer: io.BytesIO) -> list[dict]:
        buffer.seek(0)
        reader = PdfReader(buffer)
        pages: list[dict] = []
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": idx, "text": text})
        return self._clean_pdf_sections(pages)

    def _clean_pdf_sections(self, pages: list[dict]) -> list[dict]:
        if not pages:
            return []

        page_lines: list[list[str]] = []
        line_counts: dict[str, int] = {}
        for page in pages:
            lines = self._split_pdf_lines(page.get("text", ""))
            page_lines.append(lines)
            seen: set[str] = set()
            for line in lines:
                normalized = self._normalize_line_for_header(line)
                if not normalized:
                    continue
                seen.add(normalized)
            for normalized in seen:
                line_counts[normalized] = line_counts.get(normalized, 0) + 1

        threshold = max(3, int(len(pages) * 0.4))
        repeated = {line for line, count in line_counts.items() if count >= threshold}

        sections: list[dict] = []
        for page, lines in zip(pages, page_lines):
            filtered: list[str] = []
            for line in lines:
                normalized = self._normalize_line_for_header(line)
                if normalized and normalized in repeated:
                    continue
                if self._is_noise_line(line):
                    continue
                filtered.append(line.strip())

            text = self._merge_pdf_lines(filtered)
            text = self._normalize_spacing(text)
            cleaned = self._clean_text(text)
            if cleaned:
                sections.append({"page": page["page"], "text": cleaned})

        return sections

    @staticmethod
    def _split_pdf_lines(text: str) -> list[str]:
        if not text:
            return []
        return [line.rstrip() for line in text.splitlines()]

    @staticmethod
    def _normalize_line_for_header(line: str) -> str:
        if not line:
            return ""
        lowered = line.strip().lower()
        lowered = re.sub(r"\d+", "", lowered)
        lowered = re.sub(r"[^\w\s]", "", lowered)
        lowered = re.sub(r"\s+", " ", lowered)
        return lowered.strip()

    @staticmethod
    def _is_noise_line(line: str) -> bool:
        if not line:
            return False
        stripped = line.strip()
        if not stripped:
            return False
        if len(stripped) <= 2:
            return True
        if re.fullmatch(r"\d+", stripped):
            return True
        if re.fullmatch(r"[ivxlcdm]+", stripped, re.IGNORECASE):
            return True
        if re.fullmatch(r"[•·▪■]+", stripped):
            return True
        if re.fullmatch(r"[\W_]+", stripped):
            return True
        if re.search(r"\.{3,}", stripped):
            return True
        if re.fullmatch(r"(table of contents|contents|index|bibliography)", stripped, re.IGNORECASE):
            return True
        if re.search(r"\bcopyright\b|\ball rights reserved\b", stripped, re.IGNORECASE):
            return True
        return False

    def _merge_pdf_lines(self, lines: list[str]) -> str:
        merged: list[str] = []
        for line in lines:
            if not line:
                merged.append("")
                continue
            if merged:
                prev = merged[-1]
                if prev and prev.endswith("-") and self._should_merge_hyphen(prev, line):
                    merged[-1] = prev[:-1] + line.lstrip()
                    continue
            merged.append(line)
        text = "\n".join(merged)
        text = re.sub(r"\n{2,}", "\n\n", text)
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        return text

    @staticmethod
    def _should_merge_hyphen(previous: str, current: str) -> bool:
        return bool(re.match(r"^[A-Za-z]", current.strip()))

    @staticmethod
    def _normalize_spacing(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
        text = re.sub(r"([.,;:])(?=[A-Za-z])", r"\1 ", text)
        text = re.sub(r"(?<=[A-Za-z])(?=[0-9])", " ", text)
        text = re.sub(r"(?<=[0-9])(?=[A-Za-z])", " ", text)
        text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
        return text

    def _parse_text_document(
        self, text: str, doc_type: str, filename: str
    ) -> list[dict]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []

        if doc_type == "md":
            html = markdown(cleaned)
            text_only = re.sub("<[^<]+?>", " ", html)
            text_only = self._clean_text(text_only)
        else:
            text_only = cleaned

        return [{"page": None, "text": text_only, "filename": filename}]

    def _chunk_sections(
        self, document: ReferenceDocument, sections: list[dict]
    ) -> list[dict]:
        """Split document sections into chunks."""
        chunks: list[dict] = []
        min_length = self.settings.min_chunk_length

        for section in sections:
            text = section.get("text") or ""
            if not text.strip():
                continue
            fragment_chunks = self.splitter.split_text(text)
            for chunk_text in fragment_chunks:
                normalized = self._clean_text(chunk_text)
                if len(normalized) < min_length:
                    continue
                chunks.append(
                    {
                        "text": normalized,
                        "page": section.get("page"),
                    }
                )
        return chunks

    def _resolve_local_path(self, document_path: str) -> Path:
        base_dir = Path(self.settings.documents_directory).resolve()
        path = Path(document_path)
        resolved = path.resolve() if path.is_absolute() else (base_dir / path).resolve()
        if not resolved.is_relative_to(base_dir):
            raise ValueError("Document path must be under the documents directory.")
        return resolved

    def _download_url(self, url: str) -> bytes:
        logger.debug("Downloading %s", url)
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        content = bytearray()
        max_bytes = self.settings.max_document_bytes
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if not chunk:
                continue
            content.extend(chunk)
            if len(content) > max_bytes:
                raise ValueError(
                    f"Remote document exceeds size limit of {max_bytes} bytes."
                )
        return bytes(content)

    @staticmethod
    def _clean_text(text: str) -> str:
        normalized = re.sub(r"\s+", " ", text)
        return normalized.strip()

    def _build_lexical_index(self) -> None:
        """Build lexical index with batching to prevent memory issues."""
        if not self.settings.enable_lexical_retrieval:
            return

        batch_size = self.settings.lexical_index_batch_size
        documents = []
        offset = 0

        try:
            while True:
                with SessionLocal() as session:
                    # Query chunks in batches
                    chunks = (
                        session.query(DocumentChunk)
                        .order_by(DocumentChunk.id)
                        .limit(batch_size)
                        .offset(offset)
                        .all()
                    )

                    if not chunks:
                        break  # No more chunks to process

                    for chunk in chunks:
                        chunk_id = f"{chunk.reference_doc_id}_{chunk.chunk_index}"
                        metadata = {
                            "source": chunk.source_title,
                            "source_page": chunk.source_page,
                        }
                        documents.append(
                            LexicalDocument(
                                chunk_id=chunk_id,
                                text=chunk.chunk_text,
                                metadata=metadata,
                                tokens=LexicalIndex.tokenize(chunk.chunk_text),
                            )
                        )

                    # If we got fewer than batch_size, we're done
                    if len(chunks) < batch_size:
                        break

                    offset += batch_size

        except (OSError, IOError) as exc:
            logger.warning("Lexical index build skipped due to I/O error: %s", exc)
            with self._lexical_lock:
                self.lexical_index = LexicalIndex([])
            return
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Lexical index build skipped: %s", exc)
            with self._lexical_lock:
                self.lexical_index = LexicalIndex([])
            return

        with self._lexical_lock:
            self.lexical_index = LexicalIndex(documents)
        logger.info("Lexical index built with %d documents", len(documents))

    def _load_domain_terms(self) -> set[str]:
        terms = set(DEFAULT_DOMAIN_TERMS)
        if self.settings.domain_terms_path:
            path = Path(self.settings.domain_terms_path)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    cleaned = line.strip().lower()
                    if cleaned:
                        terms.add(cleaned)
        return {term.lower() for term in terms if term}

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get query embedding with LRU cache support."""
        # Check cache if enabled
        if self.settings.query_cache_size > 0:
            with self._cache_lock:
                cached = self._query_embedding_cache.get(query)
                if cached is not None:
                    self._query_embedding_cache.move_to_end(query)
                    return cached

        # Generate embedding
        embedding = next(iter(self.embedding_model.embed([query], batch_size=1)))
        vector = np.asarray(embedding, dtype=float).tolist()

        # Cache if enabled
        if self.settings.query_cache_size > 0:
            with self._cache_lock:
                # Check cache size again in case it changed at runtime
                # Clear old entries if cache size was reduced
                while len(self._query_embedding_cache) >= self.settings.query_cache_size:
                    self._query_embedding_cache.popitem(last=False)
                self._query_embedding_cache[query] = vector
        return vector

    def _select_context_chunks(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        if not chunks:
            return []
        ranked = sorted(
            chunks,
            key=lambda c: float(c.metadata.get("reranker_score", c.similarity)),
            reverse=True,
        )
        filtered = [
            chunk
            for chunk in ranked
            if float(chunk.metadata.get("reranker_score", chunk.similarity))
            >= self.settings.min_source_score
        ]
        if len(filtered) < self.settings.min_cited_sources:
            filtered = ranked[: max(self.settings.min_cited_sources, 1)]
        return filtered[: self.settings.reranker_top_k]

    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        context_parts: list[str] = []
        total_chars = 0
        max_context_chars = (
            self.settings.max_context_chars
            if self.settings.max_context_chars > 0
            else None
        )
        max_chunk_chars = (
            self.settings.max_chunk_chars if self.settings.max_chunk_chars > 0 else None
        )

        for idx, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source", "unknown source")
            page = chunk.metadata.get("source_page")
            prefix = f"Source {idx}: {source}"
            if page:
                prefix += f" (page {page})"

            excerpt = chunk.text.strip()
            if max_chunk_chars and len(excerpt) > max_chunk_chars:
                excerpt = excerpt[:max_chunk_chars].rstrip() + "..."

            payload = f"{prefix}\n{excerpt}"
            if max_context_chars and total_chars + len(payload) > max_context_chars:
                break
            total_chars += len(payload)
            context_parts.append(payload)

        return "\n\n---\n\n".join(context_parts)

    def _generate_abstractive_answer(
        self, query: str, chunks: List[RetrievedChunk], allow_general: bool
    ) -> str:
        context_text = self._build_context(chunks)
        require_citations = self.settings.require_citations

        system_prompt = (
            "You are a cryptography expert. Write a clear, accurate answer in your own words. "
            "Do not quote or copy section headings. Avoid markdown headings or bullet lists unless the question asks for them."
        )
        if require_citations:
            system_prompt += (
                " Cite claims that are supported by the context using (Source X). "
                f"Use only Source 1 through Source {len(chunks)}."
            )
        if allow_general:
            system_prompt += (
                " If the context is missing some details, fill gaps using your own knowledge, "
                "but do not invent citations for those parts."
            )
        else:
            system_prompt += " Use only the provided context; if insufficient, say so."

        prompt = (
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )

        options = {
            "temperature": self.settings.generation_temperature,
            "top_p": self.settings.generation_top_p,
            "top_k": self.settings.generation_top_k,
            "max_tokens": self.settings.generation_max_tokens,
        }
        answer = self.llm.generate(prompt=prompt, system=system_prompt, options=options)
        answer = self._sanitize_answer(answer, len(chunks))
        answer = self._maybe_continue_answer(
            answer=answer,
            query=query,
            context_text=context_text,
            system_prompt=system_prompt,
            options=options,
            max_source_id=len(chunks),
        )
        answer = self._retry_full_answer(
            answer=answer,
            query=query,
            context_text=context_text,
            system_prompt=system_prompt,
            options=options,
            max_source_id=len(chunks),
        )

        if require_citations and "(Source" not in answer and chunks:
            options["temperature"] = 0.1
            system_prompt = (
                system_prompt
                + " Ensure at least one citation like (Source 1) appears in the answer."
            )
            answer = self.llm.generate(
                prompt=prompt, system=system_prompt, options=options
            )
            answer = self._sanitize_answer(answer, len(chunks))
            answer = self._maybe_continue_answer(
                answer=answer,
                query=query,
                context_text=context_text,
                system_prompt=system_prompt,
                options=options,
                max_source_id=len(chunks),
            )
            answer = self._retry_full_answer(
                answer=answer,
                query=query,
                context_text=context_text,
                system_prompt=system_prompt,
                options=options,
                max_source_id=len(chunks),
            )

        return answer

    def _generate_general_answer(self, query: str) -> str:
        system_prompt = (
            "You are a cryptography expert. Answer the question clearly and accurately "
            "using your own knowledge. Avoid bullet lists unless the question asks for them."
        )
        prompt = f"Question: {query}\nAnswer:"
        options = {
            "temperature": self.settings.generation_temperature,
            "top_p": self.settings.generation_top_p,
            "top_k": self.settings.generation_top_k,
            "max_tokens": self.settings.generation_max_tokens,
        }
        return self.llm.generate(prompt=prompt, system=system_prompt, options=options)

    def _maybe_continue_answer(
        self,
        answer: str,
        query: str,
        context_text: str,
        system_prompt: str,
        options: dict,
        max_source_id: int,
    ) -> str:
        if not answer:
            return answer
        if self.settings.continuation_max_attempts < 1:
            return answer
        if answer.startswith("I do not have enough relevant context"):
            return answer
        if not self._needs_continuation(answer):
            return answer

        continuation_prompt = (
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            f"Answer so far:\n{answer}\n\n"
            "Continue the answer in the same style. "
            "Do not repeat earlier sentences. "
            "Finish the thought if the last sentence is incomplete."
        )
        continuation_options = dict(options)
        continuation_options["max_tokens"] = self.settings.continuation_max_tokens

        combined = answer
        for _ in range(self.settings.continuation_max_attempts):
            continuation = self.llm.generate(
                prompt=continuation_prompt,
                system=system_prompt,
                options=continuation_options,
            )
            continuation = self._strip_continuation_prefix(continuation)
            if not continuation:
                break
            combined = f"{combined} {continuation}".strip()
            combined = self._sanitize_answer(combined, max_source_id)
            if not self._needs_continuation(combined):
                break
            continuation_prompt = (
                f"Context:\n{context_text}\n\n"
                f"Question: {query}\n\n"
                f"Answer so far:\n{combined}\n\n"
                "Continue the answer in the same style. "
                "Do not repeat earlier sentences. "
                "Finish the thought if the last sentence is incomplete."
            )

        return combined

    def _retry_full_answer(
        self,
        answer: str,
        query: str,
        context_text: str,
        system_prompt: str,
        options: dict,
        max_source_id: int,
    ) -> str:
        if not answer:
            return answer
        if not self._needs_continuation(answer):
            return answer

        retry_prompt = (
            f"Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            "Write a complete answer in full sentences. "
            "Do not stop mid-sentence."
        )
        retry_options = dict(options)
        retry_options["temperature"] = min(0.2, retry_options.get("temperature", 0.2))
        retry_options["max_tokens"] = max(
            retry_options.get("max_tokens", 0),
            self.settings.generation_max_tokens + self.settings.continuation_max_tokens,
        )
        regenerated = self.llm.generate(
            prompt=retry_prompt,
            system=system_prompt,
            options=retry_options,
        )
        regenerated = self._sanitize_answer(regenerated, max_source_id)
        if regenerated and not self._needs_continuation(regenerated):
            return regenerated
        return answer

    def _needs_continuation(self, answer: str) -> bool:
        stripped = answer.strip()
        min_length = self.settings.min_answer_length_for_continuation
        if len(stripped) < min_length:
            return False
        if stripped.endswith(("...", "…")):
            return True
        if stripped[-1] in ".?!\"”’)":
            return False
        return True

    @staticmethod
    def _strip_continuation_prefix(text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(
            r"^(?:Answer|Continuation|Continue|Sure|Certainly|Of course)[:\\-\\s]+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return cleaned.strip()

    def _build_extractive_answer(self, query: str, chunks: List[RetrievedChunk]) -> str:
        if not chunks:
            return ""
        query_tokens = [
            token
            for token in LexicalIndex.tokenize(query)
            if token and token not in STOPWORDS
        ]
        if not query_tokens:
            query_tokens = LexicalIndex.tokenize(query)

        source_map = {chunk.chunk_id: idx + 1 for idx, chunk in enumerate(chunks)}
        candidates: list[tuple[float, str, int]] = []
        for chunk in chunks:
            source_id = source_map.get(chunk.chunk_id, 0)
            sentences = self._split_sentences(chunk.text)
            for sentence in sentences:
                if len(sentence) < 30:
                    continue
                if self._sentence_is_noisy(sentence):
                    continue
                tokens = [t for t in LexicalIndex.tokenize(sentence) if t not in STOPWORDS]
                if not tokens:
                    continue
                overlap = len(set(tokens) & set(query_tokens))
                if overlap == 0:
                    continue
                score = overlap / max(len(set(query_tokens)), 1)
                candidates.append((score, sentence.strip(), source_id))

        if not candidates:
            return ""
        candidates.sort(key=lambda item: item[0], reverse=True)
        selected = []
        used = set()
        for _, sentence, source_id in candidates[: self.settings.extractive_max_sentences]:
            if sentence in used:
                continue
            used.add(sentence)
            selected.append(f"- {sentence} (Source {source_id})")

        return "\n".join(selected)

    def _is_definition_query(self, query: str) -> bool:
        lowered = query.strip().lower()
        return any(trigger in lowered for trigger in DEFINITION_TRIGGERS)

    def _has_definition_evidence(
        self, query: str, chunks: List[RetrievedChunk]
    ) -> bool:
        tokens = [
            token
            for token in LexicalIndex.tokenize(query)
            if token and token not in STOPWORDS
        ]
        if not tokens:
            return False
        focus = [token for token in tokens if token not in GENERIC_QUERY_TERMS]
        if not focus:
            focus = tokens

        for chunk in chunks:
            for sentence in self._split_sentences(chunk.text):
                if self._sentence_is_noisy(sentence):
                    continue
                lowered = sentence.lower()
                for term in focus:
                    if term not in lowered:
                        continue
                    if self._sentence_is_definition(sentence, term):
                        return True
        return False

    @staticmethod
    def _sentence_is_definition(sentence: str, term: str) -> bool:
        lowered = sentence.lower()
        if term not in lowered:
            return False
        if "stands for" in lowered or "refers to" in lowered:
            return True
        if re.search(rf"\\b{re.escape(term)}\\b\\s+is\\b", lowered):
            return True
        if re.search(
            rf"\\b{re.escape(term)}\\b.*\\b({'|'.join(DEFINITION_KEYWORDS)})\\b",
            lowered,
        ):
            return True
        return False

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        normalized = re.sub(r"\s+", " ", text.strip())
        if not normalized:
            return []
        parts = re.split(r"(?<=[.!?])\s+", normalized)
        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _sentence_is_noisy(sentence: str) -> bool:
        if any(pattern.search(sentence) for pattern in NOISE_PATTERNS):
            return True
        alpha_ratio = sum(char.isalpha() for char in sentence) / max(len(sentence), 1)
        if alpha_ratio < 0.5:
            return True
        return False

    @staticmethod
    def _sanitize_answer(answer: str, max_source_id: int) -> str:
        cleaned = answer.strip()
        match = REFERENCE_SECTION_RE.search(cleaned)
        if match:
            cleaned = cleaned[: match.start()].rstrip()

        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        filtered: list[str] = []
        invalid_source_pattern = re.compile(r"\bSource\s+(\d+)\b", re.IGNORECASE)
        for sentence in sentences:
            if not sentence.strip():
                continue
            def _replace_invalid_source(match: re.Match) -> str:
                try:
                    if int(match.group(1)) > max_source_id:
                        return ""
                except ValueError:
                    return match.group(0)
                return match.group(0)

            normalized = invalid_source_pattern.sub(_replace_invalid_source, sentence)
            normalized = re.sub(r"\s{2,}", " ", normalized).strip()
            if not normalized:
                continue
            filtered.append(normalized)

        return " ".join(filtered).strip()
