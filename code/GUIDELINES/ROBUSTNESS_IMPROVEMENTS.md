# PRODUCTION ROBUSTNESS ENHANCEMENT GUIDE
## Vitruvian Cryptography Platform - Comprehensive Failure Mode & Resilience Fixes

---

## 1. CONCURRENCY & RACE CONDITIONS

### 1.1 Go Executor Buffered Channel Leak (CRITICAL)
**File**: `agents/orchestrator/internal/executor/executor.go:37`
**Problem**: Unbuffered error path can deadlock. If `group.Wait()` returns error at line 70, semaphore tokens are leaked.

```go
// CURRENT (BUGGY)
sem := make(chan struct{}, e.maxParallel)
group.Go(func() error {
    defer func() { <-sem }()  // Only released on success
    ...
})
if err := group.Wait(); err != nil {
    return nil, err  // Semaphore leaked if goroutine panics or context cancels
}
```

**Fix**:
```go
// ROBUST VERSION
sem := make(chan struct{}, e.maxParallel)
var wg sync.WaitGroup

for _, idx := range ready {
    wg.Add(1)
    sem <- struct{}{}  // Acquire
    go func(idx int) {
        defer func() {
            wg.Done()
            <-sem  // Always release, panic-safe
        }()
        // execution logic
    }(idx)
}

group.Go(func() error {
    wg.Wait()
    return nil
})
```

**Test**: Add panic injection test to verify semaphore is released even on panic.

---

### 1.2 Python Asyncio Task Cancellation (HIGH)
**File**: `agents/password_checker/aggregator/app.py:196`
**Problem**: `asyncio.gather(*tasks)` without `return_exceptions=True` causes hung requests if one component times out.

```python
# CURRENT (RISKY)
results = await asyncio.gather(*tasks)  # If task_N times out, all tasks cancelled
```

**Fix**:
```python
# ROBUST VERSION
results = await asyncio.gather(
    *tasks,
    return_exceptions=True  # Capture timeouts per-component
)

# Process results with error handling
processed = []
for i, result in enumerate(results):
    if isinstance(result, Exception):
        logger.warning(f"Component {COMPONENTS[i].name} failed: {result}")
        processed.append(ComponentResult(
            component=COMPONENTS[i].name,
            score=0,
            source="timeout",
            error=str(result)
        ))
    else:
        processed.append(result)
```

**Test**: Mock timeout on one component, verify others complete.

---

### 1.3 BoltDB Concurrent Write Lock (MEDIUM)
**File**: `agents/prime_checker/main.go:800+`
**Problem**: BoltDB single-writer model can cause request rejection under load.

**Fix**:
```go
// Add write queue to serialize updates
type Store struct {
    db *bolt.DB
    writeQueue chan WriteOp  // Buffer writes
    writeSem   chan struct{} // Limit concurrent writes
}

func (s *Store) cacheResult(ctx context.Context, number string, result HistoryItem) error {
    op := WriteOp{number, result, make(chan error)}
    select {
    case s.writeQueue <- op:
        return <-op.done
    case <-ctx.Done():
        return ctx.Err()
    }
}

// Background worker
go func() {
    for op := range s.writeQueue {
        op.done <- s.db.Update(func(tx *bolt.Tx) error {
            return tx.Bucket([]byte("results")).Put([]byte(op.num), op.data)
        })
    }
}()
```

---

## 2. RESOURCE EXHAUSTION & MEMORY LEAKS

### 2.1 Unbounded HTTP Client Connections (HIGH)
**File**: `agents/orchestrator/internal/choice/client.go` (missing pooling)
**Problem**: Creating new HTTP client per request exhausts file descriptors.

```go
// CURRENT (INEFFICIENT)
client := &http.Client{
    Timeout: 10 * time.Second,
}
resp, err := client.Do(req)  // New conn each time
defer resp.Body.Close()
```

**Fix**:
```go
// Create once at init
var httpClient = &http.Client{
    Timeout: 10 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        MaxConnsPerHost:     20,  // Limit per destination
        IdleConnTimeout:     90 * time.Second,
        DisableKeepAlives:   false,
        DialContext: (&net.Dialer{
            Timeout:   5 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,
    },
}

// Reuse httpClient for all requests
```

---

