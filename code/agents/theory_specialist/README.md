# Cryptography RAG System

A fully local Retrieval-Augmented Generation stack specialized for cryptography theory. The system ingests PDF/Markdown/Text material, stores semantic representations in an embedded ChromaDB instance, and serves high-quality answers via a FastAPI backend.

## Table of Contents
- [Key Features](#key-features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Testing](#testing)
- [Development](#development)

## Key Features
- **Automatic document discovery** - Scan the documents folder and automatically ingest new files
- **Automatic background ingestion** of queued documents with APScheduler
- **FastEmbed embeddings** (`BAAI/bge-small-en-v1.5`) + **ONNX reranking** (`BAAI/bge-reranker-base`) for higher answer accuracy (CPU-only, no PyTorch dependency)
- **Optional hybrid retrieval** (vector + lexical BM25) to improve recall on short queries
- **Persistent storage** using SQLite (metadata/conversations) and ChromaDB (vector store)
- **Conversation history** with message-level context tracking
- **Local generation** through Ollama (Phi-3 defaults, configurable)
- **Multiple LLM providers** (Ollama local/cloud, OpenAI, Gemini) via `/provider` endpoint or per-request override
- **Dynamic provider switching** without restarting the RAG system (embeddings and reranker remain unchanged)
- **Runtime configuration** for ingestion workers and parallel processing
- **Containerized deployment** with Docker Compose

## Requirements
- Docker 24+
- Docker Compose 2.20+
- Local CPU with >=8GB RAM (recommended)
- Ollama installed **on the host machine** with models stored locally (`https://ollama.com`)

## Quick Start
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

## API Endpoints

### GET /health
System heartbeat with model and storage diagnostics.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "embedding_model": "BAAI/bge-small-en-v1.5",
  "generation_model": "phi3",
  "vector_db_chunks": 15234,
  "timestamp": "2025-01-15T10:30:00.000000Z"
}
```

---

### POST /ingest
Queue a specific document for background ingestion.

**Request:**
```json
{
  "document_path": "/app/documents/rsa_theory.pdf",
  "document_type": "pdf"
}
```

**Supported document types:** `pdf`, `md`, `txt`

**Document path options:**
- Absolute path: `/app/documents/rsa_theory.pdf`
- Relative path: `rsa_theory.pdf` (relative to documents directory)
- URL: `https://example.com/document.pdf` (if `ALLOW_REMOTE_INGEST=true`)

**Response:**
```json
{
  "status": "queued",
  "message": "Document added to processing queue: /app/documents/rsa_theory.pdf",
  "next_status_check": "/status"
}
```

**Expected Behavior:**
- The document is added to the ingestion queue
- Background processor will pick it up within 5 seconds (configurable via `INGESTION_INTERVAL_SECONDS`)
- Processing status can be monitored via `/status`
- If the document is already queued, returns a 400 error

---

### POST /auto-ingest
Automatically discover and queue all documents in the documents folder that are not yet in the database.

**Request:** No body required

**Response:**
```json
{
  "status": "queued",
  "discovered_count": 5,
  "queued_count": 5,
  "message": "Discovered 5 new documents and queued 5 for ingestion.",
  "next_status_check": "/status"
}
```

**Expected Behavior:**
- Scans the documents directory recursively for PDF, MD, and TXT files
- Compares found files against the database (by document path)
- Queues only documents that are not already in the database
- Returns count of discovered and queued documents
- Background processing begins immediately via the aggregator

---

### GET /status
Returns ingestion metrics and queue status.

**Response:**
```json
{
  "total_reference_documents": 10,
  "processed_documents": 8,
  "in_progress_documents": 1,
  "pending_documents": 1,
  "total_chunks_in_vector_db": 15234,
  "currently_processing": "cryptography_basics.pdf",
  "timestamp": "2025-01-15T10:30:00.000000Z"
}
```

**Processing Status Codes:**
- `0` = Pending
- `1` = In Progress
- `2` = Processed

---

### POST /generate
Generate an answer using the RAG system with retrieved and reranked context.

**Request:**
```json
{
  "query": "Explain the RSA algorithm and its key components",
  "conversation_id": null
}
```

**Optional Parameters (Provider Override):**
```json
{
  "query": "Explain the RSA algorithm",
  "conversation_id": null,
  "provider": "openai",
  "openai_model": "gpt-4o-mini"
}
```

**Provider Options:**
- `ollama` - Local Ollama instance (default)
- `ollama-cloud` - Ollama Cloud API
- `openai` - OpenAI API
- `gemini` - Google Gemini API

**Optional model parameters:**
- `ollama_url` - Ollama server URL
- `ollama_model` - Ollama model name
- `openai_model` - OpenAI model name
- `gemini_model` - Gemini model name

**Response:**
```json
{
  "answer": "RSA (Rivest-Shamir-Adleman) is an asymmetric cryptographic algorithm...",
  "sources": [
    {
      "chunk_id": "5_12",
      "relevance_score": 0.92,
      "preview": "RSA is based on the practical difficulty of factoring the product...",
      "metadata": {
        "source": "crypto_basics.pdf",
        "source_page": 45,
        "reranker_score": 0.92,
        "vector_score": 0.75
      }
    }
  ],
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message_id": 123
}
```

**Expected Behavior:**
- If `conversation_id` is `null` or omitted, creates a new conversation
- Query is embedded and top-k chunks are retrieved from vector store
- Retrieved chunks are reranked using the cross-encoder reranker
- Only chunks above the relevance threshold are used for generation
- If a `provider` is specified, it uses that provider for this request only (without changing global settings)
- Answer includes source citations when enabled

**Per-Request Provider Override:**
```bash
# Use OpenAI for just this request
curl -sS http://localhost:8100/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Explain AES encryption",
    "provider": "openai",
    "openai_model": "gpt-4o-mini"
  }'

# Use Gemini for just this request
curl -sS http://localhost:8100/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Explain elliptic curve cryptography",
    "provider": "gemini",
    "gemini_model": "gemini-1.5-flash"
  }'
```

---

### POST /provider
Update the global LLM provider at runtime.

**IMPORTANT: Changing the provider does NOT restart the RAG system.**
- The embeddings model and reranker remain unchanged (they are the heart of the RAG)
- Only the LLM client used for answer generation is switched

**Request (Ollama):**
```json
{
  "provider": "ollama",
  "ollama_url": "http://ollama:11434",
  "ollama_model": "phi3"
}
```

**Request (Ollama Cloud):**
```json
{
  "provider": "ollama-cloud",
  "ollama_model": "gpt-oss:120b-cloud",
  "ollama_api_key": "your-api-key"
}
```

**Request (OpenAI):**
```json
{
  "provider": "openai",
  "openai_api_key": "your-api-key",
  "openai_model": "gpt-4o-mini",
  "openai_base_url": "https://api.openai.com"
}
```

**Request (Gemini):**
```json
{
  "provider": "gemini",
  "gemini_api_key": "your-api-key",
  "gemini_model": "gemini-1.5-flash",
  "gemini_base_url": "https://generativelanguage.googleapis.com"
}
```

**Response:**
```json
{
  "status": "updated",
  "provider": "openai",
  "generation_model": "gpt-4o-mini",
  "base_url": "https://api.openai.com"
}
```

**Examples:**
```bash
# Switch to local Ollama
curl -sS http://localhost:8100/provider \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "ollama",
    "ollama_url": "http://ollama:11434",
    "ollama_model": "phi3"
  }'

# Switch to Ollama Cloud
curl -sS http://localhost:8100/provider \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "ollama-cloud",
    "ollama_model": "gpt-oss:120b-cloud",
    "ollama_api_key": "..."
  }'

# Switch to OpenAI
curl -sS http://localhost:8100/provider \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "openai",
    "openai_model": "gpt-4o-mini",
    "openai_api_key": "..."
  }'

# Switch to Gemini
curl -sS http://localhost:8100/provider \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "gemini",
    "gemini_model": "gemini-1.5-flash",
    "gemini_api_key": "..."
  }'
```

---

### POST /config
Update runtime configuration for ingestion workers and parallel requests.

**Request:**
```json
{
  "ingestion_workers": 3,
  "parallel_requests": 2
}
```

**Parameters:**
- `ingestion_workers` (1-10) - Number of documents to process in parallel per batch cycle
- `parallel_requests` (1-10) - Number of generate requests to process in parallel (reserved for future use)

**Response:**
```json
{
  "status": "updated",
  "ingestion_workers": 3,
  "parallel_requests": 2,
  "message": "Configuration updated: ingestion_workers=3, parallel_requests=2"
}
```

**Expected Behavior:**
- Updates are applied immediately
- Increasing `ingestion_workers` processes more documents per batch cycle
- Values are persisted in memory only (reset on restart)

**Example:**
```bash
# Increase to process 5 documents at a time
curl -sS http://localhost:8100/config \
  -H 'Content-Type: application/json' \
  -d '{"ingestion_workers": 5}'
```

---

### GET /config
Get current runtime configuration values.

**Response:**
```json
{
  "ingestion_workers": 1,
  "parallel_requests": 1
}
```

---

### GET /conversations/{conversation_id}
Fetch full conversation history for a specific conversation.

**Response:**
```json
{
  "conversation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2025-01-15T10:00:00.000000Z",
  "messages": [
    {
      "id": 123,
      "role": "user",
      "content": "Explain RSA",
      "created_at": "2025-01-15T10:00:00.000000Z"
    },
    {
      "id": 124,
      "role": "assistant",
      "content": "RSA is an asymmetric cryptographic algorithm...",
      "created_at": "2025-01-15T10:00:05.000000Z"
    }
  ]
}
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `page_size` - Number of messages per page (default: 50, max: 200)

---

## Configuration

Environment variables can override defaults (see `app/config.py`):

### Database & Storage
- `DATABASE_URL` (default: `sqlite:////app/data/rag_system.db`)
- `CHROMA_PERSIST_DIRECTORY` (default: `./data/chromadb`)
- `DOCUMENTS_DIRECTORY` (default: `./documents`)
- `MODELS_CACHE_DIRECTORY` (default: `./models`)

### Embedding & Reranking
- `EMBEDDING_MODEL_NAME` (default: `BAAI/bge-small-en-v1.5`)
- `EMBEDDING_BATCH_SIZE` (default: `32`)
- `RERANKER_MODEL_NAME` (default: `BAAI/bge-reranker-base`)
- `RERANKER_BATCH_SIZE` (default: `16`)

### Retrieval Settings
- `RETRIEVAL_TOP_K` (default: `10`) - Number of chunks to retrieve
- `RERANKER_TOP_K` (default: `3`) - Number of chunks to use after reranking
- `RERANKER_THRESHOLD` (default: `0.5`) - Minimum reranker score
- `MIN_SOURCE_SCORE` (default: `0.35`) - Minimum source relevance

### LLM Providers

**Ollama (Local):**
- `OLLAMA_URL` (default: `http://127.0.0.1:11434`)
- `OLLAMA_MODEL` (default: `phi3`)
- `OLLAMA_API_KEY` (optional, for authenticated instances)
- `OLLAMA_USE_CHAT` (default: `true`)

**Ollama Cloud:**
- Set `OLLAMA_URL` to `https://ollama.com`
- Provide `OLLAMA_API_KEY`

**OpenAI:**
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (default: `https://api.openai.com`)

**Gemini:**
- `GEMINI_API_KEY`
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)
- `GEMINI_BASE_URL` (default: `https://generativelanguage.googleapis.com`)

