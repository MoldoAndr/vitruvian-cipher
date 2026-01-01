# Hash Breaker Microservice - Technical Specification

## Executive Summary

The Hash Breaker Microservice is a distributed, containerized password hash auditing system designed for security testing and password strength assessment. The service exposes RESTful API endpoints for submitting hash cracking jobs, querying job status, and retrieving results. It implements a multi-phase cracking strategy combining traditional tools (Hashcat, John the Ripper) with AI-driven password generation using FLA (Fast, Lean, and Accurate) LSTM-based neural networks.

**Key Design Decision**: Replacing PassGAN with **FLA (LSTM-based)** due to:
- 2x better performance on cross-community datasets
- Lightweight architecture (model size: hundreds of KB vs GBs)
- Trainable on commodity hardware (CPU-compatible training)
- Proven competitive performance with PassGPT/VGPT2
- Transfer learning capabilities for policy-specific fine-tuning

---

## 1. System Overview

### 1.1 Purpose

Provide a scalable, efficient hash cracking service for:
- Password security auditing (red teaming)
- Password policy validation
- Recovery of lost passwords (authorized use only)
- Security research and testing

### 1.2 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
│  - POST /audit-hash    - GET /status/{job_id}               │
│  - GET /health         - GET /metrics                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Task Queue (Redis/RabbitMQ)                │
│  - Job distribution  - Priority queuing  - Fault tolerance  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Cracking Workers (Celery/Dramatiq)              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Multi-Phase Cracking Pipeline:                      │  │
│  │  1. Quick Dictionary (top 100K passwords)            │  │
│  │  2. Rule-Based Attack (Hashcat + best64.rules)       │  │
│  │  3. AI Generation (FLA LSTM model)                   │  │
│  │  4. Mask Attack (time-limited brute-force)           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   State Store (Redis)                        │
│  - Job status        - Progress tracking  - Results cache   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **API Framework** | FastAPI | Async support, automatic OpenAPI docs, high performance |
| **Task Queue** | Dramatiq + RabbitMQ | Superior defaults, auto-retry with exponential backoff |
| **State Store** | Redis | Sub-millisecond latency, ideal for real-time job tracking |
| **Workers** | Dramatiq | Thread-based, memory-efficient, reliable by default |
| **Cracking Tools** | Hashcat (primary), John the Ripper (backup) | GPU-accelerated, industry standard |
| **AI Model** | FLA (LSTM) | Lightweight, trainable, state-of-the-art performance |
| **Container** | Docker + Docker Compose | Consistent deployment, easy scaling |

---

## 2. Multi-Phase Cracking Strategy

### Phase 1: Quick Dictionary Attack (0-15% time budget)

**Goal**: Capture low-hanging fruit (common passwords)

**Implementation**:
```bash
hashcat -m {hash_type} hash_file.txt /data/wordlists/top100k.txt \
  --potfile-disable --quiet
```

**Time Budget**: 10% of total timeout
**Wordlist**: Top 100,000 from RockYou (most common passwords)
**Expected Success Rate**: 15-30% for weak passwords

---

### Phase 2: Rule-Based Attack (15-40% time budget)

**Goal**: Apply intelligent mutations to dictionary words

**Implementation**:
```bash
hashcat -m {hash_type} hash_file.txt /data/wordlists/rockyou.txt \
  -r /data/rules/best64.rule --potfile-disable --quiet
```

**Time Budget**: 25% of total timeout
**Wordlist**: Full RockYou (32M passwords, filtered to max length)
**Rules**: best64.rule (64 most effective mutation rules)
**Expected Success Rate**: Additional 10-20% (cumulative: 25-50%)

---

### Phase 3: AI-Generated Candidates (40-75% time budget) ⭐

**Goal**: Generate novel, human-like passwords using FLA model

**Implementation**:
```python
# Generate candidates on-the-fly, pipe to hashcat
python /app/fla_generator.py --num 5000000 --temperature 0.8 | \
  hashcat -m {hash_type} hash_file.txt --stdin --potfile-disable --quiet
```

**Model**: FLA (3 LSTM layers × 200 units, 2 Dense layers × 1000 units)
**Generation Strategy**:
- Temperature sampling (0.7-0.9) for diversity
- Top-k sampling (k=40) to filter low-probability tokens
- Batch generation with streaming to avoid disk I/O

**Time Budget**: 35% of total timeout
**Candidates Generated**: 5-50 million (time-dependent)
**Expected Success Rate**: Additional 10-15% (cumulative: 35-65%)

---

### Phase 4: Limited Mask Attack (75-100% time budget)

**Goal**: Systematic brute-force of simple patterns

**Implementation**:
```bash
# Common masks for 8-character passwords
hashcat -m {hash_type} hash_file.txt -a 3 \
  ?l?l?l?l?l?l?l?l --increment --potfile-disable --quiet
```

