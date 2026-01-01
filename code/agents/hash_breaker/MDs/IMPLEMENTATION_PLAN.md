# Hash Breaker Microservice - Implementation Plan

## Bachelor Thesis Edition

**Based on Your Requirements**:
- Single-node deployment with heterogeneous GPU support
- RabbitMQ + Dramatiq (reliable task distribution)
- PagPassGPT (state-of-the-art, 2024)
- 24-hour result storage
- Personal tool (no auth needed)
- Basic monitoring (Prometheus)
- Academic research (thesis work)

---

## Phase 1: Setup & FLA Model Training (Week 1)

### Goal: Train PagPassGPT model for password generation

**Note on PagPassGPT Availability**:
As of January 2025, PagPassGPT code may not be publicly available (paper published April 2024).

**Options**:

#### Option A: Implement PagPassGPT from Paper (Recommended for Thesis)
- **Pros**: Cutting-edge, thesis contribution, best performance
- **Cons**: Requires implementation from paper (2-3 weeks)
- **Thesis Value**: ⭐⭐⭐⭐⭐ (novel contribution)

**Steps**:
1. Download RockYou dataset
2. Implement GPT-2 character-level tokenizer
3. Implement D&C-GEN algorithm (key innovation)
4. Train with pattern-guided generation
5. Evaluate on test set (MAYA benchmarking framework)

#### Option B: Use PassGPT Pre-trained (Faster)
- **Pros**: Models available on HuggingFace, works immediately
- **Cons**: Not state-of-the-art (12% worse than PagPassGPT)
- **Thesis Value**: ⭐⭐⭐ (solid, but not novel)

**Steps**:
```bash
# Install PassGPT
pip install transformers

# Download pre-trained model (10-char version)
from transformers import GPT2LMHeadModel, RobertaTokenizerFast
tokenizer = RobertaTokenizerFast.from_pretrained("javirandor/passgpt-10characters")
model = GPT2LMHeadModel.from_pretrained("javirandor/passgpt-10characters")
```

#### Option C: Train FLA (Backup Plan)
- **Pros**: Lightweight, trainable on CPU
- **Cons**: 42.9% worse than PassTCN, not state-of-the-art
- **Thesis Value**: ⭐⭐ (adequate baseline)

---

## Phase 2: API Development (Week 2-3)

### Project Structure

```
hash_breaker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   ├── worker.py               # Dramatiq worker
│   ├── cracking/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Multi-phase cracking
│   │   ├── phases/
│   │   │   ├── phase1_dict.py
│   │   │   ├── phase2_rules.py
│   │   │   ├── phase3_ai.py    # PagPassGPT generation
│   │   │   └── phase4_mask.py
│   │   └── tools.py            # Hashcat/JtR wrappers
│   ├── ml/
│   │   ├── __init__.py
│   │   └── pagpassgpt.py       # PagPassGPT generator
│   └── utils/
│       ├── __init__.py
│       ├── redis_client.py
│       └── metrics.py
├── tests/
│   ├── test_api.py
│   ├── test_worker.py
│   └── test_cracking.py
├── wordlists/
│   ├── rockyou.txt
│   └── top100k.txt
├── models/
│   └── pagpassgpt_rockyou.pt
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Core Files to Implement

#### 1. `app/main.py` (FastAPI Application)

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
from .cracking.pipeline import submit_job
from .utils.redis_client import RedisClient

app = FastAPI(title="Hash Breaker Microservice", version="1.0.0")
redis = RedisClient()

class HashAuditRequest(BaseModel):
    hash: str
    hash_type_id: int
    timeout_seconds: int = 60

@app.post("/v1/audit-hash")
async def audit_hash(request: HashAuditRequest):
    """Submit hash cracking job."""
    job_id = str(uuid.uuid4())

    # Submit to Dramatiq queue
    submit_job.send(job_id, request.hash, request.hash_type_id, request.timeout_seconds)

    # Create initial state in Redis
    redis.set(f"job:{job_id}", {
        "status": "pending",
        "progress": 0,
        "submitted_at": datetime.utcnow().isoformat()
    }, ex=86400)  # 24h TTL

    return {"job_id": job_id, "status": "pending"}

@app.get("/v1/status/{job_id}")
async def get_status(job_id: str):
    """Get job status."""
    job_state = redis.get(f"job:{job_id}")
    if not job_state:
        raise HTTPException(404, "Job not found")
    return job_state

@app.get("/v1/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/v1/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Return metrics in Prometheus format
    from .utils.metrics import generate_metrics
    return generate_metrics()
```

