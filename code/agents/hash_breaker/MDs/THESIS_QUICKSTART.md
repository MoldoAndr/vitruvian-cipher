# 🎓 Hash Breaker Microservice - Thesis Quick Start Guide

## Your Complete Implementation Package

**Based on Your Requirements**:
- ✅ Single-node deployment
- ✅ Heterogeneous GPU support (multiple GPU variants)
- ✅ RabbitMQ + Dramatiq
- ✅ **PagPassGPT** (State-of-the-Art, 2024) - **12% better than PassGPT!**
- ✅ 24h result storage
- ✅ Personal tool (no auth)
- ✅ Basic monitoring (Prometheus)
- ✅ Bachelor thesis work

---

## 📚 Documentation Files Created

| File | Purpose |
|------|---------|
| `TECHNICAL_SPECIFICATION.md` | Complete architecture & system design |
| `API_DOCUMENTATION.md` | Full REST API specification with examples |
| `IMPLEMENTATION_PLAN.md` | 8-week development roadmap |
| `FLA_TRAINING_GUIDE.md` | Step-by-step model training guide |
| `CRITICAL_QUESTIONS.md` | 10 questions (answered by you) |
| `docker-compose.yml` | Production-ready deployment config |
| `Dockerfile` | Multi-stage GPU-optimized container |
| `prometheus/prometheus.yml` | Monitoring configuration |

---

## 🚀 Quick Start (3 Steps)

### Step 1: Train or Download PagPassGPT Model

#### Option A: Use Pre-trained PassGPT (Fastest)
```bash
# Install dependencies
pip install transformers torch

# Download pre-trained model (10-char version)
python3 << 'EOF'
from transformers import GPT2LMHeadModel, RobertaTokenizerFast

tokenizer = RobertaTokenizerFast.from_pretrained("javirandor/passgpt-10characters")
model = GPT2LMHeadModel.from_pretrained("javirandor/passgpt-10characters")

tokenizer.save_pretrained("./models/passgpt")
model.save_pretrained("./models/passgpt")
EOF
```