**Masks** (in priority order):
1. `?l?l?l?l?l?l?l?l` (8 lowercase)
2. `?u?l?l?l?l?l?l?l` (capital + 7 lowercase)
3. `?l?l?l?l?l?l?l?d` (7 lowercase + 1 digit)
4. `?a?a?a?a?a?a?a` (8 printable ASCII)

**Time Budget**: Remaining time (25%)
**Expected Success Rate**: Additional 5-10% (cumulative: 40-75%)

---

## 3. API Endpoints Specification

### 3.1 POST /audit-hash

Submit a new hash cracking job.

**Request**:
```json
{
  "hash": "a87ff679a2f3e71d9181a67b7542122c",
  "hash_type_id": 0,
  "timeout_seconds": 60,
  "priority": "normal"
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "pending",
  "estimated_completion": "2025-01-01T12:01:00Z"
}
```

**Validation Rules**:
- `hash`: Non-empty string, format validated by hash_type_id
- `hash_type_id`: Integer 0-974 (valid Hashcat hash modes)
- `timeout_seconds`: 10-3600 (enforced max: 1 hour)
- `priority`: "low" | "normal" | "high" (default: "normal")

---

### 3.2 GET /status/{job_id}

Query the status of a submitted job.

**Response** (200 OK):
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "running",
  "progress": 45,
  "current_phase": "Phase 3: AI Candidate Generation",
  "time_remaining": 33,
  "submitted_at": "2025-01-01T12:00:00Z",
  "started_at": "2025-01-01T12:00:01Z",
  "result": null
}
```

**Status Values**:
- `pending`: Queued, not yet started
- `running`: Currently processing
- `success`: Password cracked, result available
- `failed`: Timeout or password not found
- `cancelled`: Job cancelled by client

**Success Response** (status=success):
```json
{
  "job_id": "...",
  "status": "success",
  "result": "password123",
  "cracked_at": "2025-01-01T12:00:15Z",
  "phase": "Phase 2: Rule-Based Attack",
  "attempts": 1523490
}
```

**Failed Response** (status=failed):
```json
{
  "job_id": "...",
  "status": "failed",
  "reason": "Timeout exceeded",
  "attempts": 5820394,
  "last_phase": "Phase 4: Limited Mask Attack"
}
```

---

### 3.3 POST /jobs/{job_id}/cancel

Cancel a running or pending job.

**Response** (200 OK):
```json
{
  "job_id": "...",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

### 3.4 GET /health

Health check endpoint for load balancers/orchestration.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "workers": {
    "total": 4,
    "active": 3,
    "idle": 1
  },
  "queue_depth": 12
}
```

---

### 3.5 GET /metrics

Prometheus-compatible metrics endpoint.

**Response** (200 OK - text/plain):
```
# HELP hash_breaker_jobs_total Total number of jobs processed
# TYPE hash_breaker_jobs_total counter
hash_breaker_jobs_total{status="success"} 1523
hash_breaker_jobs_total{status="failed"} 847
hash_breaker_jobs_total{status="cancelled"} 23

# HELP hash_breaker_jobs_current Current number of jobs by status
# TYPE hash_breaker_jobs_current gauge
hash_breaker_jobs_current{status="running"} 3
hash_breaker_jobs_current{status="pending"} 12

# HELP hash_breaker_phase_duration_seconds Phase execution duration
# TYPE hash_breaker_phase_duration_seconds histogram
hash_breaker_phase_duration_seconds{phase="dictionary",le="0.1"} 450
hash_breaker_phase_duration_seconds{phase="dictionary",le="1"} 1523
...
```

---

## 4. FLA Model Architecture & Training

### 4.1 Model Architecture

```python
# FLA Architecture Specification
model = Sequential([
    Input(shape=(max_password_length, vocab_size)),

    # LSTM layers (character-level processing)
    LSTM(200, return_sequences=True),
    LSTM(200, return_sequences=True),
    LSTM(200, return_sequences=False),

    # Dense layers (classification)
    Dense(1000, activation='relu'),
    Dense(1000, activation='relu'),

    # Output layer (character prediction)
    Dense(vocab_size, activation='softmax')
])
```

**Key Specifications**:
- **Input**: Character sequences (one-hot encoded, 95-character vocabulary)
- **Vocabulary**: lowercase (26) + uppercase (26) + digits (10) + special (33) = 95
- **Max Password Length**: 10-16 characters (configurable)
- **Output**: Probability distribution over vocabulary for next character
- **Total Parameters**: ~2-3M (trainable on CPU)

---

### 4.2 Training Pipeline

#### Data Preparation
```bash
# Download RockYou dataset (32M+ passwords)
wget https://datasets.seed/enwiki/RockYou.txt

