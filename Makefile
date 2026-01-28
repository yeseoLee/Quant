.PHONY: install install-dev format lint check test clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install all dependencies including dev"
	@echo "  make format       - Format code with ruff"
	@echo "  make lint         - Run linter"
	@echo "  make check        - Run format check and lint"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean cache files"

# Install dependencies
install:
	uv sync

install-dev:
	uv sync --all-extras

# Code formatting
format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

# Linting
lint:
	uv run ruff check src tests

# Check without fixing
check:
	uv run ruff format --check src tests
	uv run ruff check src tests

# Run tests
test:
	uv run pytest

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
