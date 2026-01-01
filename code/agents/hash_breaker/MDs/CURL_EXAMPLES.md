# Hash Breaker API - Curl Examples

## Base URL
```
http://localhost:8000
```

---

## 1. Health Check

### Check System Health
```bash
curl http://localhost:8000/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-01T21:34:00",
  "dependencies": {
    "redis": {"status": "healthy"}
  },
  "workers": {
    "total": 4,
    "active": 0,
    "idle": 4
  },
  "queue": {
    "depth": 0
  }
}
```

---

## 2. Submit Cracking Jobs

### MD5 Hash (mode 0)
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 60
  }'
```

### SHA1 Hash (mode 100)
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8",
    "hash_type_id": 100,
    "timeout_seconds": 60
  }'
```

### SHA256 Hash (mode 1400)
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "0c030df5a4e7477d218012c0121ebce6d61bb8dc46e0a6c4f8e1cc8091b946a5",
    "hash_type_id": 1400,
    "timeout_seconds": 60
  }'
```

### With High Priority
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 120,
    "priority": "HIGH"
  }'
```

**Response (all):**
```json
{
  "job_id": "af17a0fe-8188-4e50-a809-e894bff28e86",
  "status": "pending",
  "estimated_completion": null,
  "queue_position": null
}
```

---

## 3. Check Job Status

### Basic Status Check
```bash
curl http://localhost:8000/v1/status/{job_id}
```

### Pretty JSON Output
```bash
curl -s http://localhost:8000/v1/status/{job_id} | python3 -m json.tool
```

### With jq (filtered)
```bash
curl -s http://localhost:8000/v1/status/{job_id} | jq '{status, result, attempts}'
```

**Success Response:**
```json
{
  "job_id": "af17a0fe-8188-4e50-a809-e894bff28e86",
  "status": "success",
  "progress": 100,
  "current_phase": "Phase 1: Quick Dictionary Attack",
  "phase_number": 1,
  "time_elapsed": 0.001,
  "submitted_at": "2026-01-01T21:34:00",
  "result": "hello",
  "attempts": 60
}
```

**Failure Response:**
```json
{
  "job_id": "f754b5c3-d10c-45c1-8433-01c14574a767",
  "status": "failed",
  "progress": 100,
  "reason": "Password not found after all phases",
  "attempts": 15099996
}
```

---

## 4. Cancel Job

### Cancel Running Job
```bash
curl -X POST http://localhost:8000/v1/jobs/{job_id}/cancel
```

**Response:**
```json
{
  "job_id": "af17a0fe-8188-4e50-a809-e894bff28e86",
  "status": "cancelled",
  "message": "Job cancelled successfully",
  "cancelled_at": "2026-01-01T21:35:00"
}
```

---

## 5. Complete Workflow (One-Liner)

### Submit + Wait + Result
```bash
# Submit job
JOB_ID=$(curl -s -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{"hash": "5d41402abc4b2a76b9719d911017c592", "hash_type_id": 0, "timeout_seconds": 60}' \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Wait for completion
sleep 5

# Get result
curl -s http://localhost:8000/v1/status/$JOB_ID | jq
```

### Submit + Poll Until Complete
```bash
JOB_ID=$(curl -s -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{"hash": "5d41402abc4b2a76b9719d911017c592", "hash_type_id": 0, "timeout_seconds": 60}' \
  | jq -r '.job_id')

echo "Cracking hash... Job ID: $JOB_ID"

while true; do
  STATUS=$(curl -s http://localhost:8000/v1/status/$JOB_ID)
  STATE=$(echo $STATUS | jq -r '.status')

  if [ "$STATE" = "success" ] || [ "$STATE" = "failed" ]; then
    echo $STATUS | jq
    break
  fi

  PROGRESS=$(echo $STATUS | jq -r '.progress')
  echo "Progress: $PROGRESS%"
  sleep 2
done
```

---

## 6. Generate Test Hashes

### MD5
```bash
echo -n "password" | md5sum | cut -d' ' -f1
# Output: 5f4dcc3b5aa765d61d8327deb882cf99
```

### SHA1
```bash
echo -n "password" | sha1sum | cut -d' ' -f1
# Output: 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
```

### SHA256
```bash
echo -n "password" | sha256sum | cut -d' ' -f1
# Output: 5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
```