### 2.2 Python AsyncIO Connection Pool Exhaustion (HIGH)
**File**: `agents/password_checker/aggregator/app.py:115`
**Problem**: Creating new `httpx.AsyncClient` per request bleeds connections.

```python
# CURRENT (LEAKY)
async def _call_component(client: httpx.AsyncClient, ...):
    async with httpx.AsyncClient() as client:  # New client per call
        response = await client.post(...)
```

**Fix**:
```python
# Global connection pool
_http_client: Optional[httpx.AsyncClient] = None

async def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
                keepalive_expiry=30.0
            )
        )
    return _http_client

@app.on_event("shutdown")
async def shutdown():
    if _http_client:
        await _http_client.aclose()

async def _call_component(component: ComponentConfig, password: str) -> ComponentResult:
    client = await get_http_client()
    try:
        response = await client.post(
            component.score_endpoint,
            json={"password": password},
            timeout=10.0
        )
    except httpx.TimeoutException:
        return ComponentResult(component=component.name, score=0, error="timeout")
    except httpx.ConnectError:
        return ComponentResult(component=component.name, score=0, error="unreachable")
```

---

### 2.3 Chromadb Embedded Mode Memory Bloat (MEDIUM)
**File**: `agents/theory_specialist/app/rag_system.py:400+`
**Problem**: In-process ChromaDB holds full embeddings in RAM, no eviction.

```python
# CURRENT (unbounded memory)
self.chroma_client = chromadb.PersistentClient(
    path=str(settings.chroma_persist_directory)
)
```

**Fix**:
```python
# Add collection-level limits
def _create_collection_safe(self, name: str) -> Collection:
    settings = chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        # Limit collection size
        is_persistent=True,
        persist_directory=str(self.settings.chroma_persist_directory)
    )
    
    collection = self.client.get_or_create_collection(
        name=name,
        metadata={"hnsw:max_elements": 10000}  # Hard limit
    )
    
    # Cleanup if exceeding quota
    if collection.count() > 9500:  # 95% threshold
        logger.warning(f"Collection {name} approaching limit, pruning old entries")
        # Remove oldest entries
        all_ids = collection.get()["ids"]
        if len(all_ids) > 9500:
            collection.delete(ids=all_ids[:-5000])
    
    return collection
```

---

## 3. TIMEOUT & DEADLINE MISMANAGEMENT

### 3.1 Missing Context Timeouts (CRITICAL)
**File**: `agents/orchestrator/internal/orchestrator/orchestrator.go:49`
**Problem**: No timeout on main `Handle()` function; requests can hang forever.

```go
// CURRENT (no deadline)
func (e *Engine) Handle(ctx context.Context, req model.OrchestrateRequest) (model.OrchestrateResponse, error) {
    // ctx may have no deadline
    intentResult, entities, choiceErr := e.runChoiceMaker(ctx, req.Text)  // Could block indefinitely
}
```

**Fix**:
```go
// Enforce deadline if missing
func (e *Engine) Handle(ctx context.Context, req model.OrchestrateRequest) (model.OrchestrateResponse, error) {
    // Ensure deadline exists
    if _, ok := ctx.Deadline(); !ok {
        var cancel context.CancelFunc
        ctx, cancel = context.WithTimeout(ctx, 30*time.Second)  // Max 30s for orchestration
        defer cancel()
    }
    
    // All child operations inherit deadline
    intentResult, entities, choiceErr := e.runChoiceMaker(ctx, req.Text)
    if choiceErr != nil && errors.Is(choiceErr, context.DeadlineExceeded) {
        return model.OrchestrateResponse{}, fmt.Errorf("orchestration timeout: %w", choiceErr)
    }
}
```

---

### 3.2 Rust Test Unwraps in Hot Path (HIGH)
**File**: `agents/command_executor/src/providers/symmetric.rs:267`
**Problem**: `.unwrap()` on ExecutionContext in production code causes panic.

```rust
// CURRENT (PANICS)
let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();  // Line 267
```

**Fix**:
```rust
// Proper error handling
let ctx = match ExecutionContext::new(EXECUTION_TIMEOUT_MS) {
    Ok(ctx) => ctx,
    Err(e) => {
        error!("Failed to create execution context: {}", e);
        return Err(SymmetricError::ExecutionFailed(
            format!("Context init failed: {}", e)
        ));
    }
};
```

