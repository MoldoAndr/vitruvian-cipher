# Hash Breaker API Documentation

## Base URL

```
Development: http://localhost:8000
Production:  https://hash-breaker.example.com
API Version: v1
```

---

## Authentication

### Optional JWT Authentication (Production Deployments)

```bash
# Include bearer token in headers
curl -H "Authorization: Bearer <your_token>" \
  https://hash-breaker.example.com/v1/audit-hash
```

**Header Format**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Endpoints

### 1. Submit Hash Audit Job

Initiates a new hash cracking job with multi-phase attack strategy.

**Endpoint**: `POST /v1/audit-hash`

**Request Headers**:
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <token>"  // Optional
}
```

**Request Body**:
```json
{
  "hash": "a87ff679a2f3e71d9181a67b7542122c",
  "hash_type_id": 0,
  "timeout_seconds": 60,
  "priority": "normal"
}
```

**Request Parameters**:

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `hash` | string | ✅ Yes | Target hash to crack | Format depends on hash_type_id |
| `hash_type_id` | integer | ✅ Yes | Hashcat hash mode identifier | 0-974 (see Hash Modes table) |
| `timeout_seconds` | integer | ❌ No | Max execution time | 10-3600 (default: 60) |
| `priority` | string | ❌ No | Job priority | "low" \| "normal" \| "high" |

**Hash Type IDs (Common)**:

| ID | Algorithm | Example Hash |
|----|-----------|--------------|
| 0 | MD5 | `5d41402abc4b2a76b9719d911017c592` |
| 100 | SHA1 | `356a192b7913b04c54574d18c28d46e6395428ab` |
| 1400 | SHA256 | `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |
| 1000 | NTLM | `b4b9b02e6f09a9bd760f388b67351e2b` |
| 3200 | bcrypt | `$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy` |
| 1800 | SHA512 | `c7ad44cbad762a5da0a452f9e85e9f2e6b310a367b1dcb708a37c28dac8e4c73` |

**Success Response** (202 Accepted):
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "pending",
  "estimated_completion": "2025-01-01T12:01:00Z",
  "queue_position": 3
}
```

**Error Responses**:

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | `INVALID_HASH_FORMAT` | Hash format invalid for specified hash_type_id |
| 400 | `INVALID_HASH_TYPE` | hash_type_id not supported |
| 400 | `INVALID_TIMEOUT` | timeout_seconds outside range 10-3600 |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests (max 100/hour) |
| 500 | `INTERNAL_ERROR` | Server error, check logs |

**Error Response Format**:
```json
{
  "error": {
    "code": "INVALID_HASH_FORMAT",
    "message": "Hash 'abc123' is not a valid MD5 hash",
    "details": {
      "expected_format": "32-character hexadecimal string"
    }
  }
}
```

**Example Usage**:
```bash
# Crack MD5 hash with 60-second timeout
curl -X POST https://hash-breaker.example.com/v1/audit-hash \
  -H "Content-Type: application/json" \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 60,
    "priority": "normal"
  }'

# Response:
# {"job_id": "f4a5c6b7-1234-5678-9abc-123456789abc", "status": "pending", ...}
```

---

### 2. Get Job Status

Query the current status and progress of a submitted job.

**Endpoint**: `GET /v1/status/{job_id}`

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string (UUID) | ✅ Yes | Unique job identifier |

**Success Response** (200 OK):

**Pending/Running Status**:
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "running",
  "progress": 45,
  "current_phase": "Phase 3: AI Candidate Generation",
  "phase_number": 3,
  "time_remaining": 33,
  "time_elapsed": 27,
  "submitted_at": "2025-01-01T12:00:00Z",
  "started_at": "2025-01-01T12:00:01Z",
  "estimated_completion": "2025-01-01T12:01:00Z",
  "result": null
}
```

**Success Status**:
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "success",
  "result": "password123",
  "cracked_at": "2025-01-01T12:00:15Z",
  "cracked_in_phase": "Phase 2: Rule-Based Attack",
  "phase_number": 2,
  "time_elapsed": 15.3,
  "attempts": 1523490,
  "guess_rate": "100.2 KH/s"
}
```

**Failed Status**:
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "failed",
  "reason": "Timeout exceeded",
  "last_phase": "Phase 4: Limited Mask Attack",
  "phase_number": 4,
  "time_elapsed": 60.0,
  "attempts": 5820394,
  "max_attempts_reached": false
}
```

