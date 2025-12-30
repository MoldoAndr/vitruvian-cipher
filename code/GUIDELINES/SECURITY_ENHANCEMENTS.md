
● 🛡️ Vitruvian Platform: Defense-in-Depth Security Architecture

  ---
  1. Architecture Overview: Zero Trust Network Segmentation

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                          EXTERNAL (Internet)                                │
  └─────────────────────────────────────────────────────────────────────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │     DDoS Protection           │
                      │  (Cloudflare or on-prem)      │ ← Free tier / self-hosted
                      └───────────────┬───────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │    Reverse Proxy + TLS        │
                      │    Nginx / Traefik            │
                      └───────────────┬───────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │         WAF                   │
                      │  BunkerWeb / ModSecurity CRS  │ ← Open Source WAF
                      └───────────────┬───────────────┘
                                      │
                      ┌───────────────▼──────────────┐
                      │     API Gateway              │
                      │  Kong CE / Traefik Middlewar │
                      │  + Rate Limiting             │
                      │  + JWT Validation            │
                      │  + Request/Response Size     │
                      └──────────────┬───────────────┘
                                     │
          ┌──────────────────────────┼─────────────────────────┐
          │                          │                         │
  ┌───────▼────────┐          ┌──────▼─────┐          ┌────────▼───────┐
  │  DMZ Network   │          │   Public   │          │  Admin Network │
  │                │          │  Network   │          │                │
  │                │          │            │          │                │
  │ ┌────────────┐ │          │ ┌────────┐ │          │ ┌────────────┐ │
  │ │   React    │ │          │ │  CLI   │ │          │ │  Grafana   │ │
  │ │  Frontend  │ │          │ │Client  │ │          │ │  Prometheus│ │
  │ │ (Nginx)    │ │          │ └────────┘ │          │ │  Admin UI  │ │
  │ └────────────┘ │          │            │          │ └────────────┘ │
  │                │          │            │          │                │
  └────────────────┘          └────────────┘          └────────────────┘
          │                          │                        │
          └──────────────────────────┼────────────────────────┘
                                     │
                      ┌──────────────▼───────────────┐
                      │    Application Network       │
                      │  (Go Backend + Orchestrator) │
                      │                              │
                      │  ┌────────────────────────┐  │
                      │  │  Go Backend API        │  │
                      │  │  (Auth + Orchestration)│  │
                      │  └────────────────────────┘  │
                      │                              │
                      │  ┌────────────────────────┐  │
                      │  │  Orchestrator          │  │
                      │  │  (Go)                  │  │
                      │  └────────────────────────┘  │
                      └───────────────┬──────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │     Service Mesh              │
                      │  (mTLS + Service Discovery)   │
                      │  Istio / Linkerd              │ ← Zero Trust mesh
                      └───────────────┬───────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │     Isolated Agent Pool       │
                      │  (NO Direct External Access)  │
                      │                               │
                      │  ┌──────┐ ┌──────┐ ┌──────┐   │
                      │  │Pass- │ │Theory│ │Choice│   │
                      │  │check │ │Spec  │ │Maker │   │
                      │  └──────┘ └──────┘ └──────┘   │
                      │                               │
                      │  ┌──────┐ ┌──────┐ ┌──────┐   │
                      │  │Prime │ │Crypto│ │ Cmd  │   │
                      │  │Check │ │God   │ │Exec  │   │
                      │  └──────┘ └──────┘ └──────┘   │
                      └───────────────┬───────────────┘
                                      │
                      ┌───────────────▼───────────────┐
                      │   Data Network (Isolated)     │
                      │  PostgreSQL + Redis           │
                      └───────────────────────────────┘

  ---
  2. Open Source Security Components (All Free)

  2.1 Edge Security Layer

  | Component       | Open Source Option                                     | Purpose                             | License                 |
  |-----------------|--------------------------------------------------------|-------------------------------------|-------------------------|
  | DDoS Protection | cloudflare (free tier) or self-hosted iptables + ipset | Mitigate volumetric attacks         | Free / GPLv2            |
  | Reverse Proxy   | Nginx or Traefik                                       | TLS termination, routing            | BSD 2-Clause / MIT      |
  | WAF             | BunkerWeb or ModSecurity + OWASP CRS                   | Web attack prevention               | MIT / Apache-2.0        |
  | API Gateway     | Kong CE or Traefik                                     | API management, rate limiting       | Apache-2.0 / MIT        |
  | Load Balancer   | Nginx or HAProxy                                       | Distribution of traffic             | BSD 2-Clause / GPL-2.0  |
  | Service Mesh    | Istio or Linkerd                                       | mTLS, service-to-service encryption | Apache-2.0 / Apache-2.0 |
  | Secrets Mgmt    | Vault OSS or External Secrets Operator                 | Secure credential storage           | BSL / Apache-2.0        |
  | Network Policy  | Cilium or Calico                                       | K8s network segmentation            | Apache-2.0 / Apache-2.0 |

  2.2 Component Deep Dive

  BunkerWeb (Recommended WAF)

  Why BunkerWeb:
  ✅ All-in-one (Nginx + ModSecurity + Fail2Ban + Crowdssec)
  ✅ Auto-hardening (security headers, TLS config)
  ✅ API protection (rate limiting, bypassing)
  ✅ Docker-native
  ✅ Free community edition
  ✅ OWASP Top 10 protection

  Features:
  - SQL Injection, XSS, CSRF protection
  - HTTP protocol compliance
  - Virtual patching
  - IP reputation (CrowdSec integration)
  - DDoS mitigation (request limiting)

  Docker Compose Example:
  services:
    bunkerweb:
      image: bunkerity/bunkerweb:latest
      ports:
        - "80:8080"
        - "443:8443"
      volumes:
        - ./bw-data:/data
      environment:
        - SERVER_NAME=api.vitruvian.local
        - API_TOKENS_HEADER=X-API-Token
        - RATE_LIMIT_LIMIT=100
        - USE_REVERSE_PROXY=yes
        - REVERSE_PROXY_HOST=backend
        - REVERSE_PROXY_URL=/
        - USE_MODSECURITY=yes
        - MODSECURITY_SEC_RULE_ENGINE=On
        - USE_BLACKLIST=yes
        - BLACKLIST_SETTINGS=403 404 429 499 500-599

  Kong Community Edition (API Gateway)

  Why Kong CE:
  ✅ Open source API gateway
  ✅ Plugin ecosystem (auth, rate limit, ACL)
  ✅ Service discovery integration
  ✅ Developer portal
  ✅ Metrics and monitoring

  Plugins to Enable:
  - jwt: JWT authentication
  - acl: Access control lists
  - rate-limiting: Request throttling
  - request-size-limiting: Payload validation
  - response-templating: Response sanitization
  - cors: Cross-origin policies
  - ip-restriction: IP allowlists
  - hmac-auth: Request signing

  Istio (Service Mesh)

  Why Istio:
  ✅ mTLS for all service-to-service communication
  ✅ Mutual authentication (no spoofing)
  ✅ Authorization policies (who can call what)
  ✅ Traffic management (circuit breaking, retries)
  ✅ Observability (distributed tracing)

  Key Features:
  - Automatic mTLS injection
  - Peer authentication (SERVICE_TLS_MODE_MUTUAL)
  - Request authentication (JWT/OIDC)
  - Authorization policies (ALLOW/DENY rules)
  - Network policies (ingress/egress control)

  ---
  3. Network Segmentation Strategy

  3.1 Kubernetes Namespace Isolation

  Namespaces (Network Segments):

  1. vitruvian-public       (DMZ)
     - Frontend (React)
     - CLI Gateway API
     - Public monitoring dashboards

  2. vitruvian-application  (Application Tier)
     - Go Backend
     - Orchestrator
     - API Gateway (Kong)

  3. vitruvian-agents       (Isolated Agent Pool)
     - password_checker
     - theory_specialist
     - choice_maker
     - command_executor
     - prime_checker
     - crypto_god

  5. vitruvian-data         (Data Tier)
     - PostgreSQL
     - Redis
     - ChromaDB

  6. vitruvian-observability (Monitoring)
     - Prometheus
     - Grafana
     - Loki
     - Tempo
     - Alertmanager

  7. vitruvian-infra        (Infrastructure)
     - Vault
     - Cert-Manager
     - External Secrets Operator

  3.2 Network Policies (Cilium)

  # Default: Deny all traffic
  apiVersion: cilium.io/v2
  kind: CiliumNetworkPolicy
  metadata:
    namespace: vitruvian-agents
    name: agent-isolation
  spec:
    endpointSelector:
      matchLabels:
        tier: agents
    ingress:
      # Only allow traffic from orchestrator namespace
      - fromEndpoints:
          - matchLabels:
              k8s:io.kubernetes.pod.namespace: vitruvian-application
        toPorts:
          - ports:
              - port: "8080"
                protocol: TCP
              - port: "9000"
                protocol: TCP
              - port: "8100"
                protocol: TCP
    egress:
      # Allow DNS
      - toEndpoints:
          - matchLabels:
              k8s:io.kubernetes.pod.namespace: kube-system
              k8s:k8s-app: kube-dns
        toPorts:
          - ports:
              - port: "53"
                protocol: ANY
      # Allow database access
      - toEndpoints:
          - matchLabels:
              k8s:io.kubernetes.pod.namespace: vitruvian-data
        toPorts:
          - ports:
              - port: "5432"
                protocol: TCP
              - port: "6379"
                protocol: TCP
      # Deny all other egress (no internet, no other namespaces)

  ---
  4. Authentication & Authorization

  4.1 Multi-Factor Auth Strategy

  Authentication Layers:

  ┌─────────────────────────────────────────────────────────────┐
  │  Layer 1: Network Authentication                            │
  │  ├─ mTLS between services (Istio)                           │
  │  ├─ Client certificate validation (optional for users)      │
  │  └─ Service account tokens (K8s)                            │
  ├─────────────────────────────────────────────────────────────┤
  │  Layer 2: API Authentication                                │
  │  ├─ JWT tokens (short-lived: 15min)                         │
  │  ├─ API keys (hashed, scoped)                               │
  │  └─ Session tokens (refresh token flow)                     │
  ├─────────────────────────────────────────────────────────────┤
  │  Layer 3: Application Authorization                         │
  │  ├─ RBAC (Role-Based Access Control)                        │
  │  ├─ ABAC (Attribute-Based: time, IP, resource)              │
  │  └─ Resource-level permissions                              │
  └─────────────────────────────────────────────────────────────┘

  4.2 JWT Implementation (Go)

  // internal/auth/jwt.go
  package auth

  import (
      "crypto/rsa"
      "time"

      "github.com/golang-jwt/jwt/v5"
  )

  type Claims struct {
      UserID      string            `json:"user_id"`
      Email       string            `json:"email"`
      Roles       []string          `json:"roles"`
      Permissions []string          `json:"permissions"`
      SessionID   string            `json:"session_id"`
      jwt.RegisteredClaims
  }

  type JWTManager struct {
      privateKey   *rsa.PrivateKey
      publicKey    *rsa.PublicKey
      accessToken  time.Duration
      refreshToken time.Duration
  }

  func (j *JWTManager) GenerateTokenPair(userID, email string, roles []string) (accessToken, refreshToken string, err error) {
      // Access Token (15 minutes)
      accessClaims := Claims{
          UserID:      userID,
          Email:       email,
          Roles:       roles,
          Permissions: j.getPermissions(roles),
          SessionID:   uuid.New().String(),
          RegisteredClaims: jwt.RegisteredClaims{
              ExpiresAt: jwt.NewNumericDate(time.Now().Add(j.accessToken)),
              IssuedAt:  jwt.NewNumericDate(time.Now()),
              NotBefore: jwt.NewNumericDate(time.Now()),
              Issuer:    "vitruvian.platform",
          },
      }

      accessToken, err = jwt.NewWithClaims(jwt.SigningMethodRS256, accessClaims).SignedString(j.privateKey)

      // Refresh Token (7 days)
      refreshClaims := jwt.RegisteredClaims{
          ExpiresAt: jwt.NewNumericDate(time.Now().Add(j.refreshToken)),
          IssuedAt:  jwt.NewNumericDate(time.Now()),
          Issuer:    "vitruvian.platform",
          Subject:   userID,
      }

      refreshToken, err = jwt.NewWithClaims(jwt.SigningMethodRS256, refreshClaims).SignedString(j.privateKey)

      return
  }

  // Store refresh token hash in DB (NOT plaintext)
  func (j *JWTManager) StoreRefreshToken(userID, tokenHash string) error {
      // Use bcrypt/argon2 to hash
      hashed, _ := bcrypt.GenerateFromPassword([]byte(tokenHash), bcrypt.DefaultCost)

      // Store in PostgreSQL
      return db.RefreshToken.Create(&models.RefreshToken{
          UserID:    userID,
          TokenHash: string(hashed),
          ExpiresAt: time.Now().Add(j.refreshToken),
      })
  }

  4.3 Role-Based Access Control (RBAC)

  -- PostgreSQL RBAC Schema

  CREATE TABLE roles (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(50) UNIQUE NOT NULL,
      description TEXT,
      created_at TIMESTAMP DEFAULT NOW()
  );

  CREATE TABLE permissions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      resource VARCHAR(100) NOT NULL,  -- e.g., "password_checker", "theory_specialist"
      action VARCHAR(50) NOT NULL,      -- e.g., "read", "write", "admin"
      description TEXT
  );

  CREATE TABLE role_permissions (
      role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
      permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
      PRIMARY KEY (role_id, permission_id)
  );

  CREATE TABLE user_roles (
      user_id UUID REFERENCES users(id) ON DELETE CASCADE,
      role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
      assigned_at TIMESTAMP DEFAULT NOW(),
      assigned_by UUID REFERENCES users(id),
      PRIMARY KEY (user_id, role_id)
  );

  -- Predefined Roles
  INSERT INTO roles (name, description) VALUES
      ('admin', 'Full system access'),
      ('operator', 'Can execute crypto operations'),
      ('auditor', 'Read-only access for compliance'),
      ('user', 'Basic authenticated user');

  -- Predefined Permissions
  INSERT INTO permissions (resource, action) VALUES
      ('password_checker', 'read'),
      ('password_checker', 'write'),
      ('theory_specialist', 'read'),
      ('theory_specialist', 'write'),
      ('orchestrator', 'execute'),
      ('users', 'manage'),
      ('system', 'admin');

  ---
  5. API Security Headers & Configuration

  5.1 Nginx/BunkerWeb Security Headers

  # /etc/nginx/conf.d/security-headers.conf

  # Prevent clickjacking
  add_header X-Frame-Options "SAMEORIGIN" always;

  # Prevent MIME type sniffing
  add_header X-Content-Type-Options "nosniff" always;

  # Enable XSS filter
  add_header X-XSS-Protection "1; mode=block" always;

  # Content Security Policy
  add_header Content-Security-Policy "
      default-src 'self';
      script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net;
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
      font-src 'self' https://fonts.gstatic.com;
      img-src 'self' data: https:;
      connect-src 'self' https://api.vitruvian.local;
      frame-ancestors 'none';
      base-uri 'self';
      form-action 'self';
  " always;

  # Referrer Policy
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;

  # Permissions Policy (formerly Feature-Policy)
  add_header Permissions-Policy "
      geolocation=(),
      microphone=(),
      camera=(),
      payment=(),
      usb=(),
      magnetometer=(),
      gyroscope=()
  " always;

  # Strict Transport Security (HSTS)
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

  # Remove server version
  server_tokens off;

  # Disable unwanted methods
  if ($request_method !~ ^(GET|HEAD|POST|PUT|DELETE|OPTIONS)$) {
      return 405;
  }

  5.2 Go Middleware Stack

  // internal/interfaces/rest/middleware/security.go

  package middleware

  import (
      "strings"
      "time"

      "github.com/go-chi/chi/v5/middleware"
      "golang.org/x/time/rate"
  )

  // Security middleware stack
  func SecurityMiddleware() func(http.Handler) http.Handler {
      return func(next http.Handler) http.Handler {
          return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
              // Apply all security headers
              w.Header().Set("X-Frame-Options", "SAMEORIGIN")
              w.Header().Set("X-Content-Type-Options", "nosniff")
              w.Header().Set("X-XSS-Protection", "1; mode=block")
              w.Header().Set("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
              w.Header().Set("Content-Security-Policy", cspHeader)
              w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
              w.Header().Set("Permissions-Policy", permissionsPolicy)

              next.ServeHTTP(w, r)
          })
      }
  }

  // Rate limiting per user/IP
  func RateLimitMiddleware(limiter *rate.Limiter) func(http.Handler) http.Handler {
      return func(next http.Handler) http.Handler {
          return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
              if !limiter.Allow() {
                  http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
                  return
              }
              next.ServeHTTP(w, r)
          })
      }
  }

  // Request size limiting
  func MaxBodySize(maxBytes int64) func(http.Handler) http.Handler {
      return func(next http.Handler) http.Handler {
          return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
              r.Body = http.MaxBytesReader(w, r.Body, maxBytes)
              next.ServeHTTP(w, r)
          })
      }
  }

  // Request ID for tracing
  func RequestID() func(http.Handler) http.Handler {
      return middleware.RequestID
  }

  // Logger with security events
  func SecurityLogger(logger *zap.Logger) func(http.Handler) http.Handler {
      return func(next http.Handler) http.Handler {
          return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
              start := time.Now()

              // Wrap ResponseWriter to capture status
              ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)

              next.ServeHTTP(ww, r)

              // Log security-relevant events
              if ww.Status() >= 400 || strings.Contains(r.URL.Path, "admin") {
                  logger.Info("security_event",
                      zap.String("method", r.Method),
                      zap.String("path", r.URL.Path),
                      zap.Int("status", ww.Status()),
                      zap.String("ip", r.RemoteAddr),
                      zap.String("user_agent", r.UserAgent()),
                      zap.Duration("latency", time.Since(start)),
                  )
              }
          })
      }
  }

  ---
  6. Secrets Management

  6.1 Vault Integration

  # Vault Dev Server (for production, use Raft storage)
  services:
    vault:
      image: hashicorp/vault:latest
      ports:
        - "8200:8200"
      environment:
        - VAULT_DEV_ROOT_TOKEN_ID=dev-only-token
        - VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200
      cap_add:
        - IPC_LOCK

  // internal/infrastructure/vault/client.go

  package vault

  import (
      "context"
      "fmt"

      "github.com/hashicorp/vault/api"
  )

  type VaultClient struct {
      client *api.Client
  }

  func NewClient(addr, token string) (*VaultClient, error) {
      config := api.DefaultConfig()
      config.Address = addr

      client, err := api.NewClient(config)
      if err != nil {
          return nil, err
      }

      client.SetToken(token)
      return &VaultClient{client: client}, nil
  }

  func (v *VaultClient) GetSecret(ctx context.Context, path string) (map[string]interface{}, error) {
      secret, err := v.client.Logical().Read(path)
      if err != nil {
          return nil, err
      }

      if secret == nil {
          return nil, fmt.Errorf("secret not found: %s", path)
      }

      return secret.Data, nil
  }

  // Usage:
  // dbSecret, _ := vault.GetSecret(ctx, "secret/data/vitruvian/postgresql")
  // password := dbSecret["password"].(string)

  6.2 Kubernetes Secrets (Sealed Secrets)

  # Install Sealed Secrets
  # kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

  # Create sealed secret (encrypted, can commit to Git)
  apiVersion: bitnami.com/v1alpha1
  kind: SealedSecret
  metadata:
    name: postgresql-credentials
    namespace: vitruvian-data
  spec:
    encryptedData:
      username: AgBy3i4OJSWK+PiTySY... (encrypted)
      password: Ga7gYkA7nY2T... (encrypted)
    template:
      metadata:
        name: postgresql-credentials
        namespace: vitruvian-data
      type: Opaque

  ---
  7. Defect-Tolerant Systems (High Availability)

  7.1 Fault Isolation Patterns

  Defect Tolerance Strategy:

  1. Circuit Breaker Pattern
     - Fail fast when service is down
     - Prevent cascading failures
     - Auto-recovery with half-open state

  2. Bulkhead Pattern
     - Resource isolation per service
     - Prevent resource exhaustion
     - Separate thread pools/connection pools

  3. Retry with Exponential Backoff
     - Transient failure recovery
     - Jitter to prevent thundering herd

  4. Timeout Enforcement
     - Prevent hanging requests
     - Per-endpoint timeouts

  5. Health Check Probes
     - Liveness: Restart if dead
     - Readiness: Remove from load balancer if not ready
     - Startup: Wait for app initialization

  7.2 Circuit Breaker Implementation (Go)

  // internal/infrastructure/circuitbreaker/breaker.go

  package circuitbreaker

  import (
      "errors"
      "sync"
      "time"
  )

  type State int

  const (
      StateClosed State = iota
      StateHalfOpen
      StateOpen
  )

  type CircuitBreaker struct {
      maxFailures     int
      resetTimeout    time.Duration
      failureCount    int
      lastFailTime    time.Time
      state           State
      mu              sync.RWMutex
  }

  func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
      return &CircuitBreaker{
          maxFailures:  maxFailures,
          resetTimeout: resetTimeout,
          state:        StateClosed,
      }
  }

  func (cb *CircuitBreaker) Execute(fn func() error) error {
      if !cb.canProceed() {
          return errors.New("circuit breaker is open")
      }

      err := fn()

      cb.mu.Lock()
      defer cb.mu.Unlock()

      if err != nil {
          cb.onFailure()
          return err
      }

      cb.onSuccess()
      return nil
  }

  func (cb *CircuitBreaker) canProceed() bool {
      cb.mu.RLock()
      defer cb.mu.RUnlock()

      if cb.state == StateClosed {
          return true
      }

      if cb.state == StateOpen {
          if time.Since(cb.lastFailTime) > cb.resetTimeout {
              cb.state = StateHalfOpen
              return true
          }
          return false
      }

      return true // StateHalfOpen
  }

  func (cb *CircuitBreaker) onFailure() {
      cb.failureCount++
      cb.lastFailTime = time.Now()

      if cb.failureCount >= cb.maxFailures {
          cb.state = StateOpen
      }
  }

  func (cb *CircuitBreaker) onSuccess() {
      cb.failureCount = 0
      if cb.state == StateHalfOpen {
          cb.state = StateClosed
      }
  }

  7.3 Retry with Jitter

  // internal/infrastructure/retry/retry.go

  package retry

  import (
      "context"
      "math/rand"
      "time"
  )

  type RetryConfig struct {
      MaxAttempts int
      BaseDelay   time.Duration
      MaxDelay    time.Duration
  }

  func DoWithContext(ctx context.Context, config RetryConfig, fn func() error) error {
      var lastErr error

      for attempt := 0; attempt < config.MaxAttempts; attempt++ {
          if attempt > 0 {
              // Exponential backoff with jitter
              delay := config.BaseDelay * time.Duration(1<<uint(attempt-1))
              jitter := time.Duration(rand.Float64() * float64(delay) * 0.1)
              delay = delay + jitter

              if delay > config.MaxDelay {
                  delay = config.MaxDelay
              }

              select {
              case <-time.After(delay):
              case <-ctx.Done():
                  return ctx.Err()
              }
          }

          err := fn()
          if err == nil {
              return nil
          }

          lastErr = err
      }

      return lastErr
  }

  7.4 Kubernetes Probes

  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: orchestrator
    namespace: vitruvian-application
  spec:
    replicas: 3
    template:
      spec:
        containers:
        - name: orchestrator
          image: vitruvian/orchestrator:latest
          ports:
          - containerPort: 8200
          env:
          - name: POD_IP
            valueFrom:
              fieldRef:
                fieldPath: status.podIP
          # Liveness: Restart if container hangs
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8200
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          # Readiness: Remove from LB if not ready
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8200
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 2
            successThreshold: 1
          # Startup: Wait for slow init
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8200
            initialDelaySeconds: 0
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 30  # 30 * 5s = 150s max startup time
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"

  ---
  8. Logging, Monitoring & Alerting

  8.1 Structured Logging (Go)

  // internal/infrastructure/logging/logger.go

  package logging

  import (
      "go.uber.org/zap"
      "go.uber.org/zap/zapcore"
  )

  func NewLogger(env string) *zap.Logger {
      var config zap.Config

      if env == "production" {
          config = zap.NewProductionConfig()
          config.EncoderConfig.TimeKey = "timestamp"
          config.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
      } else {
          config = zap.NewDevelopmentConfig()
      }

      logger, _ := config.Build()
      return logger
  }

  // Usage:
  logger.Info("user_login",
      zap.String("user_id", userID),
      zap.String("ip", r.RemoteAddr),
      zap.String("user_agent", r.UserAgent()),
      zap.Bool("success", true),
  )

  8.2 Prometheus Metrics

  // internal/infrastructure/metrics/metrics.go

  package metrics

  import (
      "github.com/prometheus/client_golang/prometheus"
      "github.com/prometheus/client_golang/prometheus/promauto"
  )

  var (
      // HTTP metrics
      HttpRequestsTotal = promauto.NewCounterVec(
          prometheus.CounterOpts{
              Name: "http_requests_total",
              Help: "Total number of HTTP requests",
          },
          []string{"method", "endpoint", "status"},
      )

      HttpRequestDuration = promauto.NewHistogramVec(
          prometheus.HistogramOpts{
              Name:    "http_request_duration_seconds",
              Help:    "HTTP request latency",
              Buckets: prometheus.DefBuckets,
          },
          []string{"method", "endpoint"},
      )

      // Business metrics
      AgentRequestsTotal = promauto.NewCounterVec(
          prometheus.CounterOpts{
              Name: "agent_requests_total",
              Help: "Total agent invocations",
          },
          []string{"agent", "operation", "status"},
      )

      AgentRequestDuration = promauto.NewHistogramVec(
          prometheus.HistogramOpts{
              Name:    "agent_request_duration_seconds",
              Help:    "Agent request latency",
              Buckets: []float64{0.1, 0.5, 1, 2, 5, 10, 30},
          },
          []string{"agent", "operation"},
      )

      // Security metrics
      AuthFailuresTotal = promauto.NewCounterVec(
          prometheus.CounterOpts{
              Name: "auth_failures_total",
              Help: "Authentication failures",
          },
          []string{"method"}, // jwt, api_key, session
      )

      RateLimitHitsTotal = promauto.NewCounterVec(
          prometheus.CounterOpts{
              Name: "rate_limit_hits_total",
              Help: "Rate limit violations",
          },
          []string{"user_id", "endpoint"},
      )
  )

  8.3 Alertmanager Rules

  # alertmanager-config.yml
  groups:
    - name: security_alerts
      interval: 30s
      rules:
        - alert: HighAuthFailureRate
          expr: rate(auth_failures_total[5m]) > 10
          for: 2m
          labels:
            severity: warning
            category: security
          annotations:
            summary: "High authentication failure rate"
            description: "More than 10 auth failures/sec for 2 minutes"

        - alert: RateLimitAbuse
          expr: rate(rate_limit_hits_total[1m]) > 50
          for: 1m
          labels:
            severity: critical
            category: security
          annotations:
            summary: "Possible DDoS attack"
            description: "Rate limit hit >50 times/sec"

        - alert: AgentUnhealthy
          expr: up{job=~".*agent.*"} == 0
          for: 1m
          labels:
            severity: critical
            category: availability
          annotations:
            summary: "Agent service down"
            description: "{{ $labels.job }} is down"

        - alert: DatabaseConnectionPoolExhausted
          expr: pg_stat_activity_count / pg_settings_max_connections > 0.9
          for: 2m
          labels:
            severity: critical
            category: database
          annotations:
            summary: "Database connection pool nearly full"
            description: "90%+ of connections used"

  ---
  9. Security Best Practices Checklist

  9.1 Development Phase

  ✅ Code Security
    ├─ Static analysis (golangci-lint, SonarQube)
    ├─ Dependency scanning (Snyk, Trivy)
    ├─ SAST/DAST in CI/CD
    ├─ Code review requirements (2-person approval)
    ├─ Secret detection (git-secrets, truffleHog)
    └─ SBOM generation (Syft, SPDX)

  ✅ Testing
    ├─ Unit tests (>80% coverage)
    ├─ Integration tests
    ├─ Security-focused tests (injection, auth bypass)
    ├─ Chaos engineering (Chaos Mesh, Litmus)
    └─ Load testing (K6, Locust)

  9.2 Deployment Phase

  ✅ Container Security
    ├─ Minimal base images (alpine, distroless)
    ├─ Run as non-root user
    ├─ Read-only root filesystem
    ├─ Drop all capabilities (no setuid/setgid)
    ├─ Resource limits (CPU, memory)
    ├─ Seccomp profiles
    ├─ AppArmor/SELinux policies
    └─ Image signing (cosign, Notary)

  ✅ Kubernetes Security
    ├─ Network policies (deny by default)
    ├─ PodSecurityStandards (restricted)
    ├─ RBAC (least privilege)
    ├─ Service account automation
    ├─ Ingress restrictions
    ├─ Anti-affinity rules
    └─ Taints/tolerances for sensitive workloads

  9.3 Runtime Phase

  ✅ Monitoring
    ├─ Real-time log aggregation
    ├─ Anomaly detection (unsupervised ML)
    ├─ Behavior baselining
    ├─ File integrity monitoring (Falco)
    ├─ Runtime security (Falco, Cilium)
    └─ SIEM integration (Wazuh, OpenSearch Security)

  ✅ Incident Response
    ├─ Runbooks for common incidents
    ├─ Automated containment (auto-block IP)
    ├─ Backup/restore procedures
    ├─ Post-mortem process
    └─ Security training for operators

  ---
  10. Docker Compose Reference (Full Stack)

  # docker-compose.security.yml
  version: '3.8'

  services:
    # === Edge Layer ===
    bunkerweb:
      image: bunkerity/bunkerweb:latest
      ports:
        - "80:8080"
        - "443:8443"
      volumes:
        - ./bw-data:/data
      environment:
        - SERVER_NAME=api.vitruvian.local
        - API_TOKENS_HEADER=X-API-Token
        - RATE_LIMIT_LIMIT=100
        - USE_MODSECURITY=yes
        - MODSECURITY_SEC_RULE_ENGINE=On
      networks:
        - dmz
      restart: unless-stopped

    # === Application Layer ===
    kong:
      image: kong:latest
      ports:
        - "8001:8001"  # Admin
        - "8443:8443"  # Proxy HTTPS
      environment:
        - KONG_DATABASE=off
        - KONG_PROXY_ACCESS_LOG=/dev/stdout
        - KONG_ADMIN_ACCESS_LOG=/dev/stdout
        - KONG_ADMIN_LISTEN=0.0.0.0:8001
      networks:
        - dmz
        - application
      restart: unless-stopped

    backend:
      build: ./backend
      environment:
        - DB_HOST=postgres
        - REDIS_HOST=redis
        - JWT_PRIVATE_KEY_PATH=/run/secrets/jwt_private
      secrets:
        - jwt_private
        - db_password
      networks:
        - application
        - data
      restart: unless-stopped

    orchestrator:
      image: vitruvian/orchestrator:latest
      environment:
        - CHOICE_MAKER_URL=http://choice-maker:8081
      networks:
        - application
        - agents
      restart: unless-stopped

    # === Agent Pool (Isolated) ===
    password-checker:
      image: vitruvian/password-checker:latest
      networks:
        - agents
        - data
      restart: unless-stopped

    theory-specialist:
      image: vitruvian/theory-specialist:latest
      networks:
        - agents
        - data
      restart: unless-stopped

    command-executor:
      image: vitruvian/command-executor:latest
      security_opt:
        - no-new-privileges:true
      cap_drop:
        - ALL
      read_only: true
      tmpfs:
        - /tmp:noexec,nosuid,size=100m
      networks:
        - agents
      restart: unless-stopped

    # === Data Layer (Isolated) ===
    postgres:
      image: postgres:16-alpine
      environment:
        - POSTGRES_USER_FILE=/run/secrets/db_user
        - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
        - POSTGRES_DB=vitruvian
      secrets:
        - db_user
        - db_password
      volumes:
        - postgres-data:/var/lib/postgresql/data
      networks:
        - data
      restart: unless-stopped

    redis:
      image: redis:7-alpine
      command: redis-server --requirepass ${REDIS_PASSWORD}
      networks:
        - data
      restart: unless-stopped

    # === Observability ===
    prometheus:
      image: prom/prometheus:latest
      ports:
        - "9090:9090"
      volumes:
        - ./prometheus.yml:/etc/prometheus/prometheus.yml
        - prometheus-data:/prometheus
      networks:
        - observability
        - application
        - agents
      restart: unless-stopped

    grafana:
      image: grafana/grafana:latest
      ports:
        - "3000:3000"
      environment:
        - GF_SECURITY_ADMIN_PASSWORD_FILE=/run/secrets/grafana_admin
      secrets:
        - grafana_admin
      volumes:
        - grafana-data:/var/lib/grafana
      networks:
        - observability
      restart: unless-stopped

  networks:
    dmz:
      driver: bridge
      internal: false  # Can access internet
    application:
      driver: bridge
      internal: true  # Isolated
    agents:
      driver: bridge
      internal: true  # NO external access
    data:
      driver: bridge
      internal: true
    observability:
      driver: bridge
      internal: true

  secrets:
    jwt_private:
      file: ./secrets/jwt_private.pem
    db_user:
      file: ./secrets/db_user.txt
    db_password:
      file: ./secrets/db_password.txt
    grafana_admin:
      file: ./secrets/grafana_admin.txt

  volumes:
    postgres-data:
    prometheus-data:
    grafana-data:

  ---
  11. Final Security Recommendations

  Immediate Actions (Week 1-2)

  1. ✅ Implement network policies (deny all, allow specific)
  2. ✅ Add BunkerWeb WAF with OWASP CRS
  3. ✅ Enable mTLS with Istio in agent pool
  4. ✅ Implement JWT auth with Kong
  5. ✅ Add rate limiting (per IP, per user)
  6. ✅ Set up logging (Loki + Promtail)

  Short-Term (Month 1)

  1. ✅ Migrate to non-root containers
  2. ✅ Implement circuit breakers and retries
  3. ✅ Add Falco for runtime security
  4. ✅ Set up Vault for secrets
  5. ✅ Create security dashboards (Grafana)
  6. ✅ Implement backup/restore procedures

  Long-Term (Month 2-3)

  1. ✅ Chaos engineering tests
  2. ✅ Automated security scanning in CI/CD
  3. ✅ Incident response runbooks
  4. ✅ Security audit (external firm)
  5. ✅ Penetration testing
  6. ✅ Compliance certification (SOC2, ISO27001)