Apply to all instances:
- `src/providers/pqc.rs:209-210`
- `src/providers/random.rs:93-94`
- `src/providers/encoding.rs:137-140`
- `src/providers/hashing.rs:151-152`
- `src/providers/asymmetric.rs:358-359`

---

## 4. ERROR HANDLING GAPS

### 4.1 Silent Exception Swallowing (CRITICAL)
**File**: `agents/theory_specialist/app/database.py:43-48`
**Problem**: Broad `except Exception: pass` hides initialization failures.

```python
# CURRENT (SILENT FAILURE)
try:
    # DB connection
except Exception:
    pass  # Silently ignored!
```

**Fix**:
```python
# Explicit error handling
def get_db_session():
    try:
        session = SessionLocal()
        # Test connection
        session.execute(text("SELECT 1"))
        return session
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        raise RuntimeError("Database unavailable") from e
    except Exception as e:
        logger.critical(f"Unexpected database error: {e}", exc_info=True)
        raise RuntimeError("Database error: unknown cause") from e
```

---

### 4.2 Python Broad Exception Handlers (MEDIUM)
**File**: `agents/choice_maker/components/make_decision/scripts/server.py:70-85`
**Problem**: `except Exception as e:` catches `KeyboardInterrupt`, `SystemExit`.

```python
# CURRENT (SWALLOWS CRITICAL SIGNALS)
try:
    model.predict(...)
except Exception as e:
    logger.error(f"Prediction failed: {e}")
    # Might be SIGTERM!
```

**Fix**:
```python
# Specific exception catching
try:
    model.predict(...)
except (ValueError, TypeError) as e:
    logger.error(f"Invalid input: {e}")
    return {"error": "invalid_request"}, 400
except RuntimeError as e:
    logger.error(f"Model inference failed: {e}")
    return {"error": "inference_failed"}, 503
except (KeyboardInterrupt, SystemExit):
    raise  # Let them propagate!
```

---

### 4.3 Missing gRPC/HTTP Error Translation (HIGH)
**File**: `agents/orchestrator/internal/agents/pool.go`
**Problem**: Agent HTTP errors not properly translated to user-friendly responses.

```go
// ADD THIS WRAPPER
func (p *Pool) Execute(ctx context.Context, agent, op string, params map[string]any) (any, error) {
    result, err := p.clients[agent].Do(ctx, op, params)
    if err != nil {
        // Translate transport errors
        if errors.Is(err, context.DeadlineExceeded) {
            return nil, fmt.Errorf("agent %s timeout", agent)
        }
        if errors.Is(err, context.Canceled) {
            return nil, fmt.Errorf("agent %s cancelled", agent)
        }
        var netErr net.Error
        if errors.As(err, &netErr) {
            if netErr.Timeout() {
                return nil, fmt.Errorf("agent %s network timeout", agent)
            }
            return nil, fmt.Errorf("agent %s unreachable: %w", agent, err)
        }
        return nil, fmt.Errorf("agent %s error: %w", agent, err)
    }
    return result, nil
}
```

---

## 5. DATA CONSISTENCY & CORRUPTION

### 5.1 Incomplete Transaction Handling (HIGH)
**File**: `agents/prime_checker/main.go:800+`
**Problem**: No rollback on multi-step operations; partial writes possible.

```go
// CURRENT (NOT ATOMIC)
func (s *Store) UpdateWithStats(num string, result HistoryItem) error {
    // Write result
    s.db.Update(func(tx *bolt.Tx) error {
        return tx.Bucket([]byte("results")).Put(...)
    })
    // Write stats - if this fails, result is orphaned
    s.db.Update(func(tx *bolt.Tx) error {
        return tx.Bucket([]byte("stats")).Put(...)
    })
}
```

**Fix**:
```go
// Atomic multi-bucket write
func (s *Store) UpdateWithStats(num string, result HistoryItem) error {
    return s.db.Batch(func(tx *bolt.Tx) error {
        // Both buckets updated or nothing
        if err := tx.Bucket([]byte("results")).Put([]byte(num), encodeResult(result)); err != nil {
            return err
        }
        if err := tx.Bucket([]byte("stats")).Put([]byte(num), encodeStats(result)); err != nil {
            return err
        }
        return nil
    })
}
```

---

### 5.2 Cache Invalidation Race (MEDIUM)
**File**: `agents/prime_checker/main.go:115+`
**Problem**: LRU cache not invalidated when DB updated; stale reads possible.