**Cancelled Status**:
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "cancelled",
  "cancelled_at": "2025-01-01T12:00:30Z",
  "reason": "User requested cancellation"
}
```

**Error Responses**:

| Status Code | Error | Description |
|-------------|-------|-------------|
| 404 | `JOB_NOT_FOUND` | No job with specified job_id exists |
| 500 | `INTERNAL_ERROR` | Server error |

**Status Values**:
- `pending`: Job queued, waiting for worker
- `running`: Job currently processing
- `success`: Password successfully recovered
- `failed`: Job failed (timeout or all phases exhausted)
- `cancelled`: Job cancelled by client

**Example Usage**:
```bash
curl https://hash-breaker.example.com/v1/status/f4a5c6b7-1234-5678-9abc-123456789abc

# Response: JSON with job status
```

---

### 3. Cancel Job

Cancel a running or pending job.

**Endpoint**: `POST /v1/jobs/{job_id}/cancel`

**URL Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string (UUID) | ✅ Yes | Unique job identifier |

**Success Response** (200 OK):
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "cancelled",
  "message": "Job cancelled successfully",
  "cancelled_at": "2025-01-01T12:00:30Z"
}
```

**Error Responses**:

| Status Code | Error | Description |
|-------------|-------|-------------|
| 404 | `JOB_NOT_FOUND` | No job with specified job_id exists |
| 409 | `JOB_ALREADY_COMPLETED` | Job already finished (success/failed) |
| 500 | `INTERNAL_ERROR` | Server error |

**Example Usage**:
```bash
curl -X POST https://hash-breaker.example.com/v1/jobs/f4a5c6b7-1234-5678-9abc-123456789abc/cancel

# Response: {"status": "cancelled", ...}
```

---

### 4. Health Check

Health check endpoint for load balancers, orchestration, and monitoring.

**Endpoint**: `GET /v1/health`

**Success Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z",
  "dependencies": {
    "redis": {
      "status": "healthy",
      "latency_ms": 0.5
    },
    "rabbitmq": {
      "status": "healthy",
      "latency_ms": 2.3
    }
  },
  "workers": {
    "total": 4,
    "active": 3,
    "idle": 1,
    "disabled": 0
  },
  "queue": {
    "depth": 12,
    "high_priority": 2,
    "normal_priority": 8,
    "low_priority": 2
  }
}
```

**Degraded Response** (503 Service Unavailable):
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "timestamp": "2025-01-01T12:00:00Z",
  "issues": [
    {
      "component": "rabbitmq",
      "severity": "warning",
      "message": "High connection count: 95/100"
    }
  ]
}
```

**Example Usage**:
```bash
curl https://hash-breaker.example.com/v1/health

# Response: Health status JSON
```

---

### 5. Metrics (Prometheus)

Prometheus-compatible metrics endpoint for monitoring and alerting.

**Endpoint**: `GET /v1/metrics`

