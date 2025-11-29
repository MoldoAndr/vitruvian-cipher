.PHONY: install run dev clean build docker-build docker-run help

# Default target
help:
	@echo "Agent CLI - Available Commands"
	@echo "==============================="
	@echo ""
	@echo "  make install      Install the CLI package"
	@echo "  make run          Run the CLI"
	@echo "  make dev          Run in development mode"
	@echo "  make clean        Clean build artifacts"
	@echo "  make build        Build the package"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run in Docker"
	@echo ""

# Install the package
install:
	pip install -e .

# Run the CLI
run:
	python -m agent_cli.main

# Run in development mode (with auto-reload would need watchdog)
dev:
	python run.py

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Build the package
build: clean
	pip install build
	python -m build

# Build Docker image
docker-build:
	docker build -t agent-cli .

# Run in Docker
docker-run:
	docker run -it --rm agent-cli

# Run with environment variables
run-with-env:
	PASSWORD_CHECKER_URL=http://localhost:9000 \
	THEORY_SPECIALIST_URL=http://localhost:8100 \
	CHOICE_MAKER_URL=http://localhost:8081 \
	python -m agent_cli.main

# Install development dependencies
dev-install:
	pip install -e ".[dev]"

# Format code
format:
	black src/
	isort src/

# Type check
typecheck:
	mypy src/

# Test
test:
	pytest tests/ -v
