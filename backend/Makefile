# Makefile for StudyMate Backend Dependency Management

.PHONY: help install install-dev install-prod update-deps test clean

# Default target
help:
	@echo "StudyMate Backend Dependency Management"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  install-prod - Install production dependencies (alias for install)"
	@echo "  update-deps  - Update dependency versions (requires pip-tools)"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean virtual environment"
	@echo ""
	@echo "Usage examples:"
	@echo "  make install"
	@echo "  make install-dev"
	@echo "  make test"

# Install production dependencies
install:
	pip install --no-deps -r requirements.txt

# Install development dependencies
install-dev:
	pip install --no-deps -r requirements.txt
	pip install --no-deps -r requirements-dev.txt

# Install production dependencies (alias)
install-prod: install

# Update dependencies using pip-tools
update-deps:
	@echo "Updating dependencies..."
	@echo "Installing pip-tools if not available..."
	pip install pip-tools
	@echo "Compiling requirements..."
	pip-compile requirements.in
	pip-compile requirements-dev.in
	pip-compile requirements-prod.in
	@echo "Dependencies updated. Review changes and commit."

# Run tests
test:
	python -m pytest tests/ -v

# Run configuration tests
test-config:
	python test_config.py

# Clean virtual environment
clean:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y
	@echo "Virtual environment cleaned"

# Install and setup development environment
setup-dev: install-dev
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Development environment ready!"

# Check for security vulnerabilities
security-check:
	pip install safety
	safety check

# Format code
format:
	black .
	@echo "Code formatted with black"

# Lint code
lint:
	flake8 .
	mypy .
	@echo "Code linting completed"
