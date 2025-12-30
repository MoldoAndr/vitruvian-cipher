#!/usr/bin/env bash
set -euo pipefail

# Vitruvian Platform - Service Status Script
# Shows detailed status of all services

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

# Service definitions
declare -A SERVICES=(
    ["vitruvian-postgres"]="PostgreSQL|5432|Database"
    ["vitruvian-redis"]="Redis|6379|Cache"
    ["vitruvian-password-checker"]="Password Checker|9000|Agent"
    ["vitruvian-theory-specialist"]="Theory Specialist|8100|Agent"
    ["vitruvian-choice-maker"]="Choice Maker|8081|ML"
    ["vitruvian-command-executor"]="Command Executor|8085|Crypto"
    ["vitruvian-prime-checker"]="Prime Checker|5000|Algorithm"
    ["vitruvian-orchestrator"]="Orchestrator|8200|Router"
    # ["vitruvian-backend"]="Backend|8000|API"  # TODO: Create backend service
    ["vitruvian-frontend"]="Frontend|5173|UI"
)

# ============================================
# Utility Functions
# ============================================

container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${1}$"
}

container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${1}$"
}

get_container_status() {
    docker inspect --format='{{.State.Status}}' "$1" 2>/dev/null || echo "unknown"
}

get_container_health() {
    docker inspect --format='{{.State.Health.Status}}' "$1" 2>/dev/null || echo "no healthcheck"
}

get_container_uptime() {
    local started
    started=$(docker inspect --format='{{.State.StartedAt}}' "$1" 2>/dev/null || echo "")
    if [[ -n "$started" ]]; then
        local start_ts
        start_ts=$(date -d "$started" +%s 2>/dev/null || echo "0")
        local now_ts
        now_ts=$(date +%s)
        local uptime=$((now_ts - start_ts))

        # Format uptime
        local days=$((uptime / 86400))
        local hours=$(((uptime % 86400) / 3600))
        local minutes=$(((uptime % 3600) / 60))

        if [[ $days -gt 0 ]]; then
            echo "${days}d ${hours}h"
        elif [[ $hours -gt 0 ]]; then
            echo "${hours}h ${minutes}m"
        else
            echo "${minutes}m"
        fi
    else
        echo "N/A"
    fi
}

get_container_resources() {
    local stats
    stats=$(docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" "$1" 2>/dev/null || echo "")
    if [[ -n "$stats" ]]; then
        local cpu mem
        IFS=',' read -r cpu mem <<< "$stats"
        echo "${CPU}${CPU} | ${MEM}${mem}"
    else
        echo "N/A"
    fi
}

get_service_logs() {
    local container="$1"
    local lines="${2:-5}"

    docker logs --tail "$lines" "$container" 2>&1 | sed 's/^/  /'
}

check_port() {
    local port="$1"
    if command -v nc >/dev/null 2>&1; then
        nc -z -w 1 "localhost" "$port" 2>/dev/null && echo "open" || echo "closed"
    elif command -v timeout >/dev/null 2>&1; then
        timeout 1 bash -c "echo >/dev/tcp/$port/$port" 2>/dev/null && echo "open" || echo "closed"
    else
        echo "unknown"
    fi
}

# ============================================
# Display Functions
# ============================================

print_header() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}$1${RESET}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
}

print_service_row() {
    local container="$1"
    local name="$2"
    local port="$3"
    local type="$4"

    local status symbol color uptime resources health port_status

    # Get container status
    if ! container_exists "$container"; then
        symbol="○"
        color="${RED}"
        status="Not created"
        uptime="N/A"
        resources="N/A"
        health="N/A"
        port_status="N/A"
    elif ! container_running "$container"; then
        symbol="○"
        color="${YELLOW}"
        status="Stopped"
        uptime="N/A"
        resources="N/A"
        health=$(get_container_health "$container")
        port_status="closed"
    else
        symbol="●"
        color="${GREEN}"
        status="Running"
        uptime=$(get_container_uptime "$container")
        resources=$(get_container_resources "$container")
        health=$(get_container_health "$container")
        port_status=$(check_port "$port")
    fi

    # Print formatted row
    printf "${color}%s${RESET} %-25s ${BOLD}%-20s${RESET} %-10s %-8s %-12s %-10s %-10s %-12s\n" \
        "$symbol" "$name" "($container)" "$type" "$status" "$uptime" "$health" "$port_status" "$resources"
}

