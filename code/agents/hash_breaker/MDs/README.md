# Hash Cracker Microservice

A lightweight, containerized hash cracking microservice designed to be consumed by other services via Redis. No REST API, no NGINX, no heavy infrastructure — just Redis + Worker(s).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR ORCHESTRATOR SERVICE                │
│            (submits jobs, receives results)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
               Redis LPUSH/BRPOPLPUSH + PubSub
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  HASH CRACKER MICROSERVICE                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Cracking Pipeline                      │    │
│  │  Phase 1: Dictionary Attack (common passwords)      │    │
│  │  Phase 2: Rule-Based Attack (transformations)       │    │
│  │  Phase 3: AI Generation (PassGAN/PCFG)              │    │
│  │  Phase 4: Mask Attack (pattern brute-force)         │    │
│  └─────────────────────────────────────────────────────┘    │
│  Tools: Hashcat (GPU), John the Ripper (CPU)                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU + Drivers (optional, for GPU acceleration)
- NVIDIA Container Toolkit (for GPU workers)

### Start the Service

```bash
# Start Redis + Worker
docker compose up -d

# Check logs
docker compose logs -f worker-gpu
```

### Submit a Job (from another service)

```python
from hash_cracker.queue import JobQueue, ResultSubscriber
from hash_cracker.state import StateManager

queue = JobQueue()
state = StateManager()

job_id = queue.submit_job(
    hash_value="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    hash_type_id=1400,  # SHA256
    timeout=60
)
state.create_job(
    job_id=job_id,
    hash_value="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    hash_type_id=1400,
    timeout=60
)

subscriber = ResultSubscriber()
result = subscriber.wait_for_result(job_id, timeout=120)
print(f"Result: {result}")
```

### Direct Library Usage (no Redis)

```python
from hash_cracker import crack_hash

result = crack_hash(
    hash_value="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    hash_type_id=1400,  # SHA256
    timeout=60
)

if result.success:
    print(f"Password: {result.password}")
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `WORKER_ID` | `worker-1` | Unique worker identifier |
| `LOG_LEVEL` | `INFO` | Logging level |
| `WORDLIST_DIR` | `/data/wordlists` | Path to wordlists |
| `RULES_DIR` | `/data/rules` | Path to rule files |
| `MODELS_DIR` | `/data/models` | Path to AI models |
| `JOBS_PENDING_QUEUE` | `jobs:pending` | Pending jobs list |
| `JOBS_PROCESSING_QUEUE` | `jobs:processing` | In-flight jobs list |
| `JOBS_RESULTS_CHANNEL` | `jobs:results` | Results pub/sub channel |
| `JOBS_DEADLETTER_QUEUE` | `jobs:deadletter` | Invalid job payloads |
| `JOB_LEASE_BUFFER_SECONDS` | `30` | Extra lease time for in-flight jobs |
| `WORKER_HEARTBEAT_INTERVAL` | `10` | Worker heartbeat interval (seconds) |
| `STRICT_HASH_VALIDATION` | `true` | Validate hash format for known modes |

## Hash Types (Hashcat modes)

| Mode | Type |
|------|------|
| 0 | MD5 |
| 100 | SHA1 |
| 1000 | NTLM |
| 1400 | SHA256 |
| 1700 | SHA512 |
| 1800 | sha512crypt |
| 3200 | bcrypt |

## Project Structure

```
hash_cracker/
├── __init__.py
├── config.py          # Configuration
├── pipeline.py        # Main cracking orchestration
├── queue.py           # Redis job queue
├── state.py           # Job state management
├── worker.py          # Worker entry point
├── phases/            # Cracking phases
│   ├── dictionary.py  # Phase 1: Dictionary attack
│   ├── rules.py       # Phase 2: Rule-based attack
│   ├── ai_generator.py # Phase 3: AI candidates
│   └── mask.py        # Phase 4: Mask attack
└── tools/             # Tool wrappers
    ├── hashcat.py
    └── john.py
```

## Data Requirements

Place your data in the `data/` directory:

```
data/
├── wordlists/
│   ├── rockyou.txt
│   ├── top1000.txt
│   └── ...
├── rules/
│   ├── best64.rule
│   └── ...
└── models/
    └── passgan/
```

## Hardware Requirements

**Minimum (CPU-only):**
- 4 CPU cores
- 8 GB RAM

**Recommended (GPU):**
- NVIDIA GPU with 8GB+ VRAM
- 16 GB RAM

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run worker locally
python -m hash_cracker.worker

# Run example
python examples/client_example.py
```

## What Was Removed (vs. full version)

- ❌ FastAPI REST API
- ❌ NGINX reverse proxy
- ❌ RabbitMQ message broker
- ❌ Celery task queue
- ❌ Prometheus monitoring
- ❌ Grafana dashboards
- ❌ API authentication/rate limiting

## What Remains

- ✅ Redis (job queue + state store)
- ✅ GPU/CPU Workers
- ✅ Multi-phase cracking pipeline
- ✅ Hashcat + John the Ripper
- ✅ AI candidate generation (PassGAN/PCFG)
- ✅ Docker containerization

## Reliability Notes

- Jobs are moved to a processing list when claimed; a lease key prevents duplicate work.
- Workers emit heartbeats and refresh job leases while running.
- On restart, workers can requeue orphaned jobs without a live lease.

## License

MIT License