**Default Provider:**
- `LLM_PROVIDER` (default: `ollama`)

### Ingestion Settings
- `INGESTION_INTERVAL_SECONDS` (default: `5`) - How often to check for new documents
- `INGESTION_BATCH_SIZE` (default: `1`) - Number of documents to process per cycle
- `INGESTION_MAX_FAILURES` (default: `3`) - Max retry attempts
- `ALLOW_REMOTE_INGEST` (default: `false`) - Allow ingesting from URLs
- `ALLOWED_REMOTE_HOSTS` (default: `""`) - Comma-separated list of allowed hosts
- `MAX_DOCUMENT_BYTES` (default: `25000000`) - Maximum document size (25MB)

### Answer Generation
- `GENERATION_TEMPERATURE` (default: `0.2`)
- `GENERATION_TOP_P` (default: `0.9`)
- `GENERATION_TOP_K` (default: `40`)
- `GENERATION_MAX_TOKENS` (default: `900`)
- `ANSWER_STYLE` (default: `abstractive`) - Options: `abstractive`, `extractive`
- `ALLOW_GENERAL_KNOWLEDGE` (default: `true`) - Allow LLM to use external knowledge
- `REQUIRE_CITATIONS` (default: `true`) - Require source citations in answers

### Lexical Retrieval (Optional)
- `ENABLE_LEXICAL_RETRIEVAL` (default: `true`)
- `LEXICAL_TOP_K` (default: `10`)
- `LEXICAL_WEIGHT` (default: `0.35`) - Weight for BM25 scores
- `VECTOR_WEIGHT` (default: `0.65`) - Weight for vector scores

