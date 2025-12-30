# 🚀 Vitruvian Platform - Operations Guide

Complete guide for managing the Vitruvian Platform services.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Available Commands](#available-commands)
3. [Service Management](#service-management)
4. [Health Monitoring](#health-monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## 🎯 Quick Start

### First Time Setup

```bash
# 1. Clone repository (if not already done)
cd /home/andrei/licenta/code

# 2. Install dependencies
make install

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Build all services
make build

# 5. Start all services
make start

# 6. Verify health
make health
```

### Daily Workflow

```bash
# Start services
./run_all.sh start

# Check status
./run_all.sh status

# View logs
./run_all.sh logs

# Stop when done
./run_all.sh stop
```

---

## 🎮 Available Commands

### Using Make (Recommended)

```bash
make help                    # Show all available targets
make build                   # Build all service images
make start                   # Start all services
make stop                    # Stop all services
make restart                 # Restart all services
make status                  # Show service status
make health                  # Run health checks
make logs                    # View all logs (follow mode)
make clean                   # Stop and remove everything
```

### Using run_all.sh Script

```bash
./run_all.sh help            # Show help message
./run_all.sh start           # Start all services
./run_all.sh stop            # Stop all services
./run_all.sh restart         # Restart all services
./run_all.sh build           # Build all images
./run_all.sh status          # Show service status
./run_all.sh health          # Run health checks
./run_all.sh logs            # View logs (all services)
./run_all.sh logs <service>  # View logs for specific service
./run_all.sh clean           # Stop and remove everything
```

---

## 🛠️ Service Management

### Individual Service Control

#### Start/Stop Specific Services

```bash
# Using Make
make start-agent SERVICE=password-checker
make stop-agent SERVICE=orchestrator
make restart-agent SERVICE=backend

# Using Docker Compose directly
docker compose up -d postgres redis              # Start infrastructure
docker compose up -d password-checker             # Start specific agent
docker compose stop orchestrator                  # Stop specific service
docker compose restart backend                    # Restart specific service
```

#### Rebuild Specific Service

```bash
# Using Make
make rebuild SERVICE=backend

# Using Docker Compose
docker compose up -d --build backend
```

### Service Groups

```bash
# Infrastructure only (PostgreSQL, Redis)
./run_all.sh infra
# or
make start-dependencies

# Agents only (no infrastructure)
./run_all.sh agents
```

---

## 📊 Health Monitoring

### Health Checks

```bash
# Full health check with 120s timeout
make health
# or
./run_all.sh health

# Custom timeout (60 seconds)
./scripts/health-check.sh 60

# Quick status (no waiting)
./scripts/health-check.sh --quick
```

### Service Status

```bash
# Summary view
./run_all.sh status
# or
./scripts/service-status.sh summary

# Detailed view for specific service
./scripts/service-status.sh detailed vitruvian-orchestrator

# Watch mode (auto-refresh every 5s)
./scripts/service-status.sh watch 5
```

### Logs

```bash
# All services, follow mode
make logs
# or
./run_all.sh logs

# Specific service
make logs-agent SERVICE=password-checker
./run_all.sh logs orchestrator

# Last 100 lines
make logs-tail

# Export logs
make logs-json
```

### Resource Usage

```bash
# Live resource usage
make top

# Using Docker directly
docker stats
```

---

## 🔧 Troubleshooting

### Service Won't Start

```bash
# 1. Check service logs
docker compose logs <service>

# 2. Check if port is already in use
netstat -tuln | grep <port>
# or
lsof -i :<port>

# 3. Check Docker disk space
docker system df

# 4. Clean up if needed
docker system prune -a
```

### Health Check Failures

```bash
# 1. Run health check in verbose mode
./scripts/health-check.sh --watch 2

# 2. Check individual service health
curl http://localhost:9000/health    # Password Checker
curl http://localhost:8100/health    # Theory Specialist
curl http://localhost:8081/health    # Choice Maker
curl http://localhost:8085/health    # Command Executor
curl http://localhost:5000/health    # Prime Checker
curl http://localhost:8200/health    # Orchestrator
curl http://localhost:8000/health    # Backend

# 3. Check container health status
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Database Issues

```bash
# 1. Check PostgreSQL logs
docker compose logs postgres

# 2. Connect to database
docker exec -it vitruvian-postgres psql -U vitruvian -d vitruvian

# 3. Restart database
docker compose restart postgres

# 4. Reset database (WARNING: deletes data)
make clean
docker volume rm vitruvian_postgres_data
make start
```

### Performance Issues

```bash
# 1. Check resource usage
docker stats

# 2. Identify slow services
make top

# 3. Scale services (if needed)
docker compose up -d --scale password-checker=2

# 4. Check logs for errors
make logs | grep -i error
```

---

## 🎓 Best Practices

### Development Workflow

```bash
# 1. Start infrastructure only
./run_all.sh infra

# 2. Start specific agents you're working on
docker compose up -d password-checker choice-maker

# 3. View logs in real-time
docker compose logs -f password-checker

# 4. Rebuild on changes
docker compose up -d --build password-checker

# 5. Stop when done
docker compose stop
```

### Production Workflow

```bash
# 1. Build with no cache
make build-no-cache

# 2. Run health checks before starting
make health

# 3. Start services
make start

# 4. Monitor health
./scripts/health-check.sh --watch 30

# 5. Regular backups
make backup
```

### Environment Management

```bash
# Development
export DEV_MODE=true
export DEBUG_LOGGING=true
export HOT_RELOAD=true

# Production
export DEV_MODE=false
export DEBUG_LOGGING=false
export JWT_SECRET=<your-secure-secret>
```

### Resource Limits

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '0.5'
      memory: 1G
```

---

## 📝 Service URLs Reference

| Service | URL | Health Check |
|---------|-----|--------------|
| **Backend API** | http://localhost:8000 | /health |
| **Orchestrator** | http://localhost:8200 | /health |
| **React Frontend** | http://localhost:5173 | /health |
| **Password Checker** | http://localhost:9000 | /health |
| **Theory Specialist** | http://localhost:8100 | /health |
| **Choice Maker** | http://localhost:8081 | /health |
| **Command Executor** | http://localhost:8085 | /health |
| **Prime Checker** | http://localhost:5000 | /health |
| **PostgreSQL** | localhost:5432 | - |
| **Redis** | localhost:6379 | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | (admin/admin) |

---

## 🧹 Cleanup Commands

```bash
# Stop services (keep data)
make stop

# Stop and remove containers (keep data)
docker compose down

# Stop and remove everything including volumes (WARNING: deletes data)
make clean
# or
docker compose down -v

# Clean unused images
make clean-images

# Clean everything
make clean-all
```

---

## 🔐 Security Checklist

- [ ] Changed default passwords in `.env`
- [ ] Set strong `JWT_SECRET`
- [ ] Changed default Grafana password
- [ ] Enabled HTTPS in production
- [ ] Configured firewall rules
- [ ] Set up regular backups
- [ ] Enabled observability (Prometheus, Grafana)
- [ ] Configured rate limiting
- [ ] Enabled WAF (BunkerWeb)
- [ ] Set up mTLS (Istio)

---

## 📚 Additional Resources

- **Docker Compose Reference**: `make config` or `docker compose config`
- **Make Targets**: `make help`
- **Service Logs**: `make logs`
- **Health Checks**: `./scripts/health-check.sh --help`
- **Status Details**: `./scripts/service-status.sh --help`

---

## 🆘 Getting Help

```bash
# Show all available commands
make help

# Show run_all.sh options
./run_all.sh help

# Show health check options
./scripts/health-check.sh --help

# Show service status options
./scripts/service-status.sh --help
```

---

## 📞 Common Issues & Solutions

### Issue: Port already in use

```bash
# Find process using port
lsof -i :9000

# Kill process
kill -9 <PID>

# Or change port in .env
export PASSWORD_CHECKER_PORT=9001
```

### Issue: Out of disk space

```bash
# Clean Docker system
docker system prune -a --volumes

# Check space
docker system df
```

### Issue: Service not healthy

```bash
# Check service logs
docker compose logs <service>

# Restart service
docker compose restart <service>

# Rebuild service
docker compose up -d --build <service>
```

### Issue: Database connection failed

```bash
# Check PostgreSQL status
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# Check database logs
docker compose logs postgres
```

---

**Generated**: $(date)
**Version**: 1.0.0
