#!/usr/bin/env bash
set -euo pipefail

# Root launcher for all services used by the project
# - Password Checker (agents/password_checker/docker-compose.yml)
# - Theory Specialist (agents/theory_specialist/docker-compose.yml)
# - Choice Maker (agents/choice_maker/docker-compose.yaml|yml)
# - Mock Interface (static HTML opened via file:// or your own static server)
# - React Frontend (interface/react_interface served via Nginx container)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$ROOT_DIR/agents"
INTERFACE_DIR="$ROOT_DIR/interface"
REACT_DIR="$INTERFACE_DIR/react_interface"

log() {
  echo "[run_all] $*"
}

start_password_checker() {
  local file="$AGENTS_DIR/password_checker/docker-compose.yml"
  if [ -f "$file" ]; then
    log "Starting password_checker (single consolidated container) via docker compose..."
    (cd "$AGENTS_DIR/password_checker" && docker compose up -d)
  else
    log "password_checker/docker-compose.yml not found, skipping password checker."
  fi
}

start_theory_specialist() {
  if [ -f "$AGENTS_DIR/theory_specialist/docker-compose.yml" ]; then
    log "Starting theory_specialist via docker-compose..."
    (cd "$AGENTS_DIR/theory_specialist" && docker compose up -d)
  else
    log "theory_specialist/docker-compose.yml not found, skipping theory specialist."
  fi
}

start_choice_maker() {
  local file_yml="$AGENTS_DIR/choice_maker/docker-compose.yml"
  local file_yaml="$AGENTS_DIR/choice_maker/docker-compose.yaml"
  if [ -f "$file_yml" ] || [ -f "$file_yaml" ]; then
    local compose_file="$file_yml"
    [ -f "$file_yaml" ] && compose_file="$file_yaml"
    log "Starting choice_maker via docker compose (file: ${compose_file##*/})..."
    (cd "$AGENTS_DIR/choice_maker" && docker compose -f "${compose_file##*/}" up -d)
  else
    log "choice_maker docker-compose file not found, skipping choice maker."
  fi
}

start_command_executor() {
  local file="$AGENTS_DIR/command_executor/docker-compose.yml"
  if [ -f "$file" ]; then
    log "Starting command_executor (OpenSSL Rust backend) via docker compose..."
    (cd "$AGENTS_DIR/command_executor" && docker compose up --build -d)
  else
    log "command_executor/docker-compose.yml not found, skipping command executor."
  fi
}

start_mock_interface() {
  local mock_path="$INTERFACE_DIR/mock/index.html"
  log "Mock Interface is static; open file://$mock_path in your browser."
}

start_react_frontend() {
  if [ ! -d "$REACT_DIR" ]; then
    log "react_interface directory not found, skipping React frontend."
    return
  fi

  local compose_file="$REACT_DIR/docker-compose.yml"
  if [ ! -f "$compose_file" ]; then
    log "react_interface/docker-compose.yml not found, skipping React frontend."
    return
  fi

  local existing_container=""
  existing_container="$(docker ps -q -f name=react_frontend 2>/dev/null || true)"
  if [ -n "$existing_container" ]; then
    log "React frontend container already running."
    return
  fi

  local port="${REACT_PORT:-${REACT_FRONTEND_PORT:-5173}}"
  log "Starting react_frontend via docker compose (host port $port -> container 80)..."
  (
    cd "$REACT_DIR"
    REACT_FRONTEND_PORT="$port" docker compose up --build -d
  )
}

log "Starting all components..."
start_password_checker
start_theory_specialist
start_choice_maker
start_command_executor
start_mock_interface
start_react_frontend

log "All start commands issued. Give containers a few seconds to become healthy."
log "Services:"
log " - Password Checker: http://localhost:9000"
log " - Theory Specialist: http://localhost:8100"
log " - Choice Maker: http://localhost:8081 (host) -> container 8080"
log " - Command Executor: http://localhost:8085"
log " - Mock Interface: open file://$INTERFACE_DIR/mock/index.html (or serve it statically)."
log " - React Frontend: http://localhost:${REACT_PORT:-${REACT_FRONTEND_PORT:-5173}} (Docker container)"