### Query Processing
- `QUERY_CORRECTION_ENABLED` (default: `true`)
- `QUERY_CORRECTION_CUTOFF` (default: `0.84`)
- `QUERY_CACHE_SIZE` (default: `128`) - LRU cache for query embeddings
- `MAX_QUERY_LENGTH` (default: `5000`) - Maximum query length in characters

### Pagination
- `DEFAULT_CONVERSATION_PAGE_SIZE` (default: `50`)
- `MAX_CONVERSATION_PAGE_SIZE` (default: `200`)

## How It Works

1. **Document Ingestion:**
   - `/ingest` or `/auto-ingest` adds document metadata to SQLite (`reference_documents` table)
   - APScheduler polls every 5 seconds (configurable) for pending documents
   - Documents are chunked (~300 characters, 50 overlap)
   - Chunks are embedded with `BAAI/bge-small-en-v1.5` via FastEmbed
   - Embeddings stored in ChromaDB with metadata

2. **Query Processing:**
   - Query is embedded with the same model (cached if repeated)
   - Vector search retrieves top-k candidates from ChromaDB
   - Optional BM25 lexical search runs in parallel
   - Hybrid score combines vector and lexical weights

3. **Reranking:**
   - `BAAI/bge-reranker-base` cross-encoder reranks candidates
   - Only chunks above threshold are kept

4. **Answer Generation:**
   - Selected chunks formatted as context
   - Context sent to configured LLM (Ollama/OpenAI/Gemini)
   - Answer includes source citations

5. **Provider Switching:**
   - `/provider` updates LLM client without restarting RAG
   - Embeddings and reranker remain loaded
   - Per-request override available in `/generate`

## Testing

The project includes a comprehensive pytest test suite with **83 tests** covering all endpoints, components, and integration scenarios.

### Test Statistics

- **Endpoint Tests**: 44 tests (9 test classes)
- **Component Tests**: 19 tests (3 test classes)
- **Integration Tests**: 20 tests (7 test classes)
- **Total**: 83 tests

### Test Files

```
tests/
├── conftest.py                 # Pytest fixtures and configuration
├── test_endpoints.py           # API endpoint tests (44 tests)
├── test_document_discovery.py  # Component tests (19 tests)
├── test_integration.py         # Integration tests (20 tests)
└── README.md                   # Detailed testing guide
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_endpoints.py

# Run specific test class
pytest tests/test_endpoints.py::TestHealthEndpoint

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Coverage

The test suite covers:
- **All API endpoints** with success and error cases
- **Document discovery service** with edge cases
- **Integration workflows** for end-to-end scenarios
- **Provider switching** without RAG restart
- **Configuration management** at runtime
- **Concurrent access** patterns
- **Error recovery** scenarios

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Development

Run lint/checks locally:
```bash
python -m compileall app
```

To run the API without Docker (assumes dependencies installed):
```bash
uvicorn app.main:app --reload --port 8000
```

### Project Structure
```
theory_specialist/
├── app/
│   ├── __init__.py
│   ├── aggregator.py          # Background document processing
│   ├── config.py              # Settings and configuration
│   ├── database.py            # Database connection
│   ├── document_discovery.py  # Auto-discovery of new documents
│   ├── llm_client.py          # LLM abstraction layer
│   ├── main.py                # FastAPI endpoints
│   ├── models.py              # SQLAlchemy ORM models
│   ├── rag_system.py          # Core RAG logic
│   ├── reranker.py            # ONNX cross-encoder
│   └── schemas.py             # Pydantic request/response models
├── tests/                     # Comprehensive test suite (83 tests)
│   ├── conftest.py            # Pytest fixtures
│   ├── test_endpoints.py      # API endpoint tests
│   ├── test_document_discovery.py  # Component tests
│   ├── test_integration.py    # Integration tests
│   └── README.md              # Testing guide
├── data/                      # SQLite database and ChromaDB
├── documents/                 # Drop PDF/MD/TXT files here
├── models/                    # Cached embedding/reranker models
├── scripts/                   # Testing utilities
├── pytest.ini                 # Pytest configuration
└── requirements.txt           # Python dependencies
```

## License
Internal project for cryptography research assistance.