```go
// CURRENT (STALE CACHE)
type Server struct {
    cache *LRUCache
    store *Store
}

func (s *Server) GetPrime(num string) (PrimeResult, error) {
    if v, ok := s.cache.Get(num); ok {
        return v.(PrimeResult), nil  // Stale if DB was updated
    }
    // Load from DB
}
```

**Fix**:
```go
// Add invalidation hook
func (s *Server) UpdateResult(num string, result PrimeResult) error {
    s.cache.Delete(num)  // Invalidate first
    return s.store.Save(num, result)
}

// Or use version stamps
type CachedResult struct {
    Value   PrimeResult
    Version int64
    Mutex   sync.RWMutex
}
```

---

## 6. INPUT VALIDATION BYPASS

### 6.1 Regex `.unwrap()` Without Validation (CRITICAL)
**File**: `agents/command_executor/src/validators.rs:11-20`
**Problem**: Static regex compilation can panic if malformed.

```rust
// CURRENT (ASSUMES CORRECT COMPILE-TIME REGEX)
static ref HEX_REGEX: Regex = Regex::new(r"^[0-9a-fA-F]+$").unwrap();
```

**Fix**: Regex is correct, but add fallback:
```rust
// Safe regex initialization
lazy_static! {
    static ref HEX_REGEX: Regex = Regex::new(r"^[0-9a-fA-F]+$")
        .expect("Hardcoded regex pattern is valid");
}

// Then use safely:
pub fn validate_hex(input: &str) -> Result<(), ValidationError> {
    if !HEX_REGEX.is_match(input) {
        return Err(ValidationError::InvalidHex);
    }
    Ok(())
}
```

---

### 6.2 Password Length Not Enforced at API (MEDIUM)
**File**: `agents/password_checker/aggregator/app.py:70-74`
**Problem**: `min_length=1` allows single-character passwords; some components may reject.

```python
# CURRENT (WEAK VALIDATION)
password: str = Field(..., min_length=1)
```

**Fix**:
```python
# Comprehensive validation
password: str = Field(
    ...,
    min_length=1,
    max_length=256,  # Prevent DoS
    description="Password to score (1-256 chars)"
)

@validator("password")
def validate_password(cls, v: str) -> str:
    if len(v) < 1:
        raise ValueError("Password cannot be empty")
    if len(v) > 256:
        raise ValueError("Password exceeds maximum length")
    # Check for null bytes
    if '\x00' in v:
        raise ValueError("Password contains null bytes")
    return v
```

---

## 7. OBSERVABILITY GAPS

### 7.1 Metric Collection Missing (CRITICAL)
**Files**: All services
**Problem**: No Prometheus metrics; can't detect degradation.

```go
// ADD TO ORCHESTRATOR
import "github.com/prometheus/client_golang/prometheus"

var (
    orchestrationDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "orchestration_duration_seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"path"},
    )
    agentErrorsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "agent_errors_total",
        },
        []string{"agent", "error_type"},
    )
)

func (e *Engine) Handle(ctx context.Context, req OrchestrateRequest) (response, error) {
    defer func(start time.Time) {
        orchestrationDuration.WithLabelValues(response.ExecutionPath).Observe(time.Since(start).Seconds())
    }(time.Now())
    
    // execution...
}
```

---

### 7.2 Missing Distributed Tracing (MEDIUM)
**Files**: All services
**Problem**: Can't correlate cross-service failures.

```go
// ADD OpenTelemetry
import "go.opentelemetry.io/otel"

func (e *Engine) Handle(ctx context.Context, req OrchestrateRequest) (response, error) {
    tracer := otel.Tracer("orchestrator")
    ctx, span := tracer.Start(ctx, "orchestration",
        trace.WithAttributes(
            attribute.String("request.id", req.RequestID),
            attribute.String("conversation.id", req.ConversationID),
        ),
    )
    defer span.End()
    
    // All child calls inherit context with span
}
```

---

## 8. DEPLOYMENT & CONFIGURATION

### 8.1 Hardcoded Timeouts (MEDIUM)
**Files**: Multiple
**Problem**: No way to adjust timeouts without rebuild.

```go
// CURRENT (HARDCODED)
const EXECUTION_TIMEOUT_MS = 5000
```