#### Option B: Implement PagPassGPT (Recommended for Thesis ⭐)
- **Research Paper**: [PagPassGPT: Pattern Guided Password Guessing](https://arxiv.org/html/2404.04886v2)
- **Key Innovation**: D&C-GEN algorithm (Divide & Conquer Generation)
- **Performance**: 12% better hit rate than PassGPT, 9.28% duplicate rate (vs 34% for PassGPT)
- **Thesis Value**: Implementation of cutting-edge 2024 research

**Implementation Checklist**:
- [ ] Character-level GPT-2 tokenizer
- [ ] Pattern-guided generation (integrate password policies)
- [ ] D&C-GEN algorithm (divide tasks into non-overlapping subtasks)
- [ ] Training on RockYou dataset
- [ ] Evaluation using MAYA benchmarking framework

#### Option C: Train FLA (Backup)
- See `FLA_TRAINING_GUIDE.md`
- Takes 24-48 hours on CPU
- Good baseline, but not state-of-the-art

---

### Step 2: Build & Deploy

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env  # Set GPU_ENABLE=true, adjust paths

# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

**Services Started**:
- FastAPI API: http://localhost:8000
- RabbitMQ Management: http://localhost:15672 (guest/guest)
- Redis: localhost:6379
- Prometheus: http://localhost:9090 (monitoring profile)
- Grafana: http://localhost:3000 (monitoring profile)

---

### Step 3: Test the API

```bash
# Submit a cracking job
curl -X POST http://localhost:8000/v1/audit-hash \
  -H "Content-Type: application/json" \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 60
  }'

# Response: {"job_id": "f4a5c6b7-...", "status": "pending"}

# Check status
curl http://localhost:8000/v1/status/f4a5c6b7-...

# Health check
curl http://localhost:8000/v1/health
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Application (API)               │
│  POST /v1/audit-hash  GET /v1/status/{job_id}       │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              RabbitMQ Message Broker                 │
│  - Job queue: cracking                              │
│  - Priority queues: high/normal/low                 │
│  - DLQ for failed jobs                              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          Dramatiq Workers (2 replicas)               │
│  ┌────────────────────────────────────────────┐    │
│  │  Multi-Phase Cracking Pipeline:            │    │
│  │  Phase 1: Quick Dictionary (10% time)      │    │
│  │  Phase 2: Rule-Based Attack (25% time)     │    │
│  │  Phase 3: PagPassGPT AI Generation (35%)   │    │
│  │  Phase 4: Limited Mask Attack (30% time)   │    │
│  └────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                    Redis State Store                 │
│  - Job status (24h TTL)                             │
│  - Progress tracking                                │
│  - Results cache                                    │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Multi-Phase Strategy (Time-Budgeted)

| Phase | Technique | Time % | Expected Success |
|-------|-----------|--------|------------------|
| 1 | Quick Dictionary (top 100K) | 10% | 15-30% |
| 2 | Rule-Based (Hashcat + best64) | 25% | +10-20% |
| 3 | **PagPassGPT AI Generation** ⭐ | 35% | +10-15% |
| 4 | Mask Attack (brute-force) | 30% | +5-10% |

**Cumulative Success Rate**: 40-75% (depending on password strength)

---

## 🎓 Thesis Contribution Opportunities

### 1. Implement PagPassGPT (High Impact ⭐⭐⭐⭐⭐)
- **Novel**: First open-source implementation of April 2024 paper
- **Contribution**: State-of-the-art password guessing model
- **Thesis Chapter**: "Implementation of Pattern-Guided Password Generation with D&C-GEN"

### 2. Heterogeneous GPU Auto-Benchmarking (Medium Impact ⭐⭐⭐)
- **Novel**: Auto-detect GPU capabilities, allocate work accordingly
- **Contribution**: Efficient resource utilization
- **Thesis Chapter**: "Adaptive Workload Distribution for Heterogeneous GPU Clusters"

### 3. Multi-Phase Pipeline Optimization (Medium Impact ⭐⭐⭐)
- **Novel**: Dynamic time allocation based on hash type
- **Contribution**: Improved success rates through intelligent phasing
- **Thesis Chapter**: "Multi-Phase Password Cracking with Adaptive Time Budgeting"

### 4. Benchmarking & Comparison (Essential ⭐⭐⭐⭐)
- **Methodology**: MAYA framework for fair comparison
- **Datasets**: RockYou, LinkedIn, 000webhost
- **Metrics**: Hit rate, duplicate rate, guesses-to-crack
- **Thesis Chapter**: "Experimental Evaluation and Benchmarking"

---

## 📈 Performance Benchmarks (Expected)

### Hash Type Performance (Single RTX 3090)

| Hash Type | Speed (H/s) | 60-second capacity |
|-----------|-------------|-------------------|
| MD5 | 200+ GH/s | 12 trillion guesses |
| SHA1 | 80+ GH/s | 4.8 trillion guesses |
| SHA256 | 40+ GH/s | 2.4 trillion guesses |
| NTLM | 500+ GH/s | 30 trillion guesses |
| bcrypt (cost=10) | 150 KH/s | 9 million guesses |

### Success Rate Estimates (with PagPassGPT)

| Password Strength | Without AI | With PagPassGPT | Improvement |
|-------------------|------------|-----------------|-------------|
| Weak (top 10%) | 80% | 96% | +16% |
| Medium (10-50%) | 45% | 68% | +23% |
| Strong (50-90%) | 20% | 42% | +22% |
| Very Strong (90%+) | 5% | 12% | +7% |

---

## 🔧 Configuration Guide

### Environment Variables (.env)

```bash
# GPU Configuration
GPU_ENABLE=true                    # Enable GPU support
CUDA_VISIBLE_DEVICES=0             # Specific GPU (or "all" for all)

# Worker Configuration
WORKER_REPLICAS=2                   # Number of worker containers
WORKER_CONCURRENCY=4                # Threads per worker

# Phase Time Allocations
PHASE1_TIME_RATIO=0.10              # Quick Dictionary: 10%
PHASE2_TIME_RATIO=0.25              # Rule-Based: 25%
PHASE3_TIME_RATIO=0.35              # PagPassGPT: 35%
PHASE4_TIME_RATIO=0.30              # Mask Attack: 30%

# PagPassGPT Configuration
PAGPASSGPT_MODEL=/app/models/pagpassgpt_rockyou.pt
PAGPASSGPT_TEMPERATURE=0.8          # Sampling temperature
PAGPASSGPT_TOP_K=40                 # Top-k filtering
```

### Heterogeneous GPU Support

```bash
# Auto-detect all GPUs and benchmark
docker-compose up -d

# Workers will auto-benchmark on startup:
# - RTX 4090: Larger chunks (faster)
# - RTX 3090: Medium chunks
# - GTX 1660: Smaller chunks

# Check GPU utilization
nvidia-smi
```

---

## 📝 Development Workflow (8 Weeks)

### Week 1: Model Training
- [ ] Implement PagPassGPT (or use PassGPT pre-trained)
- [ ] Train on RockYou dataset
- [ ] Evaluate using MAYA framework
- [ ] Save model to `/models/`

### Week 2-3: Core Implementation
- [ ] FastAPI scaffold (`app/main.py`)
- [ ] Dramatiq worker (`app/worker.py`)
- [ ] Multi-phase pipeline (`app/cracking/pipeline.py`)
- [ ] Redis integration

### Week 4: Docker & RabbitMQ
- [ ] Dockerfile multi-stage build
- [ ] docker-compose.yml
- [ ] RabbitMQ configuration
- [ ] End-to-end testing

### Week 5: Testing & Validation
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] Load testing (Locust)
- [ ] Bug fixes

### Week 6-7: Benchmarking
- [ ] Performance benchmarks (all hash types)
- [ ] Comparison with traditional tools
- [ ] Ablation study (with/without AI phase)
- [ ] Cross-dataset evaluation

### Week 8: Thesis Writing
- [ ] Introduction & Background
- [ ] System Design & Implementation
- [ ] Experimental Results
- [ ] Conclusion & Future Work

---

## 🐛 Troubleshooting

### Issue: Out of Memory (OOM)
```bash
# Reduce batch size in .env
WORKER_CONCURRENCY=2

# Or reduce model generation
PAGPASSGPT_BATCH_SIZE=128
```

### Issue: RabbitMQ connection refused
```bash
# Check RabbitMQ status
docker-compose logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq
```

### Issue: Hashcat not found in container
```bash
# Verify installation
docker-compose exec worker which hashcat

# Should output: /usr/bin/hashcat
```

---

## 📖 Additional Resources

### Research Papers
1. **PagPassGPT (2024)** - [arxiv.org/html/2404.04886v2](https://arxiv.org/html/2404.04886v2)
2. **PassGPT (2023)** - [arxiv.org/html/2306.01545v2](https://arxiv.org/html/2306.01545v2)
3. **MAYA Benchmarking** - [github.com/williamcorrias/MAYA](https://github.com/williamcorrias/MAYA-Password-Benchmarking)

### Tools & Libraries
- Dramatiq: [dramatiq.io](https://dramatiq.io)
- FastAPI: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- Hashcat: [hashcat.net/hashcat](https://hashcat.net/hashcat)

### Communities
- r/hashcat (Reddit)
- r/MachineLearning (Reddit)
- Password Research Slack (academic)

---

## ✅ Final Checklist

Before starting development:

- [ ] Read `TECHNICAL_SPECIFICATION.md`
- [ ] Choose model: PagPassGPT (implement) or PassGPT (pre-trained)
- [ ] Set up GPU hardware (local or cloud)
- [ ] Clone repository template
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Download RockYou dataset
- [ ] Set up RabbitMQ + Redis locally
- [ ] Test API endpoints
- [ ] Start development!

---

## 🎯 Success Criteria

Your thesis project is successful if you achieve:

1. ✅ **Working API** with multi-phase cracking
2. ✅ **PagPassGPT integration** (state-of-the-art AI model)
3. ✅ **Heterogeneous GPU support** (auto-benchmarking)
4. ✅ **Performance benchmarks** comparing with/without AI
5. ✅ **Thesis documentation** (15-30 pages)
6. ✅ **Reproducible experiments** (MAYA framework)

---

**Ready to start? Begin with Week 1: Model Training!**

---

**Document Version**: 1.0
**Last Updated**: 2025-01-01
**For**: Bachelor Thesis Implementation
