#!/usr/bin/env bash
set -euo pipefail

# Vitruvian Platform - Health Check Script
# Validates all services are running and healthy

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

# Configuration
HEALTH_TIMEOUT="${1:-120}"  # Maximum time to wait for all services (seconds)
HEALTH_INTERVAL="${2:-2}"    # Check interval (seconds)

# Service definitions with health check endpoints
declare -A SERVICES=(
    ["PostgreSQL"]="postgres|5432|tcp"
    ["Redis"]="redis|6379|tcp"
    ["Password Checker"]="password-checker|9000|http|/health"
    ["Theory Specialist"]="theory-specialist|8100|http|/health"
    ["Choice Maker"]="choice-maker|8081|http|/health"
    ["Command Executor"]="command-executor|8085|http|/health"
    ["Prime Checker"]="prime-checker|5000|http|/health"
    ["Orchestrator"]="orchestrator|8200|http|/health"
    # ["Backend"]="backend|8000|http|/health"  # TODO: Create backend service
    ["React Frontend"]="react-frontend|5173|http|/health"
)

# ============================================
# Utility Functions
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
    echo "────────────────────────────────────────"
}

# ============================================
# Check Functions
# ============================================

check_tcp_port() {
    local host="$1"
    local port="$2"
    local timeout=3

    if command -v nc >/dev/null 2>&1; then
        nc -z -w "$timeout" "$host" "$port" 2>/dev/null
    elif command -v timeout >/dev/null 2>&1; then
        timeout "$timeout" bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null
    else
        # Fallback to /dev/tcp
        (echo >/dev/tcp/"$host"/"$port") 2>/dev/null
    fi
}

check_http_health() {
    local container="$1"
    local port="$2"
    local path="${3:-/health}"

    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 5 \
        "http://localhost:${port}${path}" 2>/dev/null || echo "000")

    [[ "$response" =~ ^[23] ]]
}

check_docker_container() {
    local container="$1"

    # Check if container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        return 1
    fi

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        return 1
    fi

    # Check container health status (if healthcheck defined)
    local health_status
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "")

    if [[ -n "$health_status" && "$health_status" != "healthy" ]]; then
        return 1
    fi

    return 0
}

wait_for_service() {
    local service_name="$1"
    local check_type="$2"

    local elapsed=0
    while [[ $elapsed -lt $HEALTH_TIMEOUT ]]; do
        case "$check_type" in
            tcp)
                if check_tcp_port "localhost" "$3"; then
                    return 0
                fi
                ;;
            http)
                if check_http_health "$service_name" "$3" "$4"; then
                    return 0
                fi
                ;;
        esac

        sleep "$HEALTH_INTERVAL"
        elapsed=$((elapsed + HEALTH_INTERVAL))

        # Show progress dots
        if [[ $((elapsed % 10)) -eq 0 ]]; then
            echo -n "."
        fi
    done

    return 1
}

# ============================================
# Main Health Check Logic
# ============================================

perform_health_checks() {
    local failed=0
    local passed=0
    local skipped=0

    log_header "Vitruvian Platform - Health Check"

    for service in "${!SERVICES[@]}"; do
        IFS='|' read -r container port type path <<< "${SERVICES[$service]}"

        echo -n "Checking $service... "

        # Check container
        if ! check_docker_container "$container"; then
            log_warning "$service container not running"
            ((skipped++))
            continue
        fi

        # Wait for service to be ready
        case "$type" in
            tcp)
                if wait_for_service "$service" "tcp" "$port"; then
                    log_success "$service (port $port)"
                    ((passed++))
                else
                    log_error "$service timeout"
                    ((failed++))
                fi
                ;;
            http)
                if wait_for_service "$service" "http" "$port" "$path"; then
                    log_success "$service (HTTP ${path:-/health})"
                    ((passed++))
                else
                    log_error "$service timeout"
                    ((failed++))
                fi
                ;;
        esac
    done

    # Summary
    echo ""
    log_header "Health Check Summary"

    if [[ $passed -gt 0 ]]; then
        log_success "Healthy: $passed"
    fi

    if [[ $failed -gt 0 ]]; then
        log_error "Unhealthy: $failed"
    fi

    if [[ $skipped -gt 0 ]]; then
        log_warning "Skipped: $skipped"
    fi

    # Return exit code
    if [[ $failed -eq 0 ]]; then
        echo ""
        log_success "All services are healthy!"
        return 0
    else
        echo ""
        log_error "Some services are unhealthy"
        return 1
    fi
}

# ============================================
# Quick Status (No Waiting)
# ============================================

quick_status() {
    log_header "Vitruvian Platform - Quick Status"

    for service in "${!SERVICES[@]}"; do
        IFS='|' read -r container port type path <<< "${SERVICES[$service]}"

        if check_docker_container "$container"; then
            echo -e "${GREEN}●${RESET} $service"
        else
            echo -e "${RED}○${RESET} $service (not running)"
        fi
    done

    echo ""
    echo "Run 'make health' to perform full health checks"
}

# ============================================
# Watch Mode (Continuous Monitoring)
# ============================================

watch_mode() {
    local interval="${1:-10}"

    log_header "Health Check Watch Mode (Ctrl+C to exit)"

    while true; do
        clear
        perform_health_checks
        echo ""
        log_info "Next check in ${interval}s... (Press Ctrl+C to exit)"
        sleep "$interval"
    done
}

# ============================================
# Main Script
# ============================================

main() {
    case "${1:-}" in
        --quick|-q)
            quick_status
            ;;
        --watch|-w)
            watch_mode "${2:-10}"
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick, -q      Show quick status without waiting"
            echo "  --watch, -w      Watch mode (continuous monitoring)"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Arguments:"
            echo "  TIMEOUT          Maximum wait time (default: 120s)"
            echo "  INTERVAL         Check interval (default: 2s)"
            echo ""
            echo "Examples:"
            echo "  $0                  # Full health check with wait"
            echo "  $0 60 1             # 60s timeout, 1s interval"
            echo "  $0 --quick          # Quick status only"
            echo "  $0 --watch 5        # Watch mode, 5s interval"
            ;;
        *)
            perform_health_checks
            ;;
    esac
}

main "$@"
