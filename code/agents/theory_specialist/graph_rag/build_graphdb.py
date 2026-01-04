#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import requests

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_ST_MODEL = "BAAI/bge-m3"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"
DEFAULT_VLLM_URL = "http://localhost:8000"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


def setup_logging(log_dir: Path, level: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"build_graphdb_{timestamp}.log"
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path),
    ]
    logging.basicConfig(level=log_level, format=LOG_FORMAT, handlers=handlers)
    logger = logging.getLogger("graph_rag")
    logger.info("Logging to %s", log_path)
    return logger


def find_documents(documents_dir: Path) -> List[Path]:
    exts = {".pdf", ".md", ".txt"}
    return sorted(
        [
            path
            for path in documents_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in exts
        ]
    )


def clean_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text)
    return normalized.strip()


def split_pdf_lines(text: str) -> List[str]:
    if not text:
        return []
    return [line.rstrip() for line in text.splitlines()]


def normalize_line_for_header(line: str) -> str:
    if not line:
        return ""
    lowered = line.strip().lower()
    lowered = re.sub(r"\d+", "", lowered)
    lowered = re.sub(r"[^\w\s]", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered.strip()


def is_noise_line(line: str) -> bool:
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
    if re.fullmatch(r"[-*]+", stripped):
        return True
    if re.fullmatch(r"[\W_]+", stripped):
        return True
    if re.search(r"\.{3,}", stripped):
        return True
    if re.fullmatch(
        r"(table of contents|contents|index|bibliography)",
        stripped,
        re.IGNORECASE,
    ):
        return True
    if re.search(r"\bcopyright\b|\ball rights reserved\b", stripped, re.IGNORECASE):
        return True
    return False


def should_merge_hyphen(previous: str, current: str) -> bool:
    return bool(re.match(r"^[A-Za-z]", current.strip()))


def merge_pdf_lines(lines: List[str]) -> str:
    merged: List[str] = []
    for line in lines:
        if not line:
            merged.append("")
            continue
        if merged:
            prev = merged[-1]
            if prev and prev.endswith("-") and should_merge_hyphen(prev, line):
                merged[-1] = prev[:-1] + line.lstrip()
                continue
        merged.append(line)
    text = "\n".join(merged)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    return text


def normalize_spacing(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"([.,;:])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=[0-9])", " ", text)
    text = re.sub(r"(?<=[0-9])(?=[A-Za-z])", " ", text)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    return text


def clean_pdf_sections(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not pages:
        return []

    page_lines: List[List[str]] = []
    line_counts: Dict[str, int] = {}
    for page in pages:
        lines = split_pdf_lines(page.get("text", ""))
        page_lines.append(lines)
        seen: set[str] = set()
        for line in lines:
            normalized = normalize_line_for_header(line)
            if not normalized:
                continue
            seen.add(normalized)
        for normalized in seen:
            line_counts[normalized] = line_counts.get(normalized, 0) + 1

    threshold = max(3, int(len(pages) * 0.4))
    repeated = {line for line, count in line_counts.items() if count >= threshold}

    sections: List[Dict[str, Any]] = []
    for page, lines in zip(pages, page_lines):
        filtered: List[str] = []
        for line in lines:
            normalized = normalize_line_for_header(line)
            if normalized and normalized in repeated:
                continue
            if is_noise_line(line):
                continue
            filtered.append(line.strip())

        text = merge_pdf_lines(filtered)
        text = normalize_spacing(text)
        cleaned = clean_text(text)
        if cleaned:
            sections.append({"page": page["page"], "text": cleaned})

    return sections


def read_pdf_sections(path: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    pages: List[Dict[str, Any]] = []
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None

    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(x_tolerance=1, y_tolerance=2) or ""
                    pages.append({"page": idx, "text": text})
        except Exception as exc:
            logger.warning("pdfplumber extraction failed for %s: %s", path.name, exc)
            pages = []

    if not pages:
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": idx, "text": text})
        except Exception as exc:
            logger.error("PyPDF2 extraction failed for %s: %s", path.name, exc)
            return []

    return clean_pdf_sections(pages)


def read_text_sections(path: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".md":
        try:
            from markdown import markdown

            html = markdown(raw)
            raw = re.sub(r"<[^<]+?>", " ", html)
        except Exception as exc:
            logger.warning("Markdown rendering failed for %s: %s", path.name, exc)
    cleaned = clean_text(raw)
    if not cleaned:
        return []
    return [{"page": None, "text": cleaned}]


def load_document_sections(path: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_sections(path, logger)
    return read_text_sections(path, logger)


def chunk_words(
    words: List[str], chunk_size: int, overlap: int
) -> Iterable[List[str]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    start = 0
    word_count = len(words)
    while start < word_count:
        end = min(word_count, start + chunk_size)
        yield words[start:end]
        if end >= word_count:
            break
        start = max(0, end - overlap)


def chunk_sections(
    sections: List[Dict[str, Any]],
    chunk_size: int,
    overlap: int,
    min_chunk_words: int,
) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    for section in sections:
        text = section.get("text") or ""
        words = text.split()
        if not words:
            continue
        for words_chunk in chunk_words(words, chunk_size, overlap):
            if len(words_chunk) < min_chunk_words:
                continue
            chunk_text = " ".join(words_chunk)
            chunks.append({"text": chunk_text, "page": section.get("page")})
    return chunks


def embed_with_fastembed(
    texts: List[str],
    model: str,
    batch_size: int,
    cache_dir: Optional[str],
    logger: logging.Logger,
) -> List[List[float]]:
    from fastembed import TextEmbedding

    embedder = TextEmbedding(model_name=model, cache_dir=cache_dir, threads=None)
    embeddings = list(embedder.embed(texts, batch_size=batch_size))
    logger.info("FastEmbed produced %d embeddings", len(embeddings))
    return [np.asarray(emb, dtype=float).tolist() for emb in embeddings]


def embed_with_sentence_transformers(
    texts: List[str],
    model: str,
    batch_size: int,
    device: str,
    logger: logging.Logger,
) -> List[List[float]]:
    from sentence_transformers import SentenceTransformer

    embedder = SentenceTransformer(model, device=device)
    embeddings = embedder.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    logger.info("SentenceTransformers produced %d embeddings", len(embeddings))
    return [np.asarray(emb, dtype=float).tolist() for emb in embeddings]


def embed_with_ollama(
    texts: List[str],
    model: str,
    ollama_url: str,
    timeout: int,
    logger: logging.Logger,
) -> List[List[float]]:
    url = ollama_url.rstrip("/") + "/api/embeddings"
    embeddings: List[List[float]] = []
    total = len(texts)
    for idx, text in enumerate(texts, start=1):
        payload = {"model": model, "prompt": text}
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if "embedding" in data:
            embedding = data["embedding"]
        elif "embeddings" in data and data["embeddings"]:
            embedding = data["embeddings"][0]
        else:
            raise ValueError("Unexpected Ollama embedding response format.")
        embeddings.append(embedding)
        if idx % 50 == 0 or idx == total:
            logger.info("Ollama embeddings %d/%d", idx, total)
    return embeddings


def embed_texts(
    texts: List[str],
    provider: str,
    model: str,
    batch_size: int,
    cache_dir: Optional[str],
    st_device: str,
    ollama_url: str,
    ollama_timeout: int,
    logger: logging.Logger,
) -> List[List[float]]:
    if provider == "fastembed":
        return embed_with_fastembed(texts, model, batch_size, cache_dir, logger)
    if provider == "sentence-transformers":
        return embed_with_sentence_transformers(
            texts, model, batch_size, st_device, logger
        )
    if provider == "ollama":
        return embed_with_ollama(texts, model, ollama_url, ollama_timeout, logger)
    raise ValueError(f"Unknown embedding provider: {provider}")


def normalize_entity_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).lower()


def normalize_entity_type(entity_type: str) -> str:
    return re.sub(r"\s+", " ", entity_type.strip()).lower()


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def extract_json_payload(text: str) -> Dict[str, Any]:
    cleaned = _strip_fences(text)
    candidates = [cleaned]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(cleaned[start : end + 1])

    for candidate in candidates:
        for attempt in range(2):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                candidate = _remove_trailing_commas(candidate)
                if attempt == 1:
                    break

    raise ValueError("Unable to parse JSON payload from LLM response.")


def build_extraction_messages(
    text: str, max_entities: int, max_relations: int
) -> List[Dict[str, str]]:
    system = (
        "You extract entities and relations for a knowledge graph. "
        "Return JSON only. No markdown, no commentary."
    )
    user = (
        "Extract high-value entities and relations from the text below.\n\n"
        f"Rules:\n"
        f"- Return JSON with keys: entities, relations.\n"
        f"- entities: list of {{name, type, description}}.\n"
        f"- relations: list of {{source, target, type, description, evidence}}.\n"
        f"- Use consistent, canonical entity names.\n"
        f"- Only include relations grounded in the text.\n"
        f"- Keep at most {max_entities} entities and {max_relations} relations.\n\n"
        "Text:\n"
        "<<<\n"
        f"{text}\n"
        ">>>"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_json_repair_messages(text: str) -> List[Dict[str, str]]:
    system = (
        "You repair invalid JSON. Output a valid JSON object only and nothing else."
    )
    user = (
        "Fix the JSON below. It must be a JSON object with keys "
        '"entities" and "relations". If unusable, return '
        '{"entities": [], "relations": []}.\n\n'
        "JSON:\n"
        "<<<\n"
        f"{text}\n"
        ">>>"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_vllm_chat(
    url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    endpoint = url.rstrip("/")
    if not endpoint.endswith("/v1/chat/completions"):
        endpoint = f"{endpoint}/v1/chat/completions"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    response = requests.post(endpoint, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_ollama_chat(
    url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    json_mode: bool,
) -> str:
    endpoint = url.rstrip("/")
    if not endpoint.endswith("/api/chat") and not endpoint.endswith("/api/generate"):
        endpoint = f"{endpoint}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "top_p": top_p, "num_predict": max_tokens},
    }
    if json_mode:
        payload["format"] = "json"
    response = requests.post(endpoint, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if "message" in data:
        return data["message"]["content"]
    if "response" in data:
        return data["response"]
    raise ValueError("Unexpected Ollama response payload.")


def call_llm_with_retries(
    provider: str,
    url: str,
    model: str,
    messages: List[Dict[str, str]],
    timeout: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    json_mode: bool,
    retries: int,
    logger: logging.Logger,
) -> str:
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            if provider == "vllm":
                return call_vllm_chat(
                    url, model, messages, timeout, temperature, top_p, max_tokens, json_mode
                )
            if provider == "ollama":
                return call_ollama_chat(
                    url, model, messages, timeout, temperature, top_p, max_tokens, json_mode
                )
            raise ValueError(f"Unknown LLM provider: {provider}")
        except Exception as exc:
            last_error = exc
            logger.warning(
                "LLM call failed (attempt %d/%d): %s",
                attempt + 1,
                retries + 1,
                exc,
            )
            time.sleep(2)
    raise RuntimeError(f"LLM call failed after retries: {last_error}")


def extract_entities_relations(
    text: str,
    provider: str,
    url: str,
    model: str,
    timeout: int,
    temperature: float,
    top_p: float,
    max_tokens: int,
    json_mode: bool,
    retries: int,
    max_entities: int,
    max_relations: int,
    max_chars: int,
    json_repair: bool,
    json_repair_max_chars: int,
    logger: logging.Logger,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    clipped = text[:max_chars]
    messages = build_extraction_messages(clipped, max_entities, max_relations)
    response = call_llm_with_retries(
        provider=provider,
        url=url,
        model=model,
        messages=messages,
        timeout=timeout,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        json_mode=json_mode,
        retries=retries,
        logger=logger,
    )
    try:
        payload = extract_json_payload(response)
    except Exception as exc:
        logger.warning("Invalid JSON from LLM (%s).", exc)
        if not json_repair:
            return [], []
        repair_text = response[:json_repair_max_chars]
        repair_messages = build_json_repair_messages(repair_text)
        repair_response = call_llm_with_retries(
            provider=provider,
            url=url,
            model=model,
            messages=repair_messages,
            timeout=timeout,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            json_mode=True,
            retries=retries,
            logger=logger,
        )
        try:
            payload = extract_json_payload(repair_response)
        except Exception as repair_exc:
            logger.warning("JSON repair failed (%s).", repair_exc)
            return [], []
    entities = payload.get("entities", []) if isinstance(payload, dict) else []
    relations = payload.get("relations", []) if isinstance(payload, dict) else []
    if not isinstance(entities, list):
        entities = []
    if not isinstance(relations, list):
        relations = []
    return entities, relations


def coerce_confidence(value: Any, default: float = 0.7) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ensure_entity(
    entity_index: Dict[str, int],
    entities: Dict[int, Dict[str, Any]],
    name: str,
    entity_type: str,
    description: str,
) -> int:
    normalized_name = normalize_entity_name(name)
    normalized_type = normalize_entity_type(entity_type or "unknown")
    key = f"{normalized_name}::{normalized_type}"
    if key in entity_index:
        entity_id = entity_index[key]
        if description and not entities[entity_id]["description"]:
            entities[entity_id]["description"] = description
        return entity_id
    entity_id = len(entities) + 1
    entities[entity_id] = {
        "id": entity_id,
        "name": name.strip(),
        "type": entity_type.strip() or "Unknown",
        "description": description.strip(),
    }
    entity_index[key] = entity_id
    return entity_id


def resolve_entity_id(
    entity_index: Dict[str, int],
    entities: Dict[int, Dict[str, Any]],
    name: str,
    entity_type: str,
    description: str,
) -> int:
    normalized_name = normalize_entity_name(name)
    for key, entity_id in entity_index.items():
        if key.startswith(f"{normalized_name}::"):
            if description and not entities[entity_id]["description"]:
                entities[entity_id]["description"] = description
            return entity_id
    return ensure_entity(entity_index, entities, name, entity_type, description)


def build_community_messages(
    entities: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    entity_lines = [
        f"- {entity['name']} ({entity['type']}): {entity['description']}".strip()
        for entity in entities
    ]
    relation_lines = [
        (
            f"- {rel['source']} --{rel['type']}--> {rel['target']}: "
            f"{rel['description']}"
        ).strip()
        for rel in relations
    ]
    system = (
        "You summarize a knowledge graph community for retrieval. "
        "Be precise and grounded in the provided entities and relations."
    )
    user = (
        "Summarize this community in 4-6 concise sentences.\n\n"
        "Entities:\n"
        + "\n".join(entity_lines)
        + "\n\nRelations:\n"
        + "\n".join(relation_lines)
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_entity_communities(
    entity_ids: List[int],
    relations: List[Tuple[Any, ...]],
    min_size: int,
    logger: logging.Logger,
) -> List[List[int]]:
    try:
        import networkx as nx
    except Exception as exc:
        logger.warning("NetworkX not available, skipping communities: %s", exc)
        return []

    graph = nx.Graph()
    graph.add_nodes_from(entity_ids)
    for relation in relations:
        source_id = int(relation[0])
        target_id = int(relation[1])
        graph.add_edge(source_id, target_id)

    if graph.number_of_edges() == 0:
        return []

    communities = list(nx.algorithms.community.greedy_modularity_communities(graph))
    filtered = [sorted(list(group)) for group in communities if len(group) >= min_size]
    logger.info("Detected %d communities", len(filtered))
    return filtered

def init_graph_db(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.executescript(
        """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT UNIQUE,
            source_path TEXT,
            source_name TEXT,
            page INTEGER,
            chunk_index INTEGER,
            text TEXT,
            token_count INTEGER
        );
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY,
            source_id INTEGER,
            target_id INTEGER,
            score REAL,
            edge_type TEXT,
            FOREIGN KEY(source_id) REFERENCES nodes(id),
            FOREIGN KEY(target_id) REFERENCES nodes(id)
        );
        CREATE INDEX IF NOT EXISTS edges_source_idx ON edges(source_id);
        CREATE INDEX IF NOT EXISTS edges_target_idx ON edges(target_id);
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY,
            name TEXT,
            entity_type TEXT,
            description TEXT
        );
        CREATE UNIQUE INDEX IF NOT EXISTS entities_name_type_idx
            ON entities(name, entity_type);
        CREATE TABLE IF NOT EXISTS chunk_entities (
            chunk_node_id INTEGER,
            entity_id INTEGER,
            confidence REAL,
            evidence TEXT,
            PRIMARY KEY (chunk_node_id, entity_id),
            FOREIGN KEY(chunk_node_id) REFERENCES nodes(id),
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        );
        CREATE INDEX IF NOT EXISTS chunk_entities_entity_idx
            ON chunk_entities(entity_id);
        CREATE TABLE IF NOT EXISTS entity_relations (
            id INTEGER PRIMARY KEY,
            source_entity_id INTEGER,
            target_entity_id INTEGER,
            relation_type TEXT,
            description TEXT,
            confidence REAL,
            evidence TEXT,
            chunk_node_id INTEGER,
            FOREIGN KEY(source_entity_id) REFERENCES entities(id),
            FOREIGN KEY(target_entity_id) REFERENCES entities(id),
            FOREIGN KEY(chunk_node_id) REFERENCES nodes(id)
        );
        CREATE INDEX IF NOT EXISTS entity_relations_source_idx
            ON entity_relations(source_entity_id);
        CREATE INDEX IF NOT EXISTS entity_relations_target_idx
            ON entity_relations(target_entity_id);
        CREATE TABLE IF NOT EXISTS communities (
            id INTEGER PRIMARY KEY,
            entity_ids TEXT,
            summary TEXT
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )
    connection.commit()
    return connection


def store_nodes(connection: sqlite3.Connection, nodes: List[Tuple[Any, ...]]) -> None:
    connection.executemany(
        """
        INSERT INTO nodes (
            id, chunk_id, source_path, source_name, page, chunk_index, text, token_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        nodes,
    )
    connection.commit()


def store_edges(connection: sqlite3.Connection, edges: List[Tuple[Any, ...]]) -> None:
    if not edges:
        return
    connection.executemany(
        """
        INSERT INTO edges (source_id, target_id, score, edge_type)
        VALUES (?, ?, ?, ?);
        """,
        edges,
    )
    connection.commit()


def store_entities(
    connection: sqlite3.Connection, entities: List[Tuple[Any, ...]]
) -> None:
    if not entities:
        return
    connection.executemany(
        """
        INSERT INTO entities (id, name, entity_type, description)
        VALUES (?, ?, ?, ?);
        """,
        entities,
    )
    connection.commit()


def store_chunk_entities(
    connection: sqlite3.Connection, links: List[Tuple[Any, ...]]
) -> None:
    if not links:
        return
    connection.executemany(
        """
        INSERT OR REPLACE INTO chunk_entities (
            chunk_node_id, entity_id, confidence, evidence
        )
        VALUES (?, ?, ?, ?);
        """,
        links,
    )
    connection.commit()


def store_entity_relations(
    connection: sqlite3.Connection, relations: List[Tuple[Any, ...]]
) -> None:
    if not relations:
        return
    connection.executemany(
        """
        INSERT INTO entity_relations (
            source_entity_id,
            target_entity_id,
            relation_type,
            description,
            confidence,
            evidence,
            chunk_node_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        relations,
    )
    connection.commit()


def store_communities(
    connection: sqlite3.Connection, communities: List[Tuple[Any, ...]]
) -> None:
    if not communities:
        return
    connection.executemany(
        """
        INSERT INTO communities (id, entity_ids, summary)
        VALUES (?, ?, ?);
        """,
        communities,
    )
    connection.commit()


def store_meta(connection: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    items = [(key, json.dumps(value)) for key, value in payload.items()]
    connection.executemany(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?);", items
    )
    connection.commit()


def build_similarity_edges(
    embeddings: np.ndarray,
    top_k: int,
    min_similarity: float,
    logger: logging.Logger,
) -> List[Tuple[int, int, float, str]]:
    if embeddings.size == 0:
        return []
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1e-12
    normalized = embeddings / norms
    total = normalized.shape[0]
    edges: List[Tuple[int, int, float, str]] = []
    for idx in range(total):
        sims = np.dot(normalized, normalized[idx])
        sims[idx] = -1.0
        k = min(top_k, total - 1)
        if k <= 0:
            continue
        candidates = np.argpartition(-sims, k)[:k]
        candidates = candidates[np.argsort(-sims[candidates])]
        for target in candidates:
            score = float(sims[target])
            if score < min_similarity:
                continue
            edges.append((idx + 1, int(target) + 1, score, "similarity"))
        if (idx + 1) % 200 == 0 or idx + 1 == total:
            logger.info("Similarity edges %d/%d", idx + 1, total)
    return edges


def build_vector_db(
    output_dir: Path,
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    documents: List[str],
    logger: logging.Logger,
) -> None:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    chroma_path = output_dir / "chroma"
    client = chromadb.PersistentClient(
        path=str(chroma_path), settings=ChromaSettings(anonymized_telemetry=False)
    )
    collection = client.get_or_create_collection(
        name=collection_name, metadata={"hnsw:space": "cosine"}
    )
    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )
    logger.info("Vector DB written to %s", chroma_path)


def prepare_output_dir(output_dir: Path, overwrite: bool) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output dir {output_dir} exists and is not empty. Use --overwrite to clear it."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a local GraphRAG graph DB + vector DB from documents."
    )
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "documents",
        help="Directory containing PDF/MD/TXT documents.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="Output directory for graph.db and vector DB.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "logs",
        help="Directory for log files.",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level.")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="Chunk size in words.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap in words.",
    )
    parser.add_argument(
        "--min-chunk-words",
        type=int,
        default=80,
        help="Minimum words per chunk.",
    )
    parser.add_argument(
        "--embedding-provider",
        choices=["fastembed", "sentence-transformers", "ollama"],
        default="fastembed",
        help="Embedding backend to use.",
    )
    parser.add_argument(
        "--embedding-model",
        default=DEFAULT_FASTEMBED_MODEL,
        help="Embedding model name.",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=64,
        help="Batch size for embedding.",
    )
    parser.add_argument(
        "--fastembed-cache-dir",
        default=None,
        help="Optional cache dir for FastEmbed model files.",
    )
    parser.add_argument(
        "--st-device",
        default="cuda",
        help="Device for sentence-transformers (e.g., cuda, cpu).",
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help="Ollama base URL.",
    )
    parser.add_argument(
        "--ollama-model",
        default=DEFAULT_OLLAMA_EMBED_MODEL,
        help="Ollama embedding model name.",
    )
    parser.add_argument(
        "--ollama-timeout",
        type=int,
        default=90,
        help="Timeout (seconds) for Ollama embedding requests.",
    )
    parser.add_argument(
        "--enable-kg",
        action="store_true",
        help="Enable LLM-based entity and relation extraction.",
    )
    parser.add_argument(
        "--llm-provider",
        choices=["vllm", "ollama"],
        default="vllm",
        help="LLM provider for entity/relation extraction.",
    )
    parser.add_argument(
        "--llm-url",
        default=DEFAULT_VLLM_URL,
        help="Base URL for the local LLM server.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_LLM_MODEL,
        help="LLM model name for extraction and summaries.",
    )
    parser.add_argument(
        "--llm-timeout",
        type=int,
        default=120,
        help="Timeout (seconds) for LLM requests.",
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.0,
        help="LLM sampling temperature.",
    )
    parser.add_argument(
        "--llm-top-p",
        type=float,
        default=0.9,
        help="LLM top-p sampling.",
    )
    parser.add_argument(
        "--llm-max-tokens",
        type=int,
        default=800,
        help="Max tokens to generate per LLM call.",
    )
    parser.add_argument(
        "--llm-retries",
        type=int,
        default=2,
        help="Retries for LLM calls.",
    )
    parser.add_argument(
        "--llm-max-chars",
        type=int,
        default=4000,
        help="Max characters from each chunk sent to the LLM.",
    )
    parser.add_argument(
        "--llm-json-repair",
        action="store_true",
        default=True,
        help="Attempt JSON repair with the LLM on parse failures.",
    )
    parser.add_argument(
        "--no-llm-json-repair",
        action="store_false",
        dest="llm_json_repair",
        help="Disable JSON repair fallback.",
    )
    parser.add_argument(
        "--llm-json-repair-max-chars",
        type=int,
        default=8000,
        help="Max characters of the bad JSON sent to the repair prompt.",
    )
    parser.add_argument(
        "--max-entities-per-chunk",
        type=int,
        default=12,
        help="Entity cap per chunk for extraction.",
    )
    parser.add_argument(
        "--max-relations-per-chunk",
        type=int,
        default=20,
        help="Relation cap per chunk for extraction.",
    )
    parser.add_argument(
        "--llm-max-chunks",
        type=int,
        default=0,
        help="Limit number of chunks for LLM extraction (0 = no limit).",
    )
    parser.add_argument(
        "--llm-json-mode",
        action="store_true",
        default=True,
        help="Request JSON-mode output when supported.",
    )
    parser.add_argument(
        "--no-llm-json-mode",
        action="store_false",
        dest="llm_json_mode",
        help="Disable JSON-mode output.",
    )
    parser.add_argument(
        "--enable-communities",
        action="store_true",
        help="Detect communities from entity relations.",
    )
    parser.add_argument(
        "--community-min-size",
        type=int,
        default=3,
        help="Minimum entity count per community.",
    )
    parser.add_argument(
        "--community-max-entities",
        type=int,
        default=40,
        help="Max entities to include in a community summary prompt.",
    )
    parser.add_argument(
        "--community-max-relations",
        type=int,
        default=80,
        help="Max relations to include in a community summary prompt.",
    )
    parser.add_argument(
        "--community-summaries",
        action="store_true",
        help="Generate LLM summaries for communities.",
    )
    parser.add_argument(
        "--collection-name",
        default="graph_rag_chunks",
        help="Chroma collection name.",
    )
    parser.add_argument(
        "--no-vector-db",
        action="store_true",
        help="Skip creation of Chroma vector DB.",
    )
    parser.add_argument(
        "--no-similarity-edges",
        action="store_true",
        help="Skip similarity edges (sequence edges only).",
    )
    parser.add_argument(
        "--graph-top-k",
        type=int,
        default=8,
        help="Top-k similar edges per node.",
    )
    parser.add_argument(
        "--graph-min-similarity",
        type=float,
        default=0.45,
        help="Minimum cosine similarity for graph edges.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Clear output directory before writing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logger = setup_logging(args.log_dir, args.log_level)

    documents_dir = args.documents_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents dir not found: {documents_dir}")

    prepare_output_dir(output_dir, args.overwrite)

    documents = find_documents(documents_dir)
    if not documents:
        logger.warning("No documents found in %s", documents_dir)
        return

    logger.info("Found %d documents", len(documents))

    chunks: List[Dict[str, Any]] = []
    doc_node_ids: List[List[int]] = []

    for doc_index, path in enumerate(documents, start=1):
        start_time = time.time()
        sections = load_document_sections(path, logger)
        if not sections:
            logger.warning("No text extracted from %s", path.name)
            continue
        doc_chunks = chunk_sections(
            sections, args.chunk_size, args.chunk_overlap, args.min_chunk_words
        )
        if not doc_chunks:
            logger.warning("No chunks produced for %s", path.name)
            continue

        rel_path = str(path.relative_to(documents_dir))
        node_ids: List[int] = []
        for chunk_index, chunk in enumerate(doc_chunks):
            node_id = len(chunks) + 1
            chunk_id = f"{doc_index}_{chunk_index}"
            chunk_text = chunk["text"]
            chunks.append(
                {
                    "id": node_id,
                    "chunk_id": chunk_id,
                    "source_path": rel_path,
                    "source_name": path.name,
                    "page": chunk.get("page"),
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "token_count": len(chunk_text.split()),
                }
            )
            node_ids.append(node_id)
        doc_node_ids.append(node_ids)

        elapsed = time.time() - start_time
        logger.info(
            "Processed %s: %d chunks in %.2fs",
            path.name,
            len(doc_chunks),
            elapsed,
        )

    if not chunks:
        logger.warning("No chunks generated across all documents.")
        return

    texts = [chunk["text"] for chunk in chunks]
    embedding_model = args.embedding_model
    if args.embedding_provider == "ollama":
        embedding_model = args.ollama_model
    elif (
        args.embedding_provider == "sentence-transformers"
        and args.embedding_model == DEFAULT_FASTEMBED_MODEL
    ):
        embedding_model = DEFAULT_ST_MODEL
    embeddings = embed_texts(
        texts,
        provider=args.embedding_provider,
        model=embedding_model,
        batch_size=args.embedding_batch_size,
        cache_dir=args.fastembed_cache_dir,
        st_device=args.st_device,
        ollama_url=args.ollama_url,
        ollama_timeout=args.ollama_timeout,
        logger=logger,
    )

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count.")

    entities: Dict[int, Dict[str, Any]] = {}
    entity_index: Dict[str, int] = {}
    chunk_entity_links: List[Tuple[Any, ...]] = []
    entity_relations: List[Tuple[Any, ...]] = []
    community_rows: List[Tuple[Any, ...]] = []

    if args.enable_kg:
        logger.info(
            "Extracting entities/relations with %s (%s)",
            args.llm_provider,
            args.llm_model,
        )
        max_chunks = len(chunks)
        if args.llm_max_chunks > 0:
            max_chunks = min(max_chunks, args.llm_max_chunks)
        for idx, chunk in enumerate(chunks[:max_chunks], start=1):
            entities_data, relations_data = extract_entities_relations(
                text=chunk["text"],
                provider=args.llm_provider,
                url=args.llm_url,
                model=args.llm_model,
                timeout=args.llm_timeout,
                temperature=args.llm_temperature,
                top_p=args.llm_top_p,
                max_tokens=args.llm_max_tokens,
                json_mode=args.llm_json_mode,
                retries=args.llm_retries,
                max_entities=args.max_entities_per_chunk,
                max_relations=args.max_relations_per_chunk,
                max_chars=args.llm_max_chars,
                json_repair=args.llm_json_repair,
                json_repair_max_chars=args.llm_json_repair_max_chars,
                logger=logger,
            )

            for entity in entities_data:
                if not isinstance(entity, dict):
                    continue
                name = str(entity.get("name", "")).strip()
                if not name:
                    continue
                entity_type = str(entity.get("type", "")).strip() or "Unknown"
                description = str(entity.get("description", "")).strip()
                evidence = str(entity.get("evidence", "")).strip()
                confidence = coerce_confidence(entity.get("confidence"))
                entity_id = ensure_entity(
                    entity_index, entities, name, entity_type, description
                )
                chunk_entity_links.append(
                    (
                        chunk["id"],
                        entity_id,
                        confidence,
                        evidence or None,
                    )
                )

            for relation in relations_data:
                if not isinstance(relation, dict):
                    continue
                source_name = str(relation.get("source", "")).strip()
                target_name = str(relation.get("target", "")).strip()
                if not source_name or not target_name:
                    continue
                relation_type = str(relation.get("type", "")).strip() or "related_to"
                description = str(relation.get("description", "")).strip()
                evidence = str(relation.get("evidence", "")).strip()
                confidence = coerce_confidence(relation.get("confidence"))
                source_id = resolve_entity_id(
                    entity_index,
                    entities,
                    source_name,
                    "Unknown",
                    "",
                )
                target_id = resolve_entity_id(
                    entity_index,
                    entities,
                    target_name,
                    "Unknown",
                    "",
                )
                entity_relations.append(
                    (
                        source_id,
                        target_id,
                        relation_type,
                        description,
                        confidence,
                        evidence or None,
                        chunk["id"],
                    )
                )

            if idx % 25 == 0 or idx == max_chunks:
                logger.info("LLM extraction %d/%d", idx, max_chunks)

        if args.enable_communities:
            community_groups = build_entity_communities(
                list(entities.keys()),
                entity_relations,
                args.community_min_size,
                logger,
            )
            if community_groups and args.community_summaries:
                for community_id, entity_ids in enumerate(community_groups, start=1):
                    selected_entities = [
                        entities[entity_id]
                        for entity_id in entity_ids[: args.community_max_entities]
                        if entity_id in entities
                    ]
                    entity_set = set(entity_ids)
                    selected_relations = [
                        {
                            "source": entities.get(rel[0], {}).get("name", ""),
                            "target": entities.get(rel[1], {}).get("name", ""),
                            "type": rel[2],
                            "description": rel[3],
                        }
                        for rel in entity_relations
                        if rel[0] in entity_set and rel[1] in entity_set
                    ][: args.community_max_relations]

                    messages = build_community_messages(
                        selected_entities, selected_relations
                    )
                    summary = call_llm_with_retries(
                        provider=args.llm_provider,
                        url=args.llm_url,
                        model=args.llm_model,
                        messages=messages,
                        timeout=args.llm_timeout,
                        temperature=args.llm_temperature,
                        top_p=args.llm_top_p,
                        max_tokens=args.llm_max_tokens,
                        json_mode=False,
                        retries=args.llm_retries,
                        logger=logger,
                    ).strip()
                    community_rows.append(
                        (
                            community_id,
                            json.dumps(entity_ids),
                            summary,
                        )
                    )
            elif community_groups:
                for community_id, entity_ids in enumerate(community_groups, start=1):
                    community_rows.append(
                        (community_id, json.dumps(entity_ids), None)
                    )

    if not args.no_vector_db:
        metadatas = [
            {
                "source": chunk["source_name"],
                "source_page": chunk["page"],
                "source_path": chunk["source_path"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]
        ids = [chunk["chunk_id"] for chunk in chunks]
        build_vector_db(
            output_dir,
            args.collection_name,
            ids,
            embeddings,
            metadatas,
            texts,
            logger,
        )

    graph_db_path = output_dir / "graph.db"
    connection = init_graph_db(graph_db_path)
    nodes_payload = [
        (
            chunk["id"],
            chunk["chunk_id"],
            chunk["source_path"],
            chunk["source_name"],
            chunk["page"],
            chunk["chunk_index"],
            chunk["text"],
            chunk["token_count"],
        )
        for chunk in chunks
    ]
    store_nodes(connection, nodes_payload)

    if args.enable_kg:
        entity_rows = [
            (
                entity["id"],
                entity["name"],
                entity["type"],
                entity["description"],
            )
            for entity in entities.values()
        ]
        store_entities(connection, entity_rows)
        store_chunk_entities(connection, chunk_entity_links)
        store_entity_relations(connection, entity_relations)
        store_communities(connection, community_rows)

    sequence_edges: List[Tuple[int, int, float, str]] = []
    for node_ids in doc_node_ids:
        for idx in range(len(node_ids) - 1):
            source = node_ids[idx]
            target = node_ids[idx + 1]
            sequence_edges.append((source, target, 1.0, "sequence"))
            sequence_edges.append((target, source, 1.0, "sequence"))
    store_edges(connection, sequence_edges)
    logger.info("Inserted %d sequence edges", len(sequence_edges))

    similarity_edges: List[Tuple[int, int, float, str]] = []
    if not args.no_similarity_edges:
        embedding_array = np.asarray(embeddings, dtype=np.float32)
        similarity_edges = build_similarity_edges(
            embedding_array,
            top_k=args.graph_top_k,
            min_similarity=args.graph_min_similarity,
            logger=logger,
        )
        store_edges(connection, similarity_edges)
        logger.info("Inserted %d similarity edges", len(similarity_edges))

    meta_payload = {
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
        "documents_dir": str(documents_dir),
        "output_dir": str(output_dir),
        "embedding_provider": args.embedding_provider,
        "embedding_model": embedding_model,
        "kg_enabled": args.enable_kg,
        "llm_provider": args.llm_provider if args.enable_kg else None,
        "llm_model": args.llm_model if args.enable_kg else None,
        "chunk_size_words": args.chunk_size,
        "chunk_overlap_words": args.chunk_overlap,
        "min_chunk_words": args.min_chunk_words,
        "total_documents": len(documents),
        "total_chunks": len(chunks),
        "sequence_edges": len(sequence_edges),
        "similarity_edges": len(similarity_edges),
        "total_entities": len(entities) if args.enable_kg else 0,
        "total_entity_relations": len(entity_relations) if args.enable_kg else 0,
        "total_communities": len(community_rows) if args.enable_kg else 0,
        "collection_name": None if args.no_vector_db else args.collection_name,
    }
    store_meta(connection, meta_payload)
    connection.close()

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    logger.info("Graph DB written to %s", graph_db_path)
    logger.info("Manifest written to %s", manifest_path)


if __name__ == "__main__":
    main()
