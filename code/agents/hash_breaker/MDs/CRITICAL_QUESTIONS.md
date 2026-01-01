# 10 Critical Questions for Hash Breaker Microservice Finalization

## Overview

Based on comprehensive research and architectural analysis, these 10 questions must be answered **before implementation begins**. Each question addresses a critical architectural decision that will impact performance, scalability, security, and operational complexity.

---

## Question 1: Deployment Target & Infrastructure

### What is your target deployment environment?

**Context**: The choice between single-node and multi-node deployment impacts technology choices, complexity, and cost.

**Options**:

| Approach | Best For | Complexity | Cost |
|----------|----------|------------|------|
| **A. Single-Node** | Development, small-scale testing | Low | $100-500/month (single GPU instance) |
| **B. Multi-Node** | Production, high throughput | High | $1000-5000/month (cluster) |
| **C. Hybrid** | Elastic workloads | Medium | Variable |

**Decision Drivers**:
- Expected concurrent jobs: ___ (e.g., 1-5 dev, 20-100 prod)
- Budget constraints: ___ per month
- GPU availability: Local GPUs? Cloud? Both?

**Recommendation**: Start with **Option A (Single-Node)** for MVP, add horizontal scaling later.

---

## Question 2: GPU Hardware Selection

### What GPU hardware will you use?

**Context**: Different GPUs offer dramatically different price-performance ratios.

**Benchmark Data** (RTX 4090 = baseline):

| GPU | Relative Speed | Cost (approx) | Value |
|-----|----------------|---------------|-------|
| RTX 4090 | 100% | $1,600 | ⭐⭐⭐⭐⭐ |
| RTX 4080 | 75% | $1,200 | ⭐⭐⭐⭐ |
| RTX 3090 | 60% | $800 (used) | ⭐⭐⭐⭐⭐ |
| RTX 4070 Ti | 45% | $800 | ⭐⭐⭐ |
| A100 (cloud) | 120% | $3-5/hour | ⭐⭐ |

**Questions**:
- Local hardware or cloud-based (AWS/Azure/GCP)?
- If local: Budget? Power constraints?
- If cloud: Spot instances or reserved?

**Recommendation**: **RTX 3090 (used)** or **RTX 4070 Ti** for best value. Cloud: **RunPod/Vast.ai** ($0.50-1/hour).

---

## Question 3: Message Broker Selection

### Which message broker for task distribution?

**Context**: Broker choice impacts reliability, complexity, and operational overhead.

**Options**:

| Broker | Pros | Cons | Best For |
|--------|------|------|----------|
| **A. Redis** | Simple, fast, familiar | Limited durability | Single-node, dev/test |
| **B. RabbitMQ** | Reliable, mature, DLQ support | Complex setup | Multi-node production |
| **C. Kafka** | Highest throughput | Overkill for task queues | Very high scale |

**Decision Matrix**:

```
Single-Node (Dev)  → Redis (Simple)
Multi-Node (Prod)  → RabbitMQ (Reliable)
Massive Scale      → Kafka (Only if >10K jobs/hour)
```

**Recommendation**: **Redis for Phase 1 (MVP)**, **RabbitMQ for Phase 3 (Production)**.

---

## Question 4: Task Queue Framework

### Which task queue framework?

**Context**: Different frameworks offer different tradeoffs between features and simplicity.

**Comparison**:

| Feature | Dramatiq | Celery | RQ |
|---------|----------|--------|-----|
| Reliability (defaults) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Simplicity | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Learning Curve | Low | High | Very Low |
| Async Support | Native | Limited | None |

**Key Differentiator**: Dramatiq's **auto-retry with exponential backoff** is default behavior (Celery: opt-in).

**Recommendation**: **Dramatiq** (best defaults, reliability-first design).

---

## Question 5: Authentication & Authorization

### How will you authenticate API users?

**Context**: Impacts rate limiting, quota management, and abuse prevention.

**Options**:

| Approach | Complexity | Security | Use Case |
|----------|------------|----------|----------|
| **A. No Auth** | None | ❌ Low | Internal/private deployment |
| **B. API Key** | Low | ✅ Medium | B2B integration |
| **C. JWT/OAuth** | High | ✅✅ High | Public-facing service |
| **D. mTLS** | Very High | ✅✅✅ Very High | Enterprise |

**Recommendation**:
- **Phase 1 (MVP)**: No auth or simple API key
- **Phase 3 (Prod)**: JWT + Rate limiting per user

**Question**: Who are your users? (Internal team, external customers, public?)

---

## Question 6: FLA Training Strategy

### Will you train FLA from scratch or use pre-trained models?

**Context**: Training from scratch takes 24-48 hours (CPU) or 4-8 hours (GPU).

**Options**:

| Approach | Time | Resources | Customization |
|----------|------|-----------|---------------|
| **A. Train from scratch** | 24-48h | GPU required | Full control |
| **B. Use pre-trained** | 0h | Download | General purpose only |
| **C. Fine-tune pre-trained** | 2-4h | GPU | Policy-specific |

**Pre-trained Model Availability**:
- RockYou-trained FLA models: Check GitHub/HuggingFace
- If unavailable: Must train from scratch

**Question**: Do you have GPU access for training? If yes: Train from scratch. If no: Find pre-trained or use cloud GPU for 8-hour training session.

