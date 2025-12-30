#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Vitruvian Platform - Enhanced Service Launcher
# Industry-standard service orchestration
# ============================================

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly MAKEFILE="$SCRIPT_DIR/Makefile"
readonly COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

# Banner
print_banner() {
    echo -e "${BOLD}"
    cat <<'BANNER_EOF'
                         |       :     . |
                        | '  :      '   |
                         |  .  |   '  |  |
   .--._ _...:.._ _.--. ,  ' |
  (  ,  `        `  ,  )   . |
   '-/              \-'  |   |
     |  o   /\   o  |       :|
     \     _\/_     / :  '   |
     /'._   ^^   _.;___      |
   /`    """""""`      `\=   |
 /`                     /=  .|
;             '--,-----'=    |
|                 `\  |    . |
\                   \___ :   |
/'.                     `\=  |
\_/`--......_            /=  |
            |`-.        /= : |
            | : `-.__ /` .   |
            |    .   ` |    '|
            |  .  : `   . |  |
BANNER_EOF
    echo -e "${RESET}"
    echo ""
    echo -e "${BOLD}           Cryptography Platform v1.0${RESET}"
}

# ============================================
# Logging Functions
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${RESET} $*"
}

log_success() {
    echo -e "${GREEN}[✓]${RESET} $*"
}

log_warning() {
    echo -e "${YELLOW}[!]${RESET} $*"
}

log_error() {
    echo -e "${RED}[✗]${RESET} $*"
}

log_header() {
    echo ""
    echo -e "${BOLD}$*${RESET}"
    echo "────────────────────────────────────────────────────"
}

# ============================================
# Prerequisites Check
# ============================================

