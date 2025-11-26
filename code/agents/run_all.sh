#!/usr/bin/env bash
set -euo pipefail

# Root launcher for all services used by the Mock Interface
# - Password Checker (password_checker/docker-compose.yml)
# - Theory Specialist (theory_specialist/docker-compose.yml)
# - Choice Maker (choice_maker/docker-compose.yaml)
# - Mock Interface (static HTML opened via file:// or your own static server)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
  echo "[run_all] $*"
}

start_password_checker() {
  local file="$ROOT_DIR/password_checker/docker-compose.yml"
  if [ -f "$file" ]; then
    log "Starting password_checker (single consolidated container) via docker compose..."
    (cd "$ROOT_DIR/password_checker" && docker compose up -d)
  else
    log "password_checker/docker-compose.yml not found, skipping password checker."
  fi
}

start_theory_specialist() {
  if [ -f "$ROOT_DIR/theory_specialist/docker-compose.yml" ]; then
    log "Starting theory_specialist via docker-compose..."
    (cd "$ROOT_DIR/theory_specialist" && docker compose up -d)
  else
    log "theory_specialist/docker-compose.yml not found, skipping theory specialist."
  fi
}

start_choice_maker() {
  local file_yml="$ROOT_DIR/choice_maker/docker-compose.yml"
  local file_yaml="$ROOT_DIR/choice_maker/docker-compose.yaml"
  if [ -f "$file_yml" ] || [ -f "$file_yaml" ]; then
    local compose_file="$file_yml"
    [ -f "$file_yaml" ] && compose_file="$file_yaml"
    log "Starting choice_maker via docker compose (file: ${compose_file##*/})..."
    (cd "$ROOT_DIR/choice_maker" && docker compose -f "${compose_file##*/}" up -d)
  else
    log "choice_maker docker-compose file not found, skipping choice maker."
  fi
}

start_mock_interface() {
  log "Mock Interface is static; open file://$ROOT_DIR/mock_interface/index.html in your browser."
}

log "Starting all components..."
start_password_checker
start_theory_specialist
start_choice_maker
start_mock_interface

log "All start commands issued. Give containers a few seconds to become healthy."
log "Services:"
log " - Password Checker: http://localhost:9000"
log " - Theory Specialist: http://localhost:8100"
log " - Choice Maker: http://localhost:8081 (host) -> container 8080"
log "Open the Mock Interface via file://$ROOT_DIR/mock_interface/index.html (or serve it statically on a different port)."