**Recommendation**: **Train from scratch** on RockYou + fine-tune for your specific password policies.

---

## Question 7: Result Storage & Retention

### How long should cracked passwords be stored?

**Context**: Security vs. usability tradeoff.

**Options**:

| Retention | Pros | Cons |
|-----------|------|------|
| **Immediate (return in response only)** | Most secure | User might miss result |
| **1 hour** | Balanced | Small risk window |
| **24 hours** | User-friendly | Larger attack surface |
| **Permanent** | Convenient | ❌ Security nightmare |

**Recommendation**: **TTL-based storage in Redis** (auto-expire after 1-24 hours). Results returned in API response + available via `/status` endpoint for TTL duration.

**Question**: What is your security requirement? (HIPAA, SOC2, internal policy?)

---

## Question 8: Rate Limiting Strategy

### What are your rate limiting requirements?

**Context**: Prevents abuse, ensures fair resource allocation.

**Dimensions**:

| Metric | Suggested Limit | Rationale |
|--------|-----------------|-----------|
| Requests/hour | 100-1000 | Prevents API abuse |
| Concurrent jobs | 1-20 | Limits resource consumption |
| Hash types/user | Unrestricted | Or restrict premium hash types (bcrypt) |

**Question**: What is your target usage?
- Personal tool: 1 user, 1 concurrent job
- Team tool: 5-10 users, 5 concurrent jobs
- Service: 100+ users, 20+ concurrent jobs

**Recommendation**: Start with **100 requests/hour, 1 concurrent job** (anonymous). Add authenticated tiers later.

---

## Question 9: Monitoring & Observability

### What level of monitoring do you need?

**Context**: Impacts debugging, capacity planning, and incident response.

**Tiers**:

| Tier | Components | Example |
|------|------------|---------|
| **Basic** | Logs + metrics | Prometheus + Grafana |
| **Advanced** | + Tracing + Alerts | Jaeger + PagerDuty |
| **Enterprise** | + AIOps | ELK + Datadog + custom dashboards |

**Must-Have Metrics**:
- Job success rate (by hash type)
- Average job duration (p50, p95, p99)
- GPU utilization (%)
- Queue depth
- Worker health

**Recommendation**: Start with **Basic tier** (Prometheus + Grafana). Add tracing if debugging distributed issues.

**Question**: Who will respond to alerts? (Do you have on-call resources?)

---

## Question 10: Compliance & Legal

### What is your intended use case and compliance requirement?

**Context**: Hash cracking tools exist in a legal gray area. Documentation and access controls are critical.

**Use Cases** (Check all that apply):

- [ ] **Personal password recovery** (my own accounts only)
- [ ] **Security auditing** (red teaming, pentesting with authorization)
- [ ] **Password policy validation** (internal enterprise)
- [ ] **Academic research** (IRB-approved, institutional review)
- [ ] **Commercial service** (B2B password auditing SaaS)

**Legal Protections Needed**:

1. **Terms of Service** (explicitly forbid unauthorized use)
2. **Access logging** (audit trail of all jobs)
3. **Rate limiting** (prevent bulk abuse)
4. **Input validation** (reject obvious non-auditing use)
5. **User verification** (B2B: verify business entity)

**Question**: What is your **primary** use case? This determines the level of access control and documentation required.

---

## Summary Checklist

Before starting implementation, ensure you have answers for:

- [ ] **Q1**: Deployment target (single-node vs multi-node)
- [ ] **Q2**: GPU hardware selection
- [ ] **Q3**: Message broker (Redis vs RabbitMQ)
- [ ] **Q4**: Task queue framework (Dramatiq recommended)
- [ ] **Q5**: Authentication strategy (none/API key/JWT)
- [ ] **Q6**: FLA training approach (from scratch vs pre-trained)
- [ ] **Q7**: Result retention policy (TTL duration)
- [ ] **Q8**: Rate limits (requests/hour, concurrent jobs)
- [ ] **Q9**: Monitoring tier (Basic/Advanced/Enterprise)
- [ ] **Q10**: Compliance & use case documentation

---

## Recommended Starting Configuration (MVP)

Based on common requirements for a hash cracking microservice:

```yaml
Deployment: Single-node (Docker Compose)
GPU: RTX 3090 (local) or RunPod cloud ($0.70/hour)
Message Broker: Redis
Task Queue: Dramatiq
Authentication: None (internal/private)
FLA Training: Train from scratch (8 hours on GPU)
Result Retention: 1 hour TTL
Rate Limiting: 100 req/hour, 1 concurrent job
Monitoring: Basic (Prometheus metrics endpoint)
Compliance: Internal security auditing with authorization
```

**Total Setup Time**: 2-3 weeks (including FLA training)
**Estimated Cost**: $500-1000 (hardware) or $50-100 (cloud GPU rental for training)

---

## Next Steps

Once you answer these 10 questions, I will:

1. **Finalize the architecture** (update technical specs based on your choices)
2. **Create implementation guide** (step-by-step development roadmap)
3. **Generate Docker configs** (docker-compose.yml, Dockerfile)
4. **Write deployment scripts** (CI/CD, monitoring setup)
5. **Create training pipeline** (automated FLA training workflow)

**Please provide your answers to each question, and I'll customize the implementation plan accordingly.**

---

**Document Version**: 1.0
**Last Updated**: 2025-01-01
**Status**: Awaiting User Input