### SHA512
```bash
echo -n "password" | sha512sum | cut -d' ' -f1
# Output: b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86
```

---

## 7. Common Hashcat Modes

| Mode | Hash Type    | Example Command                          | Length |
|------|--------------|------------------------------------------|--------|
| 0    | MD5          | `echo -n "pass" \| md5sum`               | 32     |
| 10   | MD5($pass.$salt) | -                                      | 32     |
| 20   | MD5($salt.$pass) | -                                      | 32     |
| 100  | SHA1         | `echo -n "pass" \| sha1sum`              | 40     |
| 1400 | SHA256       | `echo -n "pass" \| sha256sum`            | 64     |
| 1700 | SHA512       | `echo -n "pass" \| sha512sum`            | 128    |
| 300  | MySQL5       | -                                        | 40     |
| 500  | md5crypt     | -                                        | 34     |
| 3200 | bcrypt       | -                                        | 60     |

**Full list:** https://hashcat.net/wiki/doku.php?id=example_hashes

---

## 8. Error Handling

### Validation Error (hash_type_id > 32000)
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{"hash": "abc", "hash_type_id": 99999, "timeout_seconds": 60}'
```

**Response:**
```json
{
  "detail": [{
    "type": "less_than_equal",
    "loc": ["body", "hash_type_id"],
    "msg": "Input should be less than or equal to 32000",
    "input": 99999
  }]
}
```

### Job Not Found
```bash
curl http://localhost:8000/v1/status/00000000-0000-0000-0000-000000000000
```

**Response:**
```json
{
  "detail": {
    "error": {
      "code": "JOB_NOT_FOUND",
      "message": "Job 00000000-0000-0000-0000-000000000000 not found"
    }
  }
}
```

---

## 9. Advanced Examples

### Batch Processing (Multiple Hashes)
```bash
#!/bin/bash
HASHES=(
  "5d41402abc4b2a76b9719d911017c592:0"
  "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8:100"
  "0c030df5a4e7477d218012c0121ebce6d61bb8dc46e0a6c4f8e1cc8091b946a5:1400"
)

for entry in "${HASHES[@]}"; do
  IFS=':' read -r hash mode <<< "$entry"

  echo "Cracking: $hash (mode $mode)"
  JOB_ID=$(curl -s -X POST http://localhost:8000/v1/audit-hash \
    -H 'Content-Type: application/json' \
    -d "{\"hash\": \"$hash\", \"hash_type_id\": $mode, \"timeout_seconds\": 60}" \
    | jq -r '.job_id')

  sleep 5
  RESULT=$(curl -s http://localhost:8000/v1/status/$JOB_ID)
  echo "Result: $(echo $RESULT | jq -r '.result // .reason')"
  echo ""
done
```

### Custom Timeout (Quick Test)
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 10
  }'
```

### Low Priority Job
```bash
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 60,
    "priority": "LOW"
  }'
```

---

## 10. Interactive API Documentation

### Swagger UI (Browser)
```
http://localhost:8000/docs
```

### ReDoc (Browser)
```
http://localhost:8000/redoc
```

### OpenAPI JSON
```bash
curl http://localhost:8000/openapi.json | python3 -m json.tool
```

---

## Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/health` | GET | Check system health |
| `/v1/audit-hash` | POST | Submit cracking job |
| `/v1/status/{job_id}` | GET | Get job status |
| `/v1/jobs/{job_id}/cancel` | POST | Cancel running job |
| `/v1/metrics` | GET | Prometheus metrics |
| `/docs` | GET | Interactive API docs |

---

## Tips

1. **Always save job_id** from submission response
2. **Poll status** every 2-5 seconds for real-time updates
3. **Use timeouts** to prevent long-running jobs
4. **Set priority** for urgent jobs (HIGH/NORMAL/LOW)
5. **Check logs** for debugging: `docker compose logs -f worker`

---

## Troubleshooting

### Job Not Starting
```bash
# Check worker status
docker compose ps

# Check worker logs
docker compose logs -f worker

# Check queue depth
curl http://localhost:8000/v1/health | jq '.queue'
```

### Connection Refused
```bash
# Verify services are running
docker compose ps

# Restart if needed
docker compose restart
```

### No Results After Timeout
- Password not in wordlist (normal behavior)
- Try longer timeout
- Check if hash type is supported (0-32000)
- Verify hash format is correct