#### 2. `app/worker.py` (Dramatiq Worker)

```python
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from .cracking.pipeline import run_cracking_pipeline

# Configure RabbitMQ broker
broker = RabbitmqBroker(host="localhost")
dramatiq.set_broker(broker)

@dramatiq.actor(max_retries=3, queue_name="cracking")
def process_cracking_job(job_id: str, hash: str, hash_type_id: int, timeout: int):
    """Process hash cracking job."""
    result = run_cracking_pipeline(job_id, hash, hash_type_id, timeout)
    # Update Redis with result
    redis.set(f"job:{job_id}", result, ex=86400)
```

#### 3. `app/cracking/pipeline.py` (Multi-Phase Pipeline)

```python
import time
from .phases.phase1_dict import quick_dictionary_attack
from .phases.phase2_rules import rule_based_attack
from .phases.phase3_ai import ai_generation_attack
from .phases.phase4_mask import mask_attack
from ..utils.redis_client import RedisClient

redis = RedisClient()

def run_cracking_pipeline(job_id: str, hash: str, hash_type_id: int, timeout: int):
    """Run multi-phase cracking pipeline."""

    start_time = time.time()

    # Update status
    redis.update(f"job:{job_id}", {
        "status": "running",
        "current_phase": "Phase 1: Quick Dictionary Attack",
        "progress": 0
    })

    # Phase 1: Quick Dictionary (10% time)
    budget_1 = timeout * 0.10
    result = quick_dictionary_attack(hash, hash_type_id, budget_1)
    if result["cracked"]:
        return {"status": "success", "result": result["password"], "phase": 1}

    # Phase 2: Rule-Based (25% time)
    elapsed = time.time() - start_time
    if elapsed < timeout * 0.35:
        budget_2 = min(timeout * 0.25, timeout - elapsed)
        redis.update(f"job:{job_id}", {"current_phase": "Phase 2: Rule-Based Attack", "progress": 25})
        result = rule_based_attack(hash, hash_type_id, budget_2)
        if result["cracked"]:
            return {"status": "success", "result": result["password"], "phase": 2}

    # Phase 3: AI Generation (35% time) - PagPassGPT
    elapsed = time.time() - start_time
    if elapsed < timeout * 0.70:
        budget_3 = min(timeout * 0.35, timeout - elapsed)
        redis.update(f"job:{job_id}", {"current_phase": "Phase 3: AI Generation (PagPassGPT)", "progress": 50})
        result = ai_generation_attack(hash, hash_type_id, budget_3)
        if result["cracked"]:
            return {"status": "success", "result": result["password"], "phase": 3}

    # Phase 4: Mask Attack (remaining time)
    elapsed = time.time() - start_time
    if elapsed < timeout:
        budget_4 = timeout - elapsed
        redis.update(f"job:{job_id}", {"current_phase": "Phase 4: Limited Mask Attack", "progress": 75})
        result = mask_attack(hash, hash_type_id, budget_4)
        if result["cracked"]:
            return {"status": "success", "result": result["password"], "phase": 4}

    # All phases failed
    return {
        "status": "failed",
        "reason": "Password not found after all phases",
        "attempts": result["attempts"]
    }
```

#### 4. `app/cracking/phases/phase3_ai.py` (PagPassGPT Integration)

```python
import subprocess
from pathlib import Path

def ai_generation_attack(hash: str, hash_type_id: int, timeout: int):
    """Phase 3: AI-generated candidates using PagPassGPT."""

    # Generate passwords using PagPassGPT
    generator_path = Path("/app/ml/pagpassgpt_generator.py")

    # Pipe directly to hashcat (no intermediate file)
    cmd = f"""
    python {generator_path} --num 5000000 --temperature 0.8 --top-k 40 |
    hashcat -m {hash_type_id} - --stdin --potfile-disable --quiet --force
    """

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            input=hash.encode(),
            timeout=timeout,
            capture_output=True
        )

        output = result.stdout.decode()
        if output and ":" in output:
            password = output.split(":")[1].strip()
            return {"cracked": True, "password": password, "attempts": 5000000}

    except subprocess.TimeoutExpired:
        pass

    return {"cracked": False, "attempts": 5000000}
```

---

## Phase 3: Docker & Deployment (Week 4)

### Dockerfile

