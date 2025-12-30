# Vitruvian Platform - Service Management Makefile
# Industry-standard Docker Compose orchestration

.PHONY: help build start stop restart status logs clean health test install uninstall
.DEFAULT_GOAL := help

# ============================================
# Configuration
# ============================================

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_RED := \033[31m
COLOR_BLUE := \033[34m

# Project paths
ROOT_DIR := $(shell pwd)
AGENTS_DIR := $(ROOT_DIR)/agents
INTERFACE_DIR := $(ROOT_DIR)/interface
COMPOSE_FILE := $(ROOT_DIR)/docker-compose.yml

# Docker Compose configuration
COMPOSE := docker compose
ifeq ($(shell docker compose version 2>/dev/null),)
	COMPOSE := docker-compose
endif

# Service ports
ORCHESTRATOR_PORT ?= 8200
REACT_PORT ?= 5173
POSTGRES_PORT ?= 5432
REDIS_PORT ?= 6379

# Health check configuration
HEALTH_TIMEOUT := 120
HEALTH_INTERVAL := 2

# ============================================
# Help Target
# ============================================

help: ## Show this help message
	@echo '$(COLOR_BOLD)Vitruvian Platform - Service Management$(COLOR_RESET)'
	@echo ''
	@echo '$(COLOR_BOLD)Usage:$(COLOR_RESET)'
	@echo '  make [target]'
	@echo ''
	@echo '$(COLOR_BOLD)Targets:$(COLOR_RESET)'
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(COLOR_BLUE)%-20s$(COLOR_RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ''
	@echo '$(COLOR_BOLD)Examples:$(COLOR_RESET)'
	@echo '  make build              # Build all services'
	@echo '  make start              # Start all services'
	@echo '  make stop               # Stop all services'
	@echo '  make logs               # View all logs'
	@echo '  make status             # Check service status'
	@echo '  make health             # Run health checks'

# ============================================
# Installation
# ============================================

install: ## Install dependencies and setup environment
	@echo '$(COLOR_GREEN)Installing dependencies...$(COLOR_RESET)'
	@command -v docker >/dev/null 2>&1 || { echo '$(COLOR_RED)Error: Docker is not installed$(COLOR_RESET)'; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo '$(COLOR_YELLOW)Warning: Git is not installed$(COLOR_RESET)'; }
	@$(COMPOSE) version >/dev/null 2>&1 || { echo '$(COLOR_RED)Error: Docker Compose is not installed$(COLOR_RESET)'; exit 1; }
	@echo '$(COLOR_GREEN)✓ All dependencies installed$(COLOR_RESET)'
	@echo ''
	@echo '$(COLOR_YELLOW)Creating .env file if not exists...$(COLOR_RESET)'
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || echo '# Environment variables' > .env; \
		echo '$(COLOR_GREEN)✓ Created .env file$(COLOR_RESET)'; \
	fi
	@echo '$(COLOR_GREEN)✓ Installation complete$(COLOR_RESET)'

# ============================================
# Build Targets
# ============================================

build: ## Build all service images
	@echo '$(COLOR_BLUE)Building all services...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) build
	@echo '$(COLOR_GREEN)✓ Build complete$(COLOR_RESET)'

build-agent: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
build-agent: ## Build specific agent (usage: make build-agent SERVICE=password_checker)
	@echo '$(COLOR_BLUE)Building $(SERVICE)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) build $(SERVICE)
	@echo '$(COLOR_GREEN)✓ $(SERVICE) built$(COLOR_RESET)'

build-no-cache: ## Build all services without cache
	@echo '$(COLOR_BLUE)Building all services (no cache)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) build --no-cache
	@echo '$(COLOR_GREEN)✓ Build complete$(COLOR_RESET)'

# ============================================
# Start Targets
# ============================================

start: ## Start all services in detached mode
	@echo '$(COLOR_BLUE)Starting Vitruvian Platform...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo '$(COLOR_GREEN)✓ Services started$(COLOR_RESET)'
	@$(MAKE) --silent health

start-dev: ## Start all services in development mode (foreground)
	@echo '$(COLOR_BLUE)Starting Vitruvian Platform (foreground mode)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up

start-agent: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
start-agent: ## Start specific agent (usage: make start-agent SERVICE=password_checker)
	@echo '$(COLOR_BLUE)Starting $(SERVICE)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d $(SERVICE)
	@echo '$(COLOR_GREEN)✓ $(SERVICE) started$(COLOR_RESET)'

start-dependencies: ## Start only infrastructure services (postgres, redis, etc.)
	@echo '$(COLOR_BLUE)Starting infrastructure services...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d postgres redis
	@echo '$(COLOR_GREEN)✓ Infrastructure services started$(COLOR_RESET)'

start-agents: ## Start only agent services (no infrastructure)
	@echo '$(COLOR_BLUE)Starting agent services...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d \
		password-checker \
		theory-specialist \
		choice-maker \
		command-executor \
		prime-checker \
		orchestrator
	@echo '$(COLOR_GREEN)✓ Agent services started$(COLOR_RESET)'

# ============================================
# Stop Targets
# ============================================

stop: ## Stop all services gracefully
	@echo '$(COLOR_BLUE)Stopping Vitruvian Platform...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) stop
	@echo '$(COLOR_GREEN)✓ Services stopped$(COLOR_RESET)'

stop-agent: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
stop-agent: ## Stop specific agent (usage: make stop-agent SERVICE=password_checker)
	@echo '$(COLOR_BLUE)Stopping $(SERVICE)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) stop $(SERVICE)
	@echo '$(COLOR_GREEN)✓ $(SERVICE) stopped$(COLOR_RESET)'

# ============================================
# Restart Targets
# ============================================

restart: ## Restart all services
	@echo '$(COLOR_BLUE)Restarting Vitruvian Platform...$(COLOR_RESET)'
	@$(MAKE) --silent stop
	@sleep 2
	@$(MAKE) --silent start

restart-agent: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
restart-agent: ## Restart specific agent (usage: make restart-agent SERVICE=password_checker)
	@echo '$(COLOR_BLUE)Restarting $(SERVICE)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) restart $(SERVICE)
	@echo '$(COLOR_GREEN)✓ $(SERVICE) restarted$(COLOR_RESET)'

# ============================================
# Status & Health Targets
# ============================================

status: ## Show status of all services
	@echo '$(COLOR_BOLD)Vitruvian Platform - Service Status$(COLOR_RESET)'
	@echo ''
	@$(COMPOSE) -f $(COMPOSE_FILE) ps

health: ## Check health of all services
	@echo '$(COLOR_BLUE)Running health checks...$(COLOR_RESET)'
	@echo ''
	@./scripts/health-check.sh $(HEALTH_TIMEOUT) $(HEALTH_INTERVAL)
	@echo ''

ps: ## Show running processes (alias for status)
	@$(MAKE) --silent status

top: ## Show resource usage
	@$(COMPOSE) -f $(COMPOSE_FILE) top

# ============================================
# Logging Targets
# ============================================

logs: ## Show logs from all services (follow mode)
	@$(COMPOSE) -f $(COMPOSE_FILE) logs -f

logs-agent: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
logs-agent: ## Show logs from specific agent (usage: make logs-agent SERVICE=password_checker)
	@$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(SERVICE)

logs-tail: ## Show last 100 lines of logs from all services
	@$(COMPOSE) -f $(COMPOSE_FILE) logs --tail=100

logs-json: ## Export logs as JSON
	@$(COMPOSE) -f $(COMPOSE_FILE) logs --no-log-prefix -t > logs/export_$(shell date +%Y%m%d_%H%M%S).json
	@echo '$(COLOR_GREEN)Logs exported to logs/$(COLOR_RESET)'

# ============================================
# Clean Targets
# ============================================

clean: ## Stop and remove all containers, networks, and volumes
	@echo '$(COLOR_YELLOW)Cleaning up all resources...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans
	@echo '$(COLOR_GREEN)✓ Cleanup complete$(COLOR_RESET)'

clean-containers: ## Remove all stopped containers
	@echo '$(COLOR_BLUE)Removing stopped containers...$(COLOR_RESET)'
	@docker container prune -f
	@echo '$(COLOR_GREEN)✓ Stopped containers removed$(COLOR_RESET)'

clean-images: ## Remove dangling images
	@echo '$(COLOR_BLUE)Removing dangling images...$(COLOR_RESET)'
	@docker image prune -f
	@echo '$(COLOR_GREEN)✓ Dangling images removed$(COLOR_RESET)'

clean-volumes: ## Remove all unused volumes
	@echo '$(COLOR_YELLOW)WARNING: This will delete all data!$(COLOR_RESET)'
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker volume prune -f; \
		echo '$(COLOR_GREEN)✓ Unused volumes removed$(COLOR_RESET)'; \
	fi

clean-all: ## Clean everything (containers, images, volumes)
	@echo '$(COLOR_YELLOW)WARNING: This will delete everything!$(COLOR_RESET)'
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) --silent clean; \
		docker system prune -a -f --volumes; \
		echo '$(COLOR_GREEN)✓ Everything cleaned$(COLOR_RESET)'; \
	fi

# ============================================
# Test Targets
# ============================================

test: ## Run all tests
	@echo '$(COLOR_BLUE)Running tests...$(COLOR_RESET)'
	@./scripts/test-all.sh
	@echo '$(COLOR_GREEN)✓ Tests complete$(COLOR_RESET)'

test-integration: ## Run integration tests
	@echo '$(COLOR_BLUE)Running integration tests...$(COLOR_RESET)'
	@./scripts/test-integration.sh

test-unit: ## Run unit tests
	@echo '$(COLOR_BLUE)Running unit tests...$(COLOR_RESET)'
	@./scripts/test-unit.sh

# ============================================
# Utility Targets
# ============================================

shell: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
shell: ## Open shell in service container (usage: make shell SERVICE=backend)
	@$(COMPOSE) -f $(COMPOSE_FILE) exec $(SERVICE) /bin/bash

exec: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
exec: CMD ?= /bin/bash
exec: ## Execute command in service (usage: make exec SERVICE=backend CMD="ls -la")
	@$(COMPOSE) -f $(COMPOSE_FILE) exec $(SERVICE) $(CMD)

rebuild: SERVICE = $(filter-out $@,$(MAKECMDGOALS))
rebuild: ## Rebuild and restart service (usage: make rebuild SERVICE=backend)
	@echo '$(COLOR_BLUE)Rebuilding $(SERVICE)...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d --build $(SERVICE)
	@echo '$(COLOR_GREEN)✓ $(SERVICE) rebuilt$(COLOR_RESET)'

pull: ## Pull latest images for all services
	@echo '$(COLOR_BLUE)Pulling latest images...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) pull
	@echo '$(COLOR_GREEN)✓ Images pulled$(COLOR_RESET)'

config: ## Validate and view the composed configuration
	@$(COMPOSE) -f $(COMPOSE_FILE) config

# ============================================
# CI/CD Targets
# ============================================

ci-build: ## CI: Build all services
	@echo '$(COLOR_BLUE)[CI] Building all services...$(COLOR_RESET)'
	@$(COMPOSE) -f $(COMPOSE_FILE) build --parallel
	@$(MAKE) --silent config

ci-test: ## CI: Run tests
	@echo '$(COLOR_BLUE)[CI] Running tests...$(COLOR_RESET)'
	@$(MAKE) --silent test

ci-deploy: ## CI: Deploy services
	@echo '$(COLOR_BLUE)[CI] Deploying services...$(COLOR_RESET)'
	@$(MAKE) --silent stop
	@$(MAKE) --silent start
	@$(MAKE) --silent health

# ============================================
# Migration Targets (TODO: Uncomment when backend service exists)
# ============================================

# migrate-create: NAME = $(filter-out $@,$(MAKECMDGOALS))
# migrate-create: ## Create new database migration (usage: make migrate-create NAME=add_users_table)
# 	@echo '$(COLOR_BLUE)Creating migration: $(NAME)$(COLOR_RESET)'
# 	@docker exec -it backend migrate create $(NAME)
# 	@echo '$(COLOR_GREEN)✓ Migration created$(COLOR_RESET)'
#
# migrate-up: ## Run pending database migrations
# 	@echo '$(COLOR_BLUE)Running migrations...$(COLOR_RESET)'
# 	@docker exec -it backend migrate up
# 	@echo '$(COLOR_GREEN)✓ Migrations complete$(COLOR_RESET)'
#
# migrate-down: ## Rollback last migration
# 	@echo '$(COLOR_BLUE)Rolling back migration...$(COLOR_RESET)'
# 	@docker exec -it backend migrate down
# 	@echo '$(COLOR_GREEN)✓ Migration rolled back$(COLOR_RESET)'
#
# migrate-status: ## Show migration status
# 	@echo '$(COLOR_BLUE)Migration status:$(COLOR_RESET)'
# 	@docker exec -it backend migrate status

# ============================================
# Backup Targets (TODO: Uncomment when backend service exists)
# ============================================

# backup: ## Backup all data
# 	@echo '$(COLOR_BLUE)Creating backup...$(COLOR_RESET)'
# 	@mkdir -p backups
# 	@docker exec postgres pg_dump -U vitruvian vitruvian > backups/db_$(shell date +%Y%m%d_%H%M%S).sql
# 	@echo '$(COLOR_GREEN)✓ Backup created: backups/db_$(shell date +%Y%m%d_%H%M%S).sql$(COLOR_RESET)'
#
# restore: FILE = $(filter-out $@,$(MAKECMDGOALS))
# restore: ## Restore database from backup (usage: make restore FILE=backups/db_20240101_120000.sql)
# 	@echo '$(COLOR_BLUE)Restoring from $(FILE)...$(COLOR_RESET)'
# 	@docker exec -i postgres psql -U vitruvian vitruvian < $(FILE)
# 	@echo '$(COLOR_GREEN)✓ Database restored$(COLOR_RESET)'

# ============================================
# Info Targets
# ============================================

info: ## Show system information
	@echo '$(COLOR_BOLD)Vitruvian Platform Information$(COLOR_RESET)'
	@echo ''
	@echo '$(COLOR_BOLD)Docker:$(COLOR_RESET)'
	@docker --version
	@echo ''
	@echo '$(COLOR_BOLD)Docker Compose:$(COLOR_RESET)'
	@$(COMPOSE) version
	@echo ''
	@echo '$(COLOR_BOLD)Environment:$(COLOR_RESET)'
	@echo '  ROOT_DIR: $(ROOT_DIR)'
	@echo '  COMPOSE_FILE: $(COMPOSE_FILE)'
	@echo '  ORCHESTRATOR_PORT: $(ORCHESTRATOR_PORT)'
	@echo '  REACT_PORT: $(REACT_PORT)'
	@echo ''
	@echo '$(COLOR_BOLD)Services:$(COLOR_RESET)'
	@$(MAKE) --silent status

# ============================================
# Development Targets
# ============================================

dev-setup: ## Setup development environment
	@echo '$(COLOR_BLUE)Setting up development environment...$(COLOR_RESET)'
	@$(MAKE) --silent install
	@$(MAKE) --silent build
	@$(MAKE) --silent start-dependencies
	@echo '$(COLOR_GREEN)✓ Dev environment ready$(COLOR_RESET)'
	@echo '$(COLOR_YELLOW)Run "make start" to start all services$(COLOR_RESET)'

dev-hot-reload: ## Enable hot reload for development
	@echo '$(COLOR_BLUE)Enabling hot reload...$(COLOR_RESET)'
	@$(COMPOSE) -f docker-compose.dev.yml up -d

dev-logs: ## Show development logs with filtering
	@$(COMPOSE) -f $(COMPOSE_FILE) logs -f | grep -v --line-buffered 'health\|ping\|heartbeat'

# ============================================
# Production Targets
# ============================================

prod-build: ## Build production images
	@echo '$(COLOR_BLUE)Building production images...$(COLOR_RESET)'
	@$(COMPOSE) -f docker-compose.prod.yml build
	@echo '$(COLOR_GREEN)✓ Production images built$(COLOR_RESET)'

prod-deploy: ## Deploy to production
	@echo '$(COLOR_YELLOW)WARNING: Deploying to production$(COLOR_RESET)'
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) --silent prod-build; \
		$(COMPOSE) -f docker-compose.prod.yml up -d; \
		$(MAKE) --silent health; \
	fi

prod-rollback: ## Rollback to previous version
	@echo '$(COLOR_BLUE)Rolling back...$(COLOR_RESET)'
	@$(COMPOSE) -f docker-compose.prod.yml down
	@git checkout HEAD~1 docker-compose.prod.yml
	@$(COMPOSE) -f docker-compose.prod.yml up -d

# ============================================
# Uninstall
# ============================================

uninstall: ## Remove all containers, images, volumes, and configuration
	@echo '$(COLOR_YELLOW)WARNING: This will completely uninstall Vitruvian Platform$(COLOR_RESET)'
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MAKE) --silent clean-all; \
		rm -rf .env logs backups; \
		echo '$(COLOR_GREEN)✓ Uninstall complete$(COLOR_RESET)'; \
	fi

# ============================================
# Phony cleanup
# ============================================

# Allow passing service name as argument (e.g., make logs-agent SERVICE=backend)
%:
	@:
