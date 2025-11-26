# Software Details - Cryptography RAG System

**Project Name:** Cryptography RAG System with Automatic Document Ingestion
**Version:** 1.0.0
**Date:** November 1, 2025
**Architecture:** Microservices with Background Processing

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [System Architecture](#system-architecture)
3. [Component Specifications](#component-specifications)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Technology Stack](#technology-stack)
7. [Implementation Details](#implementation-details)
8. [Docker Configuration](#docker-configuration)
9. [Workflow & Behavior](#workflow--behavior)
10. [Performance Specifications](#performance-specifications)
11. [File Structure](#file-structure)
12. [Dependencies](#dependencies)

---

## 1. System Overview

### Purpose
A fully containerized, locally-deployed Retrieval-Augmented Generation (RAG) system specialized in cryptography theory. The system provides intelligent question-answering capabilities by processing large cryptography documents (PDF, MD, TXT) and maintaining persistent conversation history.

### Key Features
- ✅ **Fully Local Execution** - No external API dependencies
- ✅ **Automatic Background Ingestion** - Processes documents while serving queries
- ✅ **Persistent Storage** - Conversations, chunks, and document tracking across sessions
- ✅ **Intelligent Context Filtering** - Reranking to filter irrelevant information
- ✅ **Lightweight & Efficient** - Optimized models for CPU execution
- ✅ **RESTful API** - Clean endpoint design with health checks
- ✅ **Containerized Deployment** - Full Docker support

### Core Requirements Met

| Requirement | Implementation |
|-------------|----------------|
| Single generation endpoint | `POST /generate` |
| Request-response pattern | Synchronous API with async background tasks |
| Ingestion endpoint | `POST /ingest` |
| Status check endpoint | `GET /status` |
| Health check endpoint | `GET /health` |
| Document formats | PDF, MD, TXT support |
| Persistent storage | SQLite + ChromaDB volumes |
| Dual LLM architecture | Embedding model + Generation model |
| Relevance filtering | Cross-encoder reranking |
| Lightweight design | 80MB embeddings, 2GB generation |

---

## 2. System Architecture

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    DOCKER CONTAINER                       │
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │   Backend    │◄────►│  Aggregator  │                  │
│  │   (FastAPI)  │      │ (APScheduler)│                   │
│  └──────┬───────┘      └──────┬───────┘                   │
│         │                     │                           │
│         ▼                     ▼                          │
│  ┌──────────────────────────────────┐                     │
│  │        RAG System                │                     │
│  │  ┌─────────┐    ┌─────────┐      │                     │
│  │  │Embedding│    │Generation│     │                     │
│  │  │  Model  │    │   Model   │    │                     │
│  │  └────┬────┘    └─────┬────┘     │                     │
│  │       │               │          │                     │
│  │       └───────┬───────┘          │                     │
│  │               ▼                  │                     │
│  │      ┌─────────────────┐         │                     │
│  │      │   Vector DB     │         │                     │
│  │      │   (ChromaDB)    │         │                     │
│  │      │   [Embedded]    │         │                     │
│  │      └─────────────────┘         │                     │
│  └──────────────────────────────────┘                     │
│                   ▲                                       │
│                   │                                       │
│         ┌─────────┴─────────┐                             │
│         │  Persistent DB    │                             │
│         │    (SQLite)       │                             │
│         │                   │                             │
│         │ ┌───────────────┐ │                             │
│         │ │reference_docs │ │                             │
│         │ │document_chunks│ │                             │
│         │ │conversations  │ │                             │
│         │ │messages       │ │                             │
│         │ └───────────────┘ │                             │
│         └───────────────────┘                             │
└───────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. Document Ingestion:
   Client → Backend (/ingest) → Aggregator → Queue → Process

2. Background Processing:
   Aggregator (every 5s) → Check Queue → Load Document →
   Chunk → Embed → Store in ChromaDB + SQLite

3. Query Processing:
   Client → Backend (/generate) → Embed Query →
   Retrieve Chunks → Rerank → Generate → Store Conversation → Response
```

---

## 3. Component Specifications

### 3.1 Backend (FastAPI)

**Purpose:** REST API layer for external communication

**Responsibilities:**
- Handle HTTP requests/responses
- Validate input data
- Coordinate between aggregator and RAG system
- Manage conversation sessions
- Provide health monitoring

**Key Files:**
- `main.py` - FastAPI application and endpoints
- `schemas.py` - Pydantic request/response models

**Port:** 8000

### 3.2 Aggregator (APScheduler)

**Purpose:** Background task scheduler for document processing

**Responsibilities:**
- Maintain document processing queue
- Process documents in alphabetical order
- Update document processing status
- Handle processing errors with retry logic
- Prevent concurrent processing conflicts

**Key Features:**
- Interval-based polling (5 second intervals)
- Status tracking (0=unprocessed, 1=in_progress, 2=processed)
- Automatic retry on failure
- Non-blocking execution

**Key Files:**
- `aggregator.py` - Document queue manager

### 3.3 RAG System

**Purpose:** Core intelligence layer for embeddings, retrieval, and generation

**Responsibilities:**
- Load and chunk documents
- Generate embeddings
- Store vectors in ChromaDB
- Retrieve relevant chunks
- Rerank for relevance
- Generate answers with LLM

**Key Components:**

#### 3.3.1 Embedding Model
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Size:** 80MB
- **Dimensions:** 384
- **Speed:** ~500 sentences/second on CPU
- **Purpose:** Convert text to semantic vectors

#### 3.3.2 Generation Model
- **Model:** Ollama (Phi-3-mini recommended)
- **Size:** 2.3GB
- **Purpose:** Generate human-readable answers
- **RAM Required:** 4GB minimum

#### 3.3.3 Reranking Model
- **Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Purpose:** Filter irrelevant context
- **Threshold:** 0.5 (50% relevance)
- **Improvement:** +10-20% accuracy over bi-encoder alone

**Key Files:**
- `rag_system.py` - RAG logic implementation

### 3.4 Persistent Storage

**Purpose:** Maintain state across sessions

**Components:**

#### 3.4.1 SQLite Database
- **File:** `rag_system.db`
- **Purpose:** Store conversations, document metadata, chunks
- **Location:** `/app/data/rag_system.db` (volume mounted)

#### 3.4.2 Vector Database (ChromaDB - Embedded)
- **Purpose:** Fast semantic search
- **Storage:** `/app/data/chromadb` (volume mounted)
- **Collection:** `cryptography_chunks`
- **Distance Metric:** Cosine similarity
- **Architecture:** Embedded mode (runs in-process, no separate container)

**Key Files:**
- `models.py` - SQLAlchemy ORM models

---

## 4. Database Schema

### 4.1 SQLite Tables

#### Table: `reference_documents`

**Purpose:** Track all documents to be processed

| Column | Type | Description | Default |
|--------|------|-------------|---------|
| `id` | INTEGER | Primary key | AUTO |
| `document_path` | STRING | Local path or URL | - |
| `document_name` | STRING | Filename for display | - |
| `document_type` | STRING | 'pdf', 'md', or 'txt' | - |
| `file_size` | INTEGER | Size in bytes | 0 |
| `processing_status` | INTEGER | 0=unprocessed, 1=in_progress, 2=processed | 0 |
| `created_at` | DATETIME | When added to queue | NOW |
| `processed_at` | DATETIME | When processing completed | NULL |
| `error_message` | STRING | Error if failed | NULL |
| `chunks_count` | INTEGER | Number of chunks created | 0 |

**Indexes:**
- Primary key on `id`
- Unique index on `document_path`
- Index on `document_name` (for alphabetical ordering)
- Index on `processing_status` (for queue queries)

**Behavior:**
- Documents added via `/ingest` endpoint
- Processed in alphabetical order by `document_name`
- Status automatically updated by aggregator
- Failures reset to `processing_status=0` for retry

---

#### Table: `document_chunks`

**Purpose:** Store processed text chunks with metadata

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `reference_doc_id` | INTEGER | Foreign key to `reference_documents` |
| `chunk_index` | INTEGER | Order within document |
| `chunk_text` | TEXT | Actual content |
| `token_count` | INTEGER | Approximate token count |
| `embedding_vector` | STRING | JSON array of embedding floats |
| `embedding_model` | STRING | Model identifier |
| `source_title` | STRING | Document title |
| `source_page` | INTEGER | Page number (if PDF) |
| `created_at` | DATETIME | Timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `reference_doc_id`
- Index on `chunk_index` for ordering

**Relationships:**
- Many-to-one with `reference_documents`

---

#### Table: `conversations`

**Purpose:** Track conversation sessions

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `conversation_id` | STRING | UUID for external reference |
| `title` | STRING | Optional conversation title |
| `created_at` | DATETIME | Session start |
| `updated_at` | DATETIME | Last activity |

**Indexes:**
- Primary key on `id`
- Unique index on `conversation_id`

**Behavior:**
- Created automatically on first query
- Persist across API calls
- Can be retrieved via `/conversations/{id}`

---

#### Table: `messages`

**Purpose:** Store all conversation messages

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `conversation_id` | STRING | Foreign key to conversations |
| `role` | STRING | 'user' or 'assistant' |
| `content` | TEXT | Message content |
| `retrieved_chunks_ids` | STRING | JSON array of chunk IDs used |
| `relevance_scores` | STRING | JSON array of scores |
| `created_at` | DATETIME | Message timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `conversation_id`
- Index on `created_at` for chronological ordering

**Relationships:**
- Many-to-one with `conversations`

---

### 4.2 Vector Database (ChromaDB)

**Collection:** `cryptography_chunks`

**Configuration:**
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    persist_directory="/app/data/chromadb",
    anonymized_telemetry=False
))

collection = client.get_or_create_collection(
    name="cryptography_chunks",
    metadata={"hnsw:space": "cosine"}
)
```

**Document Structure:**
```python
{
    "id": f"{doc_id}_{chunk_idx}",  # Unique string identifier
    "embedding": [0.123, 0.456, ...],  # 384 dimensions
    "metadata": {
        "ref_doc_id": 123,
        "chunk_index": 5,
        "text": "Chunk content...",
        "source": "document_name.pdf"
    }
}
```

**Operations:**
- **Insert:** `collection.add(ids=[...], embeddings=[...], metadatas=[...])`
- **Search:** `collection.query(query_embeddings=[...], n_results=10)`
- **Persistence:** Automatic on-disk persistence with DuckDB backend

**Storage Backend:**
- **DuckDB** - Metadata storage
- **Parquet** - Efficient columnar storage for embeddings
- **Total size:** ~1.5GB per 1M vectors

---

## 5. API Endpoints

### 5.1 Health Check

```http
GET /health
```

**Purpose:** Verify system operational status

**Response:**
```json
{
    "status": "healthy",
    "database": "connected",
    "embedding_model": "loaded",
    "generation_model": "loaded",
    "vector_db_chunks": 15234,
    "timestamp": "2025-11-01T15:22:00Z"
}
```

**Status Codes:**
- `200` - All systems operational
- `500` - System unhealthy with error details

---

### 5.2 Document Ingestion

```http
POST /ingest
Content-Type: application/json

{
    "document_path": "/app/documents/rsa_theory.pdf",
    "document_type": "pdf"
}
```

**Purpose:** Add documents to processing queue

**Parameters:**
- `document_path` (string, required) - Local file path or URL
- `document_type` (string, required) - One of: 'pdf', 'md', 'txt'

**Response:**
```json
{
    "status": "queued",
    "message": "Document added to processing queue: /app/documents/rsa_theory.pdf",
    "next_status_check": "/status"
}
```

**Status Codes:**
- `200` - Document queued successfully
- `400` - Invalid request (missing fields)
- `500` - Server error

**Behavior:**
- Document immediately added to `reference_documents` table
- Processing status set to `0` (unprocessed)
- Aggregator picks up automatically within 5 seconds
- Duplicate paths rejected

---

### 5.3 Status Check

```http
GET /status
```

**Purpose:** Monitor document processing progress

**Response:**
```json
{
    "total_reference_documents": 25,
    "processed_documents": 18,
    "in_progress_documents": 1,
    "pending_documents": 6,
    "total_chunks_in_vector_db": 4523,
    "currently_processing": "zero_knowledge_proofs.pdf",
    "timestamp": "2025-11-01T15:22:00Z"
}
```

**Status Codes:**
- `200` - Status retrieved successfully
- `500` - Server error

**Use Cases:**
- Monitor ingestion progress
- Verify all documents processed before deployment
- Debugging processing issues

---

### 5.4 Generation (RAG Query)

```http
POST /generate
Content-Type: application/json

{
    "query": "Explain the RSA algorithm and its security assumptions",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Purpose:** Query the RAG system for cryptography answers

**Parameters:**
- `query` (string, required) - User question
- `conversation_id` (string, optional) - UUID for conversation continuity (auto-generated if null)

**Response:**
```json
{
    "answer": "RSA (Rivest-Shamir-Adleman) is an asymmetric cryptographic algorithm...",
    "sources": [
        {
            "chunk_id": "12345",
            "relevance_score": 0.87,
            "preview": "RSA algorithm relies on the mathematical difficulty..."
        }
    ],
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": 789
}
```

**Status Codes:**
- `200` - Answer generated successfully
- `404` - Conversation ID not found
- `500` - Server error

**Processing Pipeline:**
1. Embed query with `all-MiniLM-L6-v2`
2. Retrieve top 10 chunks from ChromaDB
3. Rerank with cross-encoder (threshold 0.5)
4. Keep top 3 most relevant chunks
5. Generate answer with local LLM
6. Store user query and assistant response in database

---

### 5.5 Conversation History

```http
GET /conversations/{conversation_id}
```

**Purpose:** Retrieve full conversation history

**Parameters:**
- `conversation_id` (path parameter) - UUID of conversation

**Response:**
```json
{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-01T14:30:00Z",
    "messages": [
        {
            "id": 1,
            "role": "user",
            "content": "Explain RSA",
            "created_at": "2025-11-01T14:30:05Z"
        },
        {
            "id": 2,
            "role": "assistant",
            "content": "RSA is an asymmetric encryption algorithm...",
            "created_at": "2025-11-01T14:30:08Z"
        }
    ]
}
```

**Status Codes:**
- `200` - History retrieved
- `404` - Conversation not found
- `500` - Server error

---

## 6. Technology Stack

### Backend & API
- **FastAPI** 0.104.0 - High-performance web framework
- **Uvicorn** 0.24.0 - ASGI server
- **Pydantic** 2.5.0 - Data validation

### Database & Storage
- **SQLAlchemy** 2.0.23 - ORM for SQLite
- **SQLite** 3.x - Embedded database
- **ChromaDB** 0.4.18 - Embedded vector database

### Machine Learning
- **sentence-transformers** 2.2.2 - Embedding models
- **transformers** 4.35.0 - Hugging Face transformers
- **torch** 2.1.0 - PyTorch backend

### Document Processing
- **PyPDF2** 3.0.1 - PDF text extraction
- **langchain** 0.0.340 - Text chunking utilities
- **markdown** 3.5.1 - Markdown parsing

### Task Scheduling
- **APScheduler** 3.10.4 - Background job scheduling

### Containerization
- **Docker** 24.0+
- **Docker Compose** 2.20+

### Optional
- **Ollama** - Local LLM runtime
- **Phi-3-mini** - Generation model (via Ollama)

---

## 7. Implementation Details

### 7.1 ChromaDB Initialization

**Embedded Configuration:**
```python
# rag_system.py
import chromadb
from chromadb.config import Settings

class RAGSystem:
    def __init__(self):
        # Initialize ChromaDB in embedded mode
        self.chroma_client = chromadb.Client(Settings(
            persist_directory="/app/data/chromadb",
            anonymized_telemetry=False,
            allow_reset=True
        ))

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="cryptography_chunks",
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2'
        )
```

---

### 7.2 Document Processing Pipeline

**Step 1: Document Loading**
```python
def load_and_chunk_document(document_path: str, doc_type: str):
    if doc_type == "pdf":
        text = extract_pdf(document_path)
    elif doc_type == "md":
        text = read_markdown(document_path)
    elif doc_type == "txt":
        text = read_text(document_path)

    return text
```

**Step 2: Text Chunking**
```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,      # ~300 tokens per chunk
    chunk_overlap=50,    # 50 token overlap for context
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_text(text)
```

**Step 3: Embedding & Storage in ChromaDB**
```python
def process_chunks(self, chunks: list, reference_doc_id: int):
    db = SessionLocal()

    try:
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)

        # Prepare data for ChromaDB
        ids = [f"{reference_doc_id}_{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "ref_doc_id": reference_doc_id,
                "chunk_index": idx,
                "text": chunk,
                "source": f"doc_{reference_doc_id}"
            }
            for idx, chunk in enumerate(chunks)
        ]

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        # Store in SQLite for backup
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                reference_doc_id=reference_doc_id,
                chunk_index=idx,
                chunk_text=chunk,
                token_count=len(chunk.split()),
                embedding_vector=json.dumps(embedding.tolist()),
                embedding_model="all-MiniLM-L6-v2"
            )
            db.add(db_chunk)

        db.commit()
    finally:
        db.close()
```

---

### 7.3 Query Processing Pipeline

**Step 1: Query Embedding**
```python
query_vector = embedding_model.encode(query)
```

**Step 2: ChromaDB Vector Search**
```python
def retrieve_chunks(self, query_embedding, top_k=10):
    results = self.collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    retrieved = []
    for idx in range(len(results['ids'][0])):
        retrieved.append({
            "id": results['ids'][0][idx],
            "text": results['metadatas'][0][idx]['text'],
            "distance": results['distances'][0][idx],
            "score": 1 - results['distances'][0][idx]  # Convert distance to similarity
        })

    return retrieved
```

**Step 3: Reranking**
```python
def rerank_chunks(self, query: str, chunks: list, threshold=0.5):
    # Cross-encoder scores
    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = self.cross_encoder.predict(pairs)

    # Filter and sort
    relevant = []
    for chunk, score in zip(chunks, scores):
        if score > threshold:
            chunk["reranker_score"] = float(score)
            relevant.append(chunk)

    relevant = sorted(
        relevant,
        key=lambda x: x["reranker_score"],
        reverse=True
    )

    return relevant[:3]  # Top 3
```

---

### 7.4 Background Processing Logic

**Aggregator Main Loop:**
```python
def process_next_document():
    if is_processing:
        return

    # Get next unprocessed document (alphabetical)
    next_doc = db.query(ReferenceDocument).filter(
        ReferenceDocument.processing_status == 0
    ).order_by(ReferenceDocument.document_name).first()

    if not next_doc:
        return

    # Mark as in-progress
    next_doc.processing_status = 1
    db.commit()

    try:
        chunks = rag_system.load_and_chunk_document(
            next_doc.document_path,
            next_doc.document_type
        )

        rag_system.process_chunks(chunks, next_doc.id)

        # Mark as complete
        next_doc.processing_status = 2
        next_doc.processed_at = datetime.utcnow()
        next_doc.chunks_count = len(chunks)

    except Exception as e:
        next_doc.processing_status = 0
        next_doc.error_message = str(e)

    finally:
        db.commit()
```

---

## 8. Docker Configuration

### 8.1 docker-compose.yml

```yaml
version: '3.8'

services:
  # RAG Backend API (with embedded ChromaDB)
  rag-backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: rag_backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:////app/data/rag_system.db
      - CHROMADB_PATH=/app/data/chromadb
      - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
      - RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./data:/app/data              # Persistent SQLite + ChromaDB
      - ./documents:/app/documents    # Your crypto documents
      - ./models:/app/models          # Cached ML models
    depends_on:
      - ollama
    networks:
      - rag_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Local LLM (Ollama)
  ollama:
    image: ollama/ollama:latest
    container_name: ollama_llm
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - rag_network
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local

networks:
  rag_network:
    driver: bridge
```

---

### 8.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data /app/data/chromadb /app/documents /app/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

---

### 8.3 requirements.txt

```
# Web Framework
fastapi==0.104.0
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
alembic==1.13.0

# Machine Learning
sentence-transformers==2.2.2
transformers==4.35.0
torch==2.1.0

# Vector Database (Embedded)
chromadb==0.4.18

# Document Processing
PyPDF2==3.0.1
langchain==0.0.340
markdown==3.5.1
python-magic==0.4.27

# Background Tasks
apscheduler==3.10.4

# Utilities
python-dotenv==1.0.0
requests==2.31.0
```

---

### 8.4 Volume Persistence

| Volume | Purpose | Data Stored |
|--------|---------|-------------|
| `./data:/app/data` | SQLite + ChromaDB | `rag_system.db` and `/chromadb` directory |
| `./documents:/app/documents` | Input documents | Your PDF/MD/TXT files |
| `./models:/app/models` | Model cache | Downloaded transformer models |
| `ollama_data` | LLM models | Ollama model files |

**ChromaDB Persistence:**
```
/app/data/chromadb/
├── chroma.sqlite3       # DuckDB metadata
└── [collection_id]/
    ├── data_level0.bin  # Vector data
    ├── header.bin       # Collection metadata
    └── link_lists.bin   # HNSW graph
```

---

## 9. Workflow & Behavior

### 9.1 System Startup Sequence

```
1. Docker Compose starts services:
   ├── Ollama loads LLM model
   └── RAG Backend starts

2. Backend initialization:
   ├── Connect to SQLite (/app/data/rag_system.db)
   ├── Create tables if not exist
   ├── Initialize ChromaDB (embedded) at /app/data/chromadb
   ├── Load embedding model (all-MiniLM-L6-v2)
   ├── Load reranker model (cross-encoder)
   └── Start APScheduler background thread

3. Aggregator starts:
   └── Begin checking for unprocessed documents every 5s

4. System ready to accept requests
```

---

### 9.2 Document Processing Workflow

**User Action:**
```bash
POST /ingest
{
  "document_path": "/app/documents/aes_encryption.pdf",
  "document_type": "pdf"
}
```

**System Behavior:**

```
T+0s:   Document added to reference_documents table
        └── processing_status = 0 (unprocessed)

T+5s:   Aggregator picks up document
        └── processing_status = 1 (in_progress)
        └── Load PDF content
        └── Split into chunks (300 tokens each)

T+8s:   Generate embeddings for all chunks
        └── Batch processing: ~100 chunks/second

T+12s:  Store chunks
        ├── ChromaDB: Insert vectors (embedded, no network)
        └── SQLite: Insert chunk metadata

T+15s:  Mark as complete
        └── processing_status = 2 (processed)
        └── processed_at = NOW
        └── chunks_count = 142
```

**Processing Order:**
- Alphabetical by `document_name`:
  1. `aes_encryption.pdf`
  2. `elliptic_curve_crypto.md`
  3. `rsa_algorithm.txt`
  4. `zero_knowledge_proofs.pdf`

---

### 9.3 Query Workflow

**User Action:**
```bash
POST /generate
{
  "query": "What is the Diffie-Hellman key exchange?",
  "conversation_id": null
}
```

**System Behavior:**

```
T+0ms:    Receive request
          └── Generate conversation_id (UUID)

T+50ms:   Embed query (in-process)

T+80ms:   ChromaDB search (embedded, no network latency)
          └── Top 10 chunks

T+150ms:  Rerank with cross-encoder
          └── Keep top 3

T+200ms:  Assemble context

T+400ms:  Generate with Ollama

T+450ms:  Store conversation

T+500ms:  Return response
```

---

## 10. Performance Specifications

### 10.1 Resource Requirements

| Component | CPU | RAM | Disk | GPU |
|-----------|-----|-----|------|-----|
| Embedding Model | 2 cores | 2GB | 500MB | Optional |
| Reranker Model | 1 core | 1GB | 300MB | Optional |
| Generation Model | 2 cores | 4GB | 2.5GB | Recommended |
| ChromaDB | 0.5 cores | 1GB | Variable | No |
| FastAPI | 1 core | 1GB | 100MB | No |
| **Total** | **4+ cores** | **8GB+** | **10GB+** | **Optional** |

### 10.2 Performance Metrics

| Operation | Latency | Throughput |
|-----------|---------|------------|
| Embed query | 20-50ms | 500 queries/sec |
| ChromaDB search | 30-80ms | 150 queries/sec |
| Reranking (10 docs) | 100-200ms | 50 queries/sec |
| LLM generation | 1-5s | 1-5 tokens/sec |
| **Full query pipeline** | **2-6s** | **0.2-0.5 queries/sec** |

---

## 11. File Structure

```
rag-cryptography-system/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── SOFTWARE_DETAILS.md
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── aggregator.py
│   ├── rag_system.py
│   └── config.py
│
├── data/
│   ├── rag_system.db            # SQLite
│   └── chromadb/                # ChromaDB persistent directory
│       ├── chroma.sqlite3
│       └── [collection_data]/
│
├── documents/
│   ├── aes_encryption.pdf
│   └── ...
│
├── models/
│   └── sentence-transformers/
│
└── scripts/
    ├── setup.sh
    ├── add_documents.py
    └── query_example.py
```

---

## 12. Dependencies

### 12.1 Core Packages

```
fastapi==0.104.0
sqlalchemy==2.0.23
sentence-transformers==2.2.2
chromadb==0.4.18               # Embedded vector DB
apscheduler==3.10.4
PyPDF2==3.0.1
```

### 12.2 External Services

| Service | Purpose | Connection |
|---------|---------|------------|
| ChromaDB | Vector DB (embedded) | `persist_directory=/app/data/chromadb` |
| Ollama | LLM generation | `http://ollama:11434` |
| SQLite | Metadata storage | `sqlite:///data/rag_system.db` |

---

## 13. Key Design Decisions

### 13.1 Why ChromaDB?

**ChromaDB Advantages for Local Deployment:**

| Feature | Benefit |
|---------|---------|
| **Embedded Mode** | Runs in Python process - no separate container |
| **Zero Config** | No network setup, ports, or service management |
| **Persistent** | Native `persist_directory` with DuckDB backend |
| **Lightweight** | ~100MB RAM vs 200MB+ for standalone databases |
| **Simple API** | Pythonic interface, easy debugging |
| **Docker-Friendly** | Single volume mount |

**Architecture Comparison:**

```
Standalone Vector DB (Qdrant):
Docker → Network → Qdrant Container → Storage

Embedded ChromaDB:
Docker → RAG Backend (ChromaDB embedded) → Local Storage
```

**Code Example:**
```python
# ChromaDB - Simple embedded initialization
import chromadb
client = chromadb.Client(Settings(
    persist_directory="/app/data/chromadb"
))
# That's it! No network, no separate container
```

---

### 13.2 Why APScheduler?

| Aspect | APScheduler | Celery |
|--------|-------------|--------|
| Complexity | Simple | Requires Redis/RabbitMQ |
| Local Use | Perfect | Overkill |
| Setup | 5 lines | Complex config |

---

### 13.3 Why SQLite?

| Aspect | SQLite | PostgreSQL |
|--------|--------|------------|
| Deployment | Zero config | Requires server |
| Portability | Single file | Connection string |
| Performance | Excellent | Better for writes |

---

## 14. Deployment

### Quick Start

```bash
# 1. Setup
mkdir -p data documents models
cp /path/to/pdfs/* documents/

# 2. Start
docker-compose up -d

# 3. Pull LLM
docker exec -it ollama_llm ollama pull phi3

# 4. Verify
curl http://localhost:8000/health
```

---

**Document Version:** 1.0.0
**Last Updated:** November 1, 2025
**Vector Database:** ChromaDB (Embedded)