```dockerfile
# Multi-stage build
FROM nvidia/cuda:12.1-runtime-ubuntu22.04 AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    hashcat \
    john \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY models/ ./models/
COPY wordlists/ ./wordlists/

# Expose port
EXPOSE 8000

# Run application (API or worker based on ENV)
CMD ["python3", "-m", "app.main"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
      - REDIS_URL=redis://redis:6379
      - SERVICE_TYPE=api
    depends_on:
      - rabbitmq
      - redis
    volumes:
      - ./models:/app/models:ro
      - ./wordlists:/app/wordlists:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  worker:
    build: .
    command: dramatiq app.worker -p 4 -t rabbitmq
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
      - REDIS_URL=redis://redis:6379
      - SERVICE_TYPE=worker
    depends_on:
      - rabbitmq
      - redis
    volumes:
      - ./models:/app/models:ro
      - ./wordlists:/app/wordlists:ro
    deploy:
      replicas: 2  # 2 worker processes

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=guest
      - RABBITMQ_DEFAULT_PASS=guest
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  rabbitmq_data:
  redis_data:
```

---

## Phase 4: Testing & Validation (Week 5)

### Test Suite

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_submit_job():
    response = client.post("/v1/audit-hash", json={
        "hash": "5d41402abc4b2a76b9719d911017c592",  # "hello"
        "hash_type_id": 0,  # MD5
        "timeout_seconds": 60
    })

    assert response.status_code == 202
    assert "job_id" in response.json()

def test_get_status():
    # Submit job first
    job = client.post("/v1/audit-hash", json={...}).json()
    job_id = job["job_id"]

    # Check status
    response = client.get(f"/v1/status/{job_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "running", "success", "failed"]

def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## Phase 5: Performance Benchmarking (Week 6-7)

### Benchmarking Script

```python
# benchmarks/benchmark.py
import time
import statistics
from app.main import client

TEST_HASHES = {
    "MD5": "5d41402abc4b2a76b9719d911017c592",  # "hello"
    "SHA1": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",  # "hello"
    "SHA256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",  # "hello"
}

def run_benchmark(hash_type, hash_value, timeout=60, iterations=10):
    """Run benchmark for specific hash type."""

    times = []
    successes = 0

    for _ in range(iterations):
        start = time.time()

        response = client.post("/v1/audit-hash", json={
            "hash": hash_value,
            "hash_type_id": hash_type,
            "timeout_seconds": timeout
        })

        submit_time = time.time() - start
        job_id = response.json()["job_id"]

        # Poll for completion
        while True:
            status = client.get(f"/v1/status/{job_id}").json()
            if status["status"] in ["success", "failed"]:
                break
            time.sleep(1)

        total_time = time.time() - start
        times.append(total_time)

        if status["status"] == "success":
            successes += 1

    return {
        "hash_type": hash_type,
        "success_rate": successes / iterations,
        "avg_time": statistics.mean(times),
        "median_time": statistics.median(times),
        "min_time": min(times),
        "max_time": max(times)
    }

# Run benchmarks
for hash_type, hash_value in TEST_HASHES.items():
    result = run_benchmark(hash_type, hash_value)
    print(f"{hash_type}: {result}")
```

---

## Phase 6: Documentation & Thesis Write-up (Week 8)

### Thesis Structure Suggestion

1. **Introduction**
   - Password security & hash cracking
   - Limitations of traditional methods
   - AI-based password guessing evolution

2. **Background**
   - PassGAN → FLA → PassGPT → **PagPassGPT** (state-of-the-art)
   - Multi-phase attack strategies
   - Microservices architecture

3. **System Design**
   - Overall architecture (FastAPI + Dramatiq + RabbitMQ)
   - Multi-phase cracking pipeline
   - PagPassGPT integration
   - Heterogeneous GPU support

4. **Implementation**
   - Technology choices (why Dramatiq over Celery, etc.)
   - Docker deployment
   - API design

5. **Evaluation**
   - Performance benchmarks (success rate by hash type)
   - Comparison with traditional tools (Hashcat-only)
   - Ablation study (with/without AI phase)
   - MAYA framework integration

6. **Conclusion & Future Work**
   - Contributions (PagPassGPT implementation)
   - Limitations
   - Future improvements (multi-model ensemble, etc.)

---

## Summary Timeline

| Week | Tasks |
|------|-------|
| 1 | Train/implement PagPassGPT model |
| 2-3 | Implement API + Worker + Pipeline |
| 4 | Docker deployment + RabbitMQ integration |
| 5 | Testing & validation |
| 6-7 | Performance benchmarking |
| 8 | Thesis documentation |

---

**Document Version**: 1.0
**Last Updated**: 2025-01-01
**Context**: Bachelor Thesis Implementation Plan