**Fix**:
```go
// Environment-configurable
type Config struct {
    ExecutionTimeout time.Duration
}

func loadConfig() Config {
    return Config{
        ExecutionTimeout: parseDuration(os.Getenv("EXECUTION_TIMEOUT"), 5*time.Second),
    }
}

func parseDuration(s string, fallback time.Duration) time.Duration {
    if s == "" {
        return fallback
    }
    d, err := time.ParseDuration(s)
    if err != nil {
        log.Printf("Invalid duration %q, using fallback: %v", s, err)
        return fallback
    }
    return d
}
```

---

### 8.2 Missing Graceful Shutdown (HIGH)
**File**: `agents/prime_checker/main.go:146+`
**Problem**: Killing container mid-request causes data loss.

```go
// CURRENT (NO GRACEFUL SHUTDOWN)
httpServer := &http.Server{...}
if err := httpServer.ListenAndServe(); err != nil {
    log.Fatalf("server failed: %v", err)
}
```

**Fix**:
```go
// Add signal handler
go func() {
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)
    sig := <-sigChan
    
    log.Printf("Received signal %v, graceful shutdown...", sig)
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    if err := httpServer.Shutdown(ctx); err != nil {
        log.Printf("Shutdown error: %v", err)
    }
    if err := s.store.db.Close(); err != nil {
        log.Printf("DB close error: %v", err)
    }
}()

if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
    log.Fatalf("server failed: %v", err)
}
```

---

## 9. PRODUCTION CHECKLIST

### Before Deploying:

- [ ] **Load test**: 100+ concurrent requests per service
- [ ] **Chaos testing**: Kill containers, break network links
- [ ] **Memory leak detection**: Run with `--memprofile` for Go, `tracemalloc` for Python
- [ ] **Connection limit validation**: `lsof -p <pid>` should not exceed limits
- [ ] **Timeout validation**: All requests complete within configured limits
- [ ] **Error rate monitoring**: Set up alerts on 5xx errors
- [ ] **Circuit breaker testing**: Verify cascading failures don't occur
- [ ] **Database backup**: Test restore procedure
- [ ] **Log aggregation**: Verify all services log to centralized system
- [ ] **Metrics export**: Confirm Prometheus scrapes all endpoints

### Docker Compose Best Practices:

```yaml
services:
  agent:
    # Add healthcheck with dependency tracking
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    
    # Add restart policy
    restart: on-failure:3  # Restart max 3 times
    
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    
    # Add shutdown grace period
    stop_grace_period: 15s
```

---

## 10. TESTING RECOMMENDATIONS

### Mutation Testing (Detect Weak Tests)
```bash
# Go: use stryker-go
stryker-go run

# Python: use mutmut
mutmut run --tests-dir tests/
```

### Fuzz Testing
```go
// Add to command_executor
func FuzzSymmetricEncrypt(f *testing.F) {
    f.Fuzz(func(t *testing.T, plaintext []byte, key string) {
        ctx := ExecutionContext::new(...)?
        _, err := symmetric.Encrypt(&ctx, string(plaintext), key, ...)
        if err != nil && !isSilentlyIgnored(err) {
            t.Errorf("unexpected error: %v", err)
        }
    })
}
```

### Chaos Engineering
```bash
# Use gremlin or pumba to kill containers
docker run --rm -it --name pumba \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gaiaadm/pumba pumba kill \
  --signal SIGTERM \
  --interval 10s \
  vitruvian-orchestrator
```

---

## SUMMARY TABLE

| Issue | Severity | File | Impact | Fix Complexity |
|-------|----------|------|--------|-----------------|
| Semaphore leak | CRITICAL | executor.go | Deadlock | Low |
| Missing timeouts | CRITICAL | orchestrator.go | Hang | Medium |
| Silent exceptions | CRITICAL | database.py | Silent failures | Low |
| Unwrap panics | CRITICAL | pqc.rs | Crashes | Low |
| Connection leak | HIGH | (multiple) | Resource exhaustion | Medium |
| Async cancellation | HIGH | app.py | Request loss | Low |
| Broad exception catch | MEDIUM | (multiple) | Signal swallowing | Low |
| Cache invalidation | MEDIUM | main.go (prime) | Stale reads | Medium |
| Incomplete transactions | HIGH | main.go (prime) | Data corruption | Medium |
| No graceful shutdown | HIGH | (multiple) | Data loss | Medium |

**Total estimated implementation time**: 40-60 hours