# Preprocess
python scripts/preprocess.py \
  --input rockyou.txt \
  --output rockyou_processed.txt \
  --max-length 12 \
  --filter-ascii \
  --remove-duplicates

# Split train/test (80/20)
python scripts/split.py \
  --input rockyou_processed.txt \
  --train 0.8 \
  --test 0.2
```

#### Training Command
```bash
python scripts/train_fla.py \
  --train-data rockyou_train.txt \
  --test-data rockyou_test.txt \
  --vocab-size 95 \
  --max-length 12 \
  --batch-size 256 \
  --epochs 50 \
  --learning-rate 0.001 \
  --checkpoint-dir /models/checkpoints \
  --model-output /models/fla_rockyou_v1.h5
```

#### Training Requirements
| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16 GB |
| **GPU** | None | GTX 1660+ (optional) |
| **Storage** | 5 GB | 10 GB |
| **Training Time** | 24-48 hours (CPU) | 4-8 hours (GPU) |

---

### 4.3 Model Serving in Production

#### Generation Script
```python
#!/usr/bin/env python3
# fla_generator.py - Generate password candidates using trained FLA model

import argparse
import numpy as np
from tensorflow.keras.models import load_model

def generate_passwords(model, vocab, num_passwords, temperature=0.8, top_k=40):
    """Generate passwords using temperature sampling with top-k filtering."""
    passwords = []
    for _ in range(num_passwords):
        password = ""
        while True:
            # Get probabilities for next character
            probs = model.predict(password.encode())

            # Apply temperature
            probs = probs ** (1 / temperature)
            probs /= probs.sum()

            # Top-k filtering
            top_k_indices = np.argsort(probs)[-top_k:]
            top_k_probs = probs[top_k_indices]
            top_k_probs /= top_k_probs.sum()

            # Sample from top-k
            next_char_idx = np.random.choice(top_k_indices, p=top_k_probs)
            next_char = vocab[next_char_idx]

            if next_char == '<EOS>':  # End of sequence
                break
            password += next_char

        passwords.append(password)
        print(password)  # Stream to stdout

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='Path to trained model')
    parser.add_argument('--num', type=int, default=1000000, help='Number of passwords')
    parser.add_argument('--temperature', type=float, default=0.8)
    parser.add_argument('--top-k', type=int, default=40)
    args = parser.parse_args()

    model = load_model(args.model)
    vocab = load_vocabulary()  # Load from training

    generate_passwords(model, vocab, args.num, args.temperature, args.top_k)
```

#### Integration with Hashcat
```bash
# Stream generated passwords directly to hashcat
python /app/fla_generator.py \
  --model /models/fla_rockyou_v1.h5 \
  --num 5000000 \
  --temperature 0.8 \
  --top-k 40 | \
  hashcat -m 0 hash_file.txt --stdin --potfile-disable --quiet
```

---

## 5. Distributed Architecture

### 5.1 Single-Node Deployment (Development)

```
┌─────────────────────────────────────────────────────┐
│                Docker Container                     │
│                                                     │
│  ┌──────────┐  ┌─────────┐  ┌──────────────────┐  │
│  │  FastAPI │  │ Redis   │  │ Dramatiq Worker │  │
│  │  :8000   │  │ :6379   │  │ (4 threads)      │  │
│  └──────────┘  └─────────┘  └──────────────────┘  │
│       │              │              │              │
│       └──────────────┴──────────────┘              │
│              (internal network)                     │
└─────────────────────────────────────────────────────┘
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKER_CONCURRENCY=4
    depends_on:
      - redis
    volumes:
      - ./models:/app/models:ro
      - ./wordlists:/data/wordlists:ro

  worker:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - GPU_ENABLE=true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/app/models:ro
      - ./wordlists:/data/wordlists:ro

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

### 5.2 Multi-Node Deployment (Production)

```
┌─────────────────────────────────────────────────────────────┐
│                   Load Balancer (Nginx)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐        ┌───────▼────────┐
│ API Server 1   │        │ API Server 2   │
│ (FastAPI)      │  ...   │ (FastAPI)      │
└───────┬────────┘        └───────┬────────┘
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   RabbitMQ Cluster      │
        │   (3 nodes, mirrored)   │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐        ┌───────▼────────┐
│ Worker Node 1  │        │ Worker Node 2  │
│ 4× RTX 4090    │        │ 4× RTX 3090    │
└────────────────┘        └────────────────┘
```

**Key Scaling Considerations**:

1. **Horizontal API Scaling**: Run 2-4 API instances behind load balancer
2. **Worker Heterogeneity**: Different GPU types supported (auto-benchmarking)
3. **Queue Priority**: High/normal/low priority queues
4. **Fault Tolerance**: Dramatiq auto-retry with exponential backoff

---

## 6. Performance Benchmarks

### 6.1 Expected Performance (Single RTX 4090)

