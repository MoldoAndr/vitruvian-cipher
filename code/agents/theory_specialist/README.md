# Cryptography RAG System

A fully local Retrieval-Augmented Generation stack specialized for cryptography theory. The system ingests PDF/Markdown/Text material, stores semantic representations in an embedded ChromaDB instance, and serves high-quality answers via a FastAPI backend.

## ✨ Key Features
- **Automatic background ingestion** of queued documents with APScheduler.
- **SentenceTransformer embeddings** + **cross-encoder reranking** for higher answer accuracy.
- **FastEmbed + ONNX models** for lightweight CPU-only embeddings and reranking (no PyTorch dependency).
- **Persistent storage** using SQLite (metadata/conversations) and ChromaDB (vector store).
- **Conversation history** with message-level context tracking.
- **Local generation** through Ollama (Phi-3 defaults, configurable).
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
4. Ensure the host-side Ollama daemon is running, then pull models from the host (not the container):
   ```bash
   ollama pull phi3
   ```
   Repeat for any alternative models you configure in `.env`.
5. Verify the API is up:
   ```bash
   curl http://localhost:8000/health
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

- `GET /conversations/{conversation_id}`
  Fetch full conversation history.

- `GET /health`
  System heartbeat with model and storage diagnostics.

## 🧠 How It Works
1. `/ingest` inserts document metadata into SQLite (`reference_documents`).
2. APScheduler polls every 5 seconds, loading the next pending document.
3. Documents are chunked (300 tokens, 50 overlap), embedded with `all-MiniLM-L6-v2`, and stored in ChromaDB.
4. `/generate` embeds the query with `BAAI/bge-small-en-v1.5`, retrieves top-10 chunks, reranks with an ONNX `BAAI/bge-reranker-base` cross-encoder, and sends curated context to Ollama for answer generation.
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
- `OLLAMA_URL` (default points to the host gateway `http://host.docker.internal:11434`)
- `OLLAMA_MODEL`
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