check_prerequisites() {
    log_header "Checking Prerequisites"

    local missing=0

    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker installed: $(docker --version | head -n1)"
    else
        log_error "Docker is not installed"
        ((missing++))
    fi

    # Check Docker Compose
    if docker compose version >/dev/null 2>&1; then
        log_success "Docker Compose installed: $(docker compose version | head -n1)"
    elif docker-compose --version >/dev/null 2>&1; then
        log_success "Docker Compose installed: $(docker-compose --version | head -n1)"
    else
        log_error "Docker Compose is not installed"
        ((missing++))
    fi

    # Check Make
    if command -v make >/dev/null 2>&1; then
        log_success "Make installed: $(make --version | head -n1)"
    else
        log_warning "Make is not installed (optional but recommended)"
    fi

    # Check if files exist
    if [[ -f "$COMPOSE_FILE" ]]; then
        log_success "docker-compose.yml found"
    else
        log_error "docker-compose.yml not found"
        ((missing++))
    fi

    if [[ -f "$MAKEFILE" ]]; then
        log_success "Makefile found"
    else
        log_warning "Makefile not found"
    fi

    if [[ $missing -gt 0 ]]; then
        log_error "Missing $missing prerequisite(s)"
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# ============================================
# Environment Setup
# ============================================

setup_environment() {
    log_header "Setting Up Environment"

    local env_file=".env"

    if [[ ! -f "$env_file" ]]; then
        if [[ -f "${env_file}.example" ]]; then
            log_info "Creating .env from .env.example..."
            cp "${env_file}.example" "$env_file"
            log_warning "Please edit .env with your configuration before starting services"
        else
            log_warning "Creating minimal .env file..."
            cat > "$env_file" <<'ENV_EOF'
# Vitruvian Platform Environment Configuration
# Generated: $(date)

# Infrastructure
POSTGRES_USER=vitruvian
POSTGRES_PASSWORD=vitruvian_dev_password_CHANGE_ME
POSTGRES_DB=vitruvian

REDIS_PASSWORD=redis_dev_password_CHANGE_ME

# Application
JWT_SECRET=CHANGE_THIS_TO_RANDOM_64_CHAR_STRING_IN_PRODUCTION
ORCHESTRATOR_PORT=8200
REACT_PORT=5173

# Development
DEV_MODE=true
ENV_EOF
        fi
    fi

    log_success "Environment configured"
}

# ============================================
# Service Management Functions
# ============================================

start_all() {
    log_header "Starting All Services"

    # Start infrastructure first
    log_info "Starting infrastructure services (PostgreSQL, Redis)..."
    if command -v make >/dev/null 2>&1; then
        make start-dependencies
    else
        docker compose -f "$COMPOSE_FILE" up -d postgres redis
    fi

    # Wait for infrastructure
    log_info "Waiting for infrastructure to be ready..."
    sleep 5

    # Start all services
    log_info "Starting application services..."
    if command -v make >/dev/null 2>&1; then
        make start
    else
        docker compose -f "$COMPOSE_FILE" up -d
    fi

    log_success "All services started"

    # Run health checks
    log_info "Running health checks..."
    if [[ -f "./scripts/health-check.sh" ]]; then
        ./scripts/health-check.sh 60 2
    fi

    # Display service URLs
    print_service_urls
}

stop_all() {
    log_header "Stopping All Services"

    if command -v make >/dev/null 2>&1; then
        make stop
    else
        docker compose -f "$COMPOSE_FILE" stop
    fi

    log_success "All services stopped"
}

restart_all() {
    log_header "Restarting All Services"

    stop_all
    sleep 2
    start_all
}

build_all() {
    log_header "Building All Services"

    if command -v make >/dev/null 2>&1; then
        make build
    else
        docker compose -f "$COMPOSE_FILE" build
    fi

    log_success "All services built"
}

status_all() {
    if [[ -f "./scripts/service-status.sh" ]]; then
        ./scripts/service-status.sh summary
    else
        log_header "Service Status"
        docker compose -f "$COMPOSE_FILE" ps
    fi
}

logs_all() {
    local service="${2:-}"

    if [[ -n "$service" ]]; then
        if command -v make >/dev/null 2>&1; then
            make logs-agent SERVICE="$service"
        else
            docker compose -f "$COMPOSE_FILE" logs -f "$service"
        fi
    else
        if command -v make >/dev/null 2>&1; then
            make logs
        else
            docker compose -f "$COMPOSE_FILE" logs -f
        fi
    fi
}

clean_all() {
    log_header "Cleaning Up"

    read -p "Stop and remove all containers? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v make >/dev/null 2>&1; then
            make clean
        else
            docker compose -f "$COMPOSE_FILE" down -v
        fi
        log_success "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

# ============================================
# Quick Actions
# ============================================

quick_start_infrastructure() {
    log_info "Starting infrastructure only..."
    docker compose -f "$COMPOSE_FILE" up -d postgres redis
    log_success "Infrastructure started"
}

quick_start_agents() {
    log_info "Starting agent services..."
    docker compose -f "$COMPOSE_FILE" up -d \
        password-checker \
        theory-specialist \
        choice-maker \
        command-executor \
        prime-checker
    log_success "Agents started"
}

quick_restart_service() {
    local service="$1"

    if [[ -z "$service" ]]; then
        log_error "Usage: $0 restart <service-name>"
        exit 1
    fi

    log_info "Restarting $service..."
    docker compose -f "$COMPOSE_FILE" restart "$service"
    log_success "$service restarted"
}

# ============================================
# Utilities
# ============================================

print_service_urls() {
    log_header "Service URLs"

    local orchestrator_port="${ORCHESTRATOR_PORT:-8200}"
    local react_port="${REACT_PORT:-5173}"

    echo -e "${BOLD}Application Services:${RESET}"
    # echo -e "  • Backend API:         ${GREEN}http://localhost:8000${RESET}"  # TODO: Create backend
    echo -e "  • Orchestrator:        ${GREEN}http://localhost:${orchestrator_port}${RESET}"
    echo -e "  • React Frontend:      ${GREEN}http://localhost:${react_port}${RESET}"
    echo ""
    echo -e "${BOLD}Agent Services:${RESET}"
    echo -e "  • Password Checker:    ${GREEN}http://localhost:9000${RESET} /health"
    echo -e "  • Theory Specialist:   ${GREEN}http://localhost:8100${RESET} /health"
    echo -e "  • Choice Maker:        ${GREEN}http://localhost:8081${RESET} /health"
    echo -e "  • Command Executor:    ${GREEN}http://localhost:8085${RESET} /health"
    echo -e "  • Prime Checker:       ${GREEN}http://localhost:5000${RESET} /health"
    echo ""
    echo -e "${BOLD}Infrastructure:${RESET}"
    echo -e "  • PostgreSQL:          ${CYAN}localhost:5432${RESET}"
    echo -e "  • Redis:               ${CYAN}localhost:6379${RESET}"
    # echo ""
    # echo -e "${BOLD}Observability (if enabled):${RESET}"
    # echo -e "  • Prometheus:          ${GREEN}http://localhost:9090${RESET}"
    # echo -e "  • Grafana:             ${GREEN}http://localhost:3000${RESET} (admin/admin)"
}

print_help() {
    cat <<'HELP_EOF'
Usage: ./run_all.sh [COMMAND] [OPTIONS]

Commands:
  start           Start all services
  stop            Stop all services
  restart         Restart all services
  build           Build all service images
  status          Show service status
  logs [service]  View logs (all or specific service)
  clean           Stop and remove all containers
  health          Run health checks

Quick Actions:
  infra           Start only infrastructure (PostgreSQL, Redis)
  agents          Start only agent services
  restart <svc>   Restart specific service

Utilities:
  help            Show this help message
  urls            Print all service URLs

Examples:
  ./run_all.sh start              # Start all services
  ./run_all.sh logs orchestrator  # View orchestrator logs
  ./run_all.sh restart backend    # Restart backend service
  ./run_all.sh health             # Check all services

Recommended Workflow:
  1. ./run_all.sh build          # Build all images
  2. ./run_all.sh start          # Start services
  3. ./run_all.sh health         # Verify health
  4. ./run_all.sh status         # Check status
  5. ./run_all.sh stop           # Stop when done

Alternative: Use 'make' for more options
  make help                       # Show all make targets
HELP_EOF
}

# ============================================
# Main Script
# ============================================

main() {
    print_banner

    case "${1:-help}" in
        start)
            check_prerequisites
            setup_environment
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        build)
            check_prerequisites
            build_all
            ;;
        status)
            status_all
            ;;
        logs)
            logs_all "$@"
            ;;
        clean)
            clean_all
            ;;
        health)
            if [[ -f "./scripts/health-check.sh" ]]; then
                ./scripts/health-check.sh "${2:-120}" "${3:-2}"
            else
                log_error "health-check.sh not found"
                exit 1
            fi
            ;;
        infra|infrastructure)
            check_prerequisites
            setup_environment
            quick_start_infrastructure
            ;;
        agents)
            check_prerequisites
            quick_start_agents
            ;;
        urls)
            print_service_urls
            ;;
        help|--help|-h)
            print_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            print_help
            exit 1
            ;;
    esac
}

main "$@"