| Hash Type | Speed (H/s) | 60-second capacity |
|-----------|-------------|-------------------|
| **MD5** | 200+ GH/s | 12 trillion guesses |
| **SHA1** | 80+ GH/s | 4.8 trillion guesses |
| **SHA256** | 40+ GH/s | 2.4 trillion guesses |
| **NTLM** | 500+ GH/s | 30 trillion guesses |
| **bcrypt (cost=10)** | 150 KH/s | 9 million guesses |

### 6.2 Success Rate Estimates (RockYou-trained models)

| Password Strength | Phase 1 | Phase 2 | Phase 3 (FLA) | Phase 4 | Total |
|-------------------|---------|---------|---------------|---------|-------|
| **Weak** (top 10%) | 85% | 10% | 3% | 1% | 99% |
| **Medium** (10-50%) | 15% | 35% | 25% | 10% | 85% |
| **Strong** (50-90%) | 2% | 8% | 30% | 15% | 55% |
| **Very Strong** (90%+) | 0% | 1% | 10% | 5% | 16% |

*Note: Percentages are cumulative across phases*

---

## 7. Security & Ethical Considerations

### 7.1 Usage Policy

**Authorized Use Cases**:
- ✅ Security auditing of your own systems
- ✅ Password policy validation (red teaming)
- ✅ Recovery of lost passwords (you own the account)
- ✅ Academic security research (IRB-approved)

**Unauthorized Use Cases**:
- ❌ Attacking systems without permission
- ❌ Cracking passwords without authorization
- ❌ Malicious cybersecurity activities

### 7.2 Security Measures

1. **Rate Limiting**: Max 100 requests/hour per IP (configurable)
2. **Job Prioritization**: Authenticated users only for high-priority jobs
3. **Audit Logging**: All jobs logged with IP, timestamp, hash_type
4. **Result Expiry**: Results auto-delete after 24 hours
5. **Input Validation**: Strict hash format validation

### 7.3 API Authentication (Optional)

```python
# JWT-based authentication for production deployments
@app.post("/audit-hash", dependencies=[Depends(verify_token)])
async def audit_hash(request: HashAuditRequest, user_id: str = Depends(get_user)):
    # Check user quota
    if not await check_user_quota(user_id):
        raise HTTPException(429, "Quota exceeded")

    # Submit job with user_id for tracking
    job_id = await submit_job(request, user_id)
    return {"job_id": job_id}
```

---

## 8. Monitoring & Observability

### 8.1 Metrics to Track

```python
# Key metrics (Prometheus format)
hash_breaker_jobs_total{status}              # Total jobs by status
hash_breaker_jobs_duration_seconds{quantile}  # Job duration (p50, p95, p99)
hash_breaker_phase_duration_seconds{phase}   # Per-phase duration
hash_breaker_guesses_total{phase}            # Total guesses per phase
hash_breaker_success_rate{hash_type}         # Success rate by hash type
hash_breaker_gpu_utilization{worker_id}      # GPU % usage
hash_breaker_queue_depth{priority}           # Queue size by priority
```

### 8.2 Logging Strategy

```python
# Structured logging (JSON format)
logger.info("job_started", extra={
    "job_id": job_id,
    "hash_type": hash_type_id,
    "timeout": timeout_seconds,
    "timestamp": datetime.utcnow().isoformat()
})

logger.info("phase_completed", extra={
    "job_id": job_id,
    "phase": 2,
    "phase_name": "Rule-Based Attack",
    "duration_seconds": 12.3,
    "guesses": 1523490,
    "success": False
})
```

---

## 9. Development Roadmap

### Phase 1: MVP (Weeks 1-2)
- [ ] FastAPI scaffold with 3 endpoints (audit-hash, status, health)
- [ ] Dramatiq worker scaffold with Redis backend
- [ ] Phase 1 implementation (dictionary attack)
- [ ] Basic Docker containerization
- [ ] Integration tests

### Phase 2: Full Pipeline (Weeks 3-4)
- [ ] Phase 2 (rule-based attack)
- [ ] FLA model training script
- [ ] Phase 3 (AI generation)
- [ ] Phase 4 (mask attack)
- [ ] Comprehensive API tests

### Phase 3: Production Hardening (Weeks 5-6)
- [ ] Rate limiting middleware
- [ ] Prometheus metrics endpoint
- [ ] Audit logging
- [ ] Error handling and retry logic
- [ ] Multi-node deployment (docker-compose)

### Phase 4: Optimization (Weeks 7-8)
- [ ] GPU memory optimization
- [ ] FLA generation streaming
- [ ] Result caching layer
- [ ] Worker auto-scaling
- [ ] Performance benchmarking

---

## 10. Next Steps

Before implementation begins, answer the **10 Critical Questions** in the next document to finalize architectural decisions.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-01
**Author**: Hash Breaker Architecture Team
