# Cryptography RAG System

A fully local Retrieval-Augmented Generation stack specialized for cryptography theory. The system ingests PDF/Markdown/Text material, stores semantic representations in an embedded ChromaDB instance, and serves high-quality answers via a FastAPI backend.

## ✨ Key Features
- **Automatic background ingestion** of queued documents with APScheduler.
- **FastEmbed embeddings** (`BAAI/bge-small-en-v1.5`) + **ONNX reranking** (`BAAI/bge-reranker-base`) for higher answer accuracy (CPU-only, no PyTorch dependency).
- **Optional hybrid retrieval** (vector + lexical BM25) to improve recall on short queries.
- **Persistent storage** using SQLite (metadata/conversations) and ChromaDB (vector store).
- **Conversation history** with message-level context tracking.
- **Local generation** through Ollama (Phi-3 defaults, configurable).
- **Multiple LLM providers** (Ollama local/cloud, OpenAI, Gemini) via environment config.
- **Containerized deployment** with Docker Compose.

## 📦 Requirements
- Docker 24+
- Docker Compose 2.20+
- Local CPU with ≥8GB RAM (recommended)
- Ollama installed **on the host machine** with models stored locally (`https://ollama.com`)

## 🚀 Quick Start
1. Create the required directories:
   ```bash
   mkdir -p data documents models
   ```
2. Drop cryptography PDFs/MD/TXT files into `documents/`.
3. Build and start the stack:
   ```bash
   docker compose up --build -d
   ```
   Docker Compose exposes the API at `http://localhost:8100` (container port 8000).
4. Ensure the host-side Ollama daemon is running, then pull models from the host (not the container):
   ```bash
   ollama pull phi3
   ```
   Repeat for any alternative models you configure in `.env`.
5. Verify the API is up:
   ```bash
   curl http://localhost:8100/health
   ```

## 🔌 API Endpoints
- `POST /ingest`
  ```json
  {
    "document_path": "/app/documents/rsa_theory.pdf",
    "document_type": "pdf"
  }
  ```
  Queues a document for background ingestion.

- `GET /status`
  Returns ingestion metrics and queue status.

- `POST /generate`
  ```json
  {
    "query": "Explain the RSA algorithm",
    "conversation_id": null
  }
  ```
  Generates an answer with cited sources. Omit `conversation_id` to create a new session.

- `POST /provider`
  ```json
  {
    "provider": "ollama-cloud",
    "ollama_model": "deepseek-v3.2:cloud",
    "ollama_api_key": "..."
  }
  ```
  Updates the active LLM provider at runtime (ollama, ollama-cloud, gemini, openai).
  Examples:
  ```bash
  # Local Ollama (docker service)
  curl -sS http://localhost:8100/provider -H 'Content-Type: application/json' -d '{
    "provider": "ollama",
    "ollama_url": "http://ollama:11434",
    "ollama_model": "phi3"
  }'

  # Ollama Cloud
  curl -sS http://localhost:8100/provider -H 'Content-Type: application/json' -d '{
    "provider": "ollama-cloud",
    "ollama_model": "gpt-oss:120b-cloud",
    "ollama_api_key": "..."
  }'

  # Gemini
  curl -sS http://localhost:8100/provider -H 'Content-Type: application/json' -d '{
    "provider": "gemini",
    "gemini_model": "gemini-3-pro-preview",
    "gemini_api_key": "..."
  }'
  ```

- `GET /conversations/{conversation_id}`
  Fetch full conversation history.

- `GET /health`
  System heartbeat with model and storage diagnostics.

## 🧠 How It Works
1. `/ingest` inserts document metadata into SQLite (`reference_documents`).
2. APScheduler polls every 5 seconds, loading the next pending document.
3. Documents are chunked (~300 characters, 50 overlap), embedded with `BAAI/bge-small-en-v1.5` via FastEmbed, and stored in ChromaDB.
4. `/generate` embeds the query with the same model, retrieves vector + lexical (BM25) candidates when enabled, reranks with an ONNX `BAAI/bge-reranker-base` cross-encoder, and sends curated context to the selected LLM for answer generation.
5. Conversations and message metadata are persisted for traceability.

## ⚙️ Configuration
Environment variables can override defaults (see `app/config.py`):
- `DATABASE_URL` (default: `sqlite:////app/data/rag_system.db`)
- `CHROMA_PERSIST_DIRECTORY`
- `DOCUMENTS_DIRECTORY`
- `MODELS_CACHE_DIRECTORY`
- `EMBEDDING_MODEL_NAME`
- `EMBEDDING_BATCH_SIZE`
- `RERANKER_MODEL_NAME`
- `OLLAMA_URL` (default: `http://127.0.0.1:11434`; use `http://host.docker.internal:11434` in Docker)
- `OLLAMA_MODEL`
- `OLLAMA_API_KEY` (only needed for Ollama Cloud)
- `OLLAMA_USE_CHAT` (default true; uses `/api/chat`)
- `LLM_PROVIDER` (`ollama`, `ollama-cloud`, `openai`, or `gemini`)
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`
- `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_BASE_URL`
- `INGESTION_INTERVAL_SECONDS`
- `INGESTION_BATCH_SIZE`

## 🧪 Development
Run lint/checks locally:
```bash
python -m compileall app
```

To run the API without Docker (assumes dependencies installed):
```bash
uvicorn app.main:app --reload --port 8000
```

## 📄 License
Internal project for cryptography research assistance.