**Response** (200 OK - text/plain):
```
# HELP hash_breaker_jobs_total Total number of jobs processed
# TYPE hash_breaker_jobs_total counter
hash_breaker_jobs_total{status="success"} 1523
hash_breaker_jobs_total{status="failed"} 847
hash_breaker_jobs_total{status="cancelled"} 23

# HELP hash_breaker_jobs_duration_seconds Job execution duration
# TYPE hash_breaker_jobs_duration_seconds histogram
hash_breaker_jobs_duration_seconds{status="success",le="0.1"} 450
hash_breaker_jobs_duration_seconds{status="success",le="1"} 1523
hash_breaker_jobs_duration_seconds{status="success",le="10"} 2340
hash_breaker_jobs_duration_seconds{status="success",le="+Inf"} 2543
hash_breaker_jobs_duration_seconds_sum{status="success"} 15234.5
hash_breaker_jobs_duration_seconds_count{status="success"} 2543

# HELP hash_breaker_phase_duration_seconds Phase execution duration
# TYPE hash_breaker_phase_duration_seconds histogram
hash_breaker_phase_duration_seconds{phase="dictionary",le="1"} 1523
hash_breaker_phase_duration_seconds{phase="rule_based",le="5"} 450
hash_breaker_phase_duration_seconds{phase="ai_generation",le="20"} 234
hash_breaker_phase_duration_seconds{phase="mask_attack",le="30"} 123

# HELP hash_breaker_guesses_total Total password guesses
# TYPE hash_breaker_guesses_total counter
hash_breaker_guesses_total{phase="dictionary"} 150000000
hash_breaker_guesses_total{phase="rule_based"} 500000000
hash_breaker_guesses_total{phase="ai_generation"} 25000000
hash_breaker_guesses_total{phase="mask_attack"} 10000000

# HELP hash_breaker_success_rate Success rate by hash type
# TYPE hash_breaker_success_rate gauge
hash_breaker_success_rate{hash_type="MD5"} 0.68
hash_breaker_success_rate{hash_type="SHA1"} 0.54
hash_breaker_success_rate{hash_type="NTLM"} 0.72
hash_breaker_success_rate{hash_type="bcrypt"} 0.12

# HELP hash_breaker_queue_depth Current queue depth by priority
# TYPE hash_breaker_queue_depth gauge
hash_breaker_queue_depth{priority="high"} 2
hash_breaker_queue_depth{priority="normal"} 8
hash_breaker_queue_depth{priority="low"} 2

# HELP hash_breaker_gpu_utilization GPU utilization percentage
# TYPE hash_breaker_gpu_utilization gauge
hash_breaker_gpu_utilization{worker_id="worker-01",gpu_id="0"} 95.3
hash_breaker_gpu_utilization{worker_id="worker-01",gpu_id="1"} 87.2
hash_breaker_gpu_utilization{worker_id="worker-02",gpu_id="0"} 92.1

# HELP hash_breaker_worker_jobs_current Current jobs per worker
# TYPE hash_breaker_worker_jobs_current gauge
hash_breaker_worker_jobs_current{worker_id="worker-01"} 1
hash_breaker_worker_jobs_current{worker_id="worker-02"} 1
hash_breaker_worker_jobs_current{worker_id="worker-03"} 1
hash_breaker_worker_jobs_current{worker_id="worker-04"} 0
```

---

## Rate Limiting

**Default Limits** (configurable):

| Tier | Requests/Hour | Concurrent Jobs |
|------|---------------|-----------------|
| Anonymous | 100 | 1 |
| Authenticated (Basic) | 500 | 5 |
| Authenticated (Premium) | 2000 | 20 |

**Rate Limit Headers**:
```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704100200
```

**Rate Limit Exceeded Response** (429 Too Many Requests):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Maximum 100 requests per hour.",
    "retry_after": 3600
  }
}
```

---

## WebSocket Support (Optional)

For real-time job status updates, WebSocket connections are supported.

**Endpoint**: `wss://hash-breaker.example.com/v1/ws/jobs/{job_id}`

**Connection**:
```javascript
const ws = new WebSocket('wss://hash-breaker.example.com/v1/ws/jobs/f4a5c6b7-1234-5678-9abc-123456789abc');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Progress:', update.progress, '%');
  console.log('Phase:', update.current_phase);

  if (update.status === 'success') {
    console.log('Password:', update.result);
    ws.close();
  }
};
```

**Server-Sent Updates**:
```json
{
  "job_id": "f4a5c6b7-1234-5678-9abc-123456789abc",
  "status": "running",
  "progress": 45,
  "current_phase": "Phase 3: AI Candidate Generation",
  "time_remaining": 33,
  "timestamp": "2025-01-01T12:00:33Z"
}
```

---

## OpenAPI/Swagger UI

Interactive API documentation available at:

```
https://hash-breaker.example.com/docs
```

Features:
- Try out endpoints directly from browser
- View request/response schemas
- Test authentication
- Download OpenAPI spec

---

**Document Version**: 1.0
**Last Updated**: 2025-01-01