# ============================================
# Summary View
# ============================================

print_summary() {
    local total=0
    local running=0
    local stopped=0
    local missing=0

    for container in "${!SERVICES[@]}"; do
        ((total++))
        if container_exists "$container"; then
            if container_running "$container"; then
                ((running++))
            else
                ((stopped++))
            fi
        else
            ((missing++))
        fi
    done

    echo ""
    echo -e "${BOLD}Summary:${RESET}"
    echo "  Total Services: $total"
    echo -e "  ${GREEN}Running:${RESET} $running"
    echo -e "  ${YELLOW}Stopped:${RESET} $stopped"
    echo -e "  ${RED}Missing:${RESET} $missing"
}

# ============================================
# Detailed Service View
# ============================================

print_detailed_service() {
    local container="$1"
    local name="$2"
    local port="$3"

    print_header "$name Details"

    echo -e "${BOLD}Container:${RESET} $container"
    echo -e "${BOLD}Port:${RESET} $port"
    echo ""

    if ! container_exists "$container"; then
        echo -e "${RED}Container does not exist${RESET}"
        return
    fi

    echo -e "${BOLD}Status:${RESET} $(get_container_status "$container")"
    echo -e "${BOLD}Health:${RESET} $(get_container_health "$container")"
    echo -e "${BOLD}Uptime:${RESET} $(get_container_uptime "$container")"
    echo ""

    echo -e "${BOLD}Resource Usage:${RESET}"
    docker stats --no-stream "$container" --format "  CPU: {{.CPUPerc}}\n  Memory: {{.MemUsage}}\n  Net I/O: {{.NetIO}}\n  Block I/O: {{.BlockIO}}" 2>/dev/null || echo "  N/A"
    echo ""

    echo -e "${BOLD}Recent Logs (last 10 lines):${RESET}"
    get_service_logs "$container" 10
}

# ============================================
# Main Script
# ============================================

main() {
    case "${1:-summary}" in
        summary|""|"")
            print_header "Vitruvian Platform - Service Status"
            echo ""
            printf "${BOLD}%-1s %-25s %-20s %-10s %-8s %-12s %-10s %-10s %-12s${RESET}\n" \
                "" "Service" "Container" "Type" "Status" "Uptime" "Health" "Port" "Resources"
            printf "%s\n" "────────────────────────────────────────────────────────────────────────────────────────────────────"

            for container in "${!SERVICES[@]}"; do
                IFS='|' read -r name port type <<< "${SERVICES[$container]}"
                print_service_row "$container" "$name" "$port" "$type"
            done

            print_summary
            ;;

        detailed)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 detailed <container-name>"
                echo ""
                echo "Available containers:"
                for c in "${!SERVICES[@]}"; do
                    echo "  - $c"
                done
                exit 1
            fi

            local container="$2"
            if [[ -z "${SERVICES[$container]:-}" ]]; then
                echo "Unknown container: $container"
                exit 1
            fi

            IFS='|' read -r name port type <<< "${SERVICES[$container]}"
            print_detailed_service "$container" "$name" "$port"
            ;;

        logs)
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 logs <container-name> [lines]"
                exit 1
            fi

            local lines="${3:-50}"
            print_header "Logs: $2"
            get_service_logs "$2" "$lines"
            ;;

        watch)
            local interval="${2:-5}"
            while true; do
                clear
                main summary
                echo ""
                echo -e "${CYAN}Refreshing every ${interval}s... (Press Ctrl+C to exit)${RESET}"
                sleep "$interval"
            done
            ;;

        *)
            echo "Usage: $0 [command] [args]"
            echo ""
            echo "Commands:"
            echo "  summary [default]    Show summary of all services"
            echo "  detailed <name>      Show detailed information for a service"
            echo "  logs <name> [lines]  Show recent logs for a service"
            echo "  watch [interval]     Watch mode (auto-refresh)"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 summary"
            echo "  $0 detailed vitruvian-orchestrator"
            echo "  $0 logs vitruvian-backend 100"
            echo "  $0 watch 3"
            exit 1
            ;;
    esac
}

main "$@"
