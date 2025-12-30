# 📝 Disabled Services - TODO List

This document lists all services/components that have been commented out because they don't exist yet.

---

## 🔴 Disabled Services

### 1. Backend (Go Backend API)

**Status**: TODO - Needs to be created

**Description**: Central Go backend with authentication, authorization, and API management

**Location in Code**:
- Service definition: `docker-compose.yml:324-390`
- Health check: `scripts/health-check.sh:29`
- Status check: `scripts/service-status.sh:26`
- URLs output: `run_all.sh:327`

**What's Commented Out**:
```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  ports:
    - "8000:8000"
  depends_on:
    - postgres
    - redis
    - orchestrator
```

**Required to Create**:
- [ ] Go backend service structure
- [ ] Authentication/Authorization (JWT)
- [ ] User management endpoints
- [ ] API key management
- [ ] Session management
- [ ] Integration with Orchestrator

**Related Files to Update When Created**:
1. Uncomment in `docker-compose.yml`
2. Uncomment in `scripts/health-check.sh`
3. Uncomment in `scripts/service-status.sh`
4. Uncomment in `run_all.sh`
5. Uncomment in `.env.example`
6. Uncomment migration targets in `Makefile`
7. Uncomment backup/restore targets in `Makefile`

---

## 🟡 Partially Disabled Infrastructure

### 2. PostgreSQL

**Status**: Exists in docker-compose.yml but may not have database initialization

**What's Included**:
- PostgreSQL 16 Alpine image
- Health checks
- Volume persistence
- Environment variable configuration

**May Need**:
- [ ] Database initialization script (`scripts/init-db.sql`)
- [ ] Migration system setup
- [ ] Schema definitions

---

### 3. Redis

**Status**: Exists in docker-compose.yml

**What's Included**:
- Redis 7 Alpine image
- Health checks
- Volume persistence
- Password protection

**Ready to Use**: ✅ (once backend is created)

---

## 🟢 Working Services

These services are **active and working**:

1. ✅ **password-checker** - Python ensemble ML password strength
2. ✅ **theory-specialist** - Python RAG-based Q&A
3. ✅ **choice-maker** - Python NLP intent/entity classification
4. ✅ **command-executor** - Rust cryptographic operations
5. ✅ **prime-checker** - Go primality testing
6. ✅ **orchestrator** - Go routing and coordination
7. ✅ **react-frontend** - TypeScript React UI

---

## 📋 Backend Implementation Checklist

When you're ready to create the backend service, follow this checklist:

### Phase 1: Project Setup
- [ ] Create `backend/` directory structure
- [ ] Initialize Go module (`go mod init github.com/yourusername/vitruvian-backend`)
- [ ] Create Dockerfile
- [ ] Add to docker-compose.yml (uncomment)

### Phase 2: Core Features
- [ ] Server setup (Chi router or Gin)
- [ ] Configuration loading (Viper)
- [ ] Structured logging (Zap)
- [ ] Health check endpoints
- [ ] OpenAPI/Swagger documentation

### Phase 3: Database Layer
- [ ] GORM models (User, Session, APIToken, etc.)
- [ ] Migration system (Goose or golang-migrate)
- [ ] Database connection pooling
- [ ] Repository pattern implementation

### Phase 4: Authentication
- [ ] JWT token generation/validation
- [ ] Password hashing (bcrypt/argon2)
- [ ] Session management
- [ ] API key generation/validation
- [ ] Middleware for auth

### Phase 5: Authorization
- [ ] RBAC implementation
- [ ] Permission checking
- [ ] Role assignment
- [ ] ACL middleware

### Phase 6: Integration
- [ ] Orchestrator client
- [ ] Agent pool management
- [ ] Request/response handling
- [ ] Error handling

### Phase 7: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] API tests
- [ ] Load tests

### Phase 8: Deployment
- [ ] Docker image build
- [ ] Environment configuration
- [ ] Health checks
- [ ] Logging/metrics
- [ ] Uncomment all references in scripts

---

## 🚀 Quick Enable Guide

Once backend is created, uncomment these lines:

### 1. docker-compose.yml
```bash
# Uncomment lines 324-390
```

### 2. scripts/health-check.sh
```bash
# Uncomment line 29
```

### 3. scripts/service-status.sh
```bash
# Uncomment line 26
```

### 4. run_all.sh
```bash
# Uncomment line 327
```

### 5. .env.example
```bash
# Uncomment lines 25-36
```

### 6. Makefile
```bash
# Uncomment migrate targets (lines 311-329)
# Uncomment backup/restore targets (lines 335-345)
```

---

## 📊 Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  React Frontend (5173)                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                          │
│  Orchestrator (8200) ──────► Agent Pool                    │
│  ├─ Password Checker (9000)                                │
│  ├─ Theory Specialist (8100)                               │
│  ├─ Choice Maker (8081)                                    │
│  ├─ Command Executor (8085)                                │
│  └─ Prime Checker (5000)                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│  PostgreSQL (5432)  ←  TODO: Needs schema & migrations     │
│  Redis (6379)        ←  Ready to use                       │
└─────────────────────────────────────────────────────────────┘

⚠️  Backend layer (8000) - MISSING - TODO: Create Go backend
```

---

## 🎯 Next Steps

1. **Create Backend Service** - Start with the Go backend structure
2. **Implement Auth** - JWT, sessions, API keys
3. **Database Schema** - Define user tables, roles, permissions
4. **API Endpoints** - REST API for frontend consumption
5. **Testing** - Comprehensive test coverage
6. **Uncomment Services** - Enable all commented references

---

**Last Updated**: $(date)
**Version**: 1.0.0
