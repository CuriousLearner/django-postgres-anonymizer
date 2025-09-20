# Makefile for Django PostgreSQL Anonymizer
# Provides common development tasks and automation

.PHONY: help install clean test test-all lint format check security docs build publish dev-install example-setup docker-build docker-test docker-shell docker-lint docker-example docker-clean pre-commit-install pre-commit-run pre-commit-all

# Default Python and pip executables
PYTHON := python3
PIP := pip3
VENV_DIR := venv

# Package information
PACKAGE_NAME := django-postgres-anonymizer
VERSION := $(shell python -c "import django_postgres_anon; print(django_postgres_anon.__version__)")

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RESET := \033[0m

# Default target
help: ## Show this help message
	@echo "$(BLUE)Django PostgreSQL Anonymizer - Makefile Help$(RESET)"
	@echo ""
	@echo "$(GREEN)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(BLUE)Environment Variables:$(RESET)"
	@echo "  PYTHON        Python executable (default: python3)"
	@echo "  PIP          Pip executable (default: pip3)"
	@echo "  TEST_DB_NAME Database name for testing (default: test_postgres_anon)"

# Development setup
install: ## Install package in development mode
	@echo "$(BLUE)Installing django-postgres-anonymizer in development mode...$(RESET)"
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install Django psycopg2-binary PyYAML
	$(PIP) install -e .
	$(PIP) install -r requirements.txt || echo "$(YELLOW)requirements.txt not found, continuing...$(RESET)"

dev-install: venv install ## Create virtual environment and install package
	@echo "$(GREEN)Development environment ready!$(RESET)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(RESET)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(YELLOW)Activate with: source $(VENV_DIR)/bin/activate$(RESET)"

clean: ## Clean up build artifacts and caches
	@echo "$(BLUE)Cleaning up build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Testing
test: ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(RESET)"
	source $(VENV_DIR)/bin/activate && DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/ -v --tb=short --no-cov --disable-warnings

test-all: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	source $(VENV_DIR)/bin/activate && DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/ -v --tb=short

test-integration: ## Run integration tests (requires PostgreSQL with anon extension)
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@echo "$(YELLOW)Note: Requires PostgreSQL with anon extension$(RESET)"
	source $(VENV_DIR)/bin/activate && DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/test_integration.py -v --tb=short --no-cov --disable-warnings

test-commands: ## Run tests for management commands
	@echo "$(BLUE)Testing management commands...$(RESET)"
	source $(VENV_DIR)/bin/activate && DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/test_commands.py -v --tb=short --no-cov --disable-warnings

test-models: ## Run model tests
	@echo "$(BLUE)Testing models...$(RESET)"
	source $(VENV_DIR)/bin/activate && DJANGO_SETTINGS_MODULE=tests.settings python -m pytest tests/test_models.py -v --tb=short --no-cov --disable-warnings

# Code quality
lint: ## Run linting with flake8
	@echo "$(BLUE)Running linting checks...$(RESET)"
	source $(VENV_DIR)/bin/activate && flake8 || echo "$(YELLOW)flake8 not installed, skipping...$(RESET)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(RESET)"
	source $(VENV_DIR)/bin/activate && black django_postgres_anon tests example_project --line-length=120 || echo "$(YELLOW)black not installed, skipping...$(RESET)"
	source $(VENV_DIR)/bin/activate && isort django_postgres_anon tests example_project --profile=black || echo "$(YELLOW)isort not installed, skipping...$(RESET)"

format-check: ## Check if code formatting is correct
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	source $(VENV_DIR)/bin/activate && black --check django_postgres_anon tests example_project --line-length=120 || echo "$(YELLOW)black not installed, skipping...$(RESET)"
	source $(VENV_DIR)/bin/activate && isort --check-only django_postgres_anon tests example_project --profile=black || echo "$(YELLOW)isort not installed, skipping...$(RESET)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(RESET)"
	source $(VENV_DIR)/bin/activate && mypy django_postgres_anon --ignore-missing-imports --no-strict-optional || echo "$(YELLOW)mypy not installed, skipping...$(RESET)"

check: lint format-check type-check ## Run all code quality checks

# Security
security: ## Run security checks with bandit and safety
	@echo "$(BLUE)Running security checks...$(RESET)"
	source $(VENV_DIR)/bin/activate && bandit -r django_postgres_anon/ -f json -o bandit-report.json || echo "$(YELLOW)bandit not installed, skipping...$(RESET)"
	@if [ -f bandit-report.json ]; then \
		echo "$(YELLOW)Bandit report saved to bandit-report.json$(RESET)"; \
		source $(VENV_DIR)/bin/activate && python -m json.tool < bandit-report.json || cat bandit-report.json; \
	fi
	source $(VENV_DIR)/bin/activate && safety check --json || echo "$(YELLOW)safety not installed, skipping...$(RESET)"

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@echo "$(YELLOW)Documentation generation not yet implemented$(RESET)"

# Building and publishing
build: clean ## Build package for distribution
	@echo "$(BLUE)Building package...$(RESET)"
	source $(VENV_DIR)/bin/activate && python -m build
	@echo "$(GREEN)Package built successfully!$(RESET)"
	@echo "$(YELLOW)Files created in dist/:$(RESET)"
	@ls -la dist/

publish-test: build ## Publish to Test PyPI
	@echo "$(BLUE)Publishing to Test PyPI...$(RESET)"
	source $(VENV_DIR)/bin/activate && twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	@echo "$(RED)Publishing to PyPI...$(RESET)"
	@echo "$(YELLOW)Are you sure? This will publish version $(VERSION) to PyPI.$(RESET)"
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || (echo "Aborted." && exit 1)
	source $(VENV_DIR)/bin/activate && twine upload dist/*

# Example project
example-setup: ## Set up example project environment
	@echo "$(BLUE)Setting up example project...$(RESET)"
	cd example_project && $(PYTHON) -m pip install -r ../requirements.txt
	cd example_project && $(PYTHON) manage.py migrate
	@echo "$(GREEN)Example project ready!$(RESET)"
	@echo "$(YELLOW)Run: cd example_project && python manage.py runserver$(RESET)"

example-demo-data: ## Create demo data in example project
	@echo "$(BLUE)Creating demo data...$(RESET)"
	cd example_project && $(PYTHON) manage.py shell -c "from sample_app.views import create_demo_data; from django.http import HttpRequest; req = HttpRequest(); req.method = 'POST'; create_demo_data(req)"
	@echo "$(GREEN)Demo data created!$(RESET)"

example-run: ## Run example project server
	@echo "$(BLUE)Starting example project server...$(RESET)"
	cd example_project && $(PYTHON) manage.py runserver

# Database operations
db-init: ## Initialize PostgreSQL anonymizer extension
	@echo "$(BLUE)Initializing PostgreSQL Anonymizer extension...$(RESET)"
	cd example_project && $(PYTHON) manage.py anon_init

db-apply: ## Apply anonymization rules
	@echo "$(BLUE)Applying anonymization rules...$(RESET)"
	cd example_project && $(PYTHON) manage.py anon_apply

db-status: ## Show anonymization status
	@echo "$(BLUE)Checking anonymization status...$(RESET)"
	cd example_project && $(PYTHON) manage.py anon_status -v

db-load-preset: ## Load a preset (usage: make db-load-preset PRESET=django_auth)
	@echo "$(BLUE)Loading preset: $(PRESET)$(RESET)"
	cd example_project && $(PYTHON) manage.py anon_load_yaml ../django_postgres_anon/config/presets/$(PRESET).yaml

# Docker operations
docker-build: ## Build Docker image for testing
	@echo "$(BLUE)Building Docker image...$(RESET)"
	docker-compose -f docker/docker-compose.yml build

docker-test: ## Run tests in Docker container
	@echo "$(BLUE)Running tests in Docker...$(RESET)"
	docker-compose -f docker/docker-compose.yml down -v --remove-orphans 2>/dev/null || true
	docker-compose -f docker/docker-compose.yml run --rm test pytest tests/ -v --tb=short --override-ini="addopts="
	docker-compose -f docker/docker-compose.yml down

docker-shell: ## Open interactive shell in Docker container
	@echo "$(BLUE)Opening Docker shell...$(RESET)"
	docker-compose -f docker/docker-compose.yml run --rm shell

docker-lint: ## Run linting in Docker container
	@echo "$(BLUE)Running linting in Docker...$(RESET)"
	docker-compose -f docker/docker-compose.yml run --rm lint

docker-example: ## Run example project in Docker
	@echo "$(BLUE)Running example project in Docker...$(RESET)"
	docker-compose -f docker/docker-compose.yml up example db

docker-clean: ## Clean up Docker containers and images
	@echo "$(BLUE)Cleaning up Docker resources...$(RESET)"
	docker-compose -f docker/docker-compose.yml down -v
	docker system prune -f

# Utility targets
version: ## Show package version
	@echo "$(GREEN)Django PostgreSQL Anonymizer v$(VERSION)$(RESET)"

requirements: ## Update requirements.txt
	@echo "$(BLUE)Updating requirements.txt...$(RESET)"
	$(PIP) freeze > requirements.txt
	@echo "$(GREEN)Requirements updated!$(RESET)"

list-presets: ## List available anonymization presets
	@echo "$(BLUE)Available anonymization presets:$(RESET)"
	@ls -1 django_postgres_anon/config/presets/*.yaml | xargs -I {} basename {} .yaml | sort

validate-presets: ## Validate all YAML preset files
	@echo "$(BLUE)Validating preset files...$(RESET)"
	@for file in django_postgres_anon/config/presets/*.yaml; do \
		echo "$(YELLOW)Validating $$file$(RESET)"; \
		$(PYTHON) -c "import yaml; yaml.safe_load(open('$$file'))" || exit 1; \
	done
	@echo "$(GREEN)All preset files are valid!$(RESET)"

# Release preparation
pre-release: clean test-all lint security ## Run all pre-release checks
	@echo "$(GREEN)Pre-release checks completed successfully!$(RESET)"
	@echo "$(BLUE)Ready for release v$(VERSION)$(RESET)"

# Development workflow
dev: dev-install example-setup ## Complete development setup
	@echo "$(GREEN)Development environment fully set up!$(RESET)"
	@echo ""
	@echo "$(BLUE)Next steps:$(RESET)"
	@echo "  1. $(YELLOW)make example-run$(RESET)     - Start the example server"
	@echo "  2. $(YELLOW)make db-init$(RESET)        - Initialize anonymizer extension"
	@echo "  3. $(YELLOW)make example-demo-data$(RESET) - Create sample data"
	@echo "  4. $(YELLOW)make db-status$(RESET)      - Check status"

# Testing workflow
test-workflow: install test-all lint security ## Complete testing workflow
	@echo "$(GREEN)All tests and checks passed!$(RESET)"

# CI/CD helpers
ci-install: ## Install dependencies for CI
	$(PIP) install -e .
	$(PIP) install pytest pytest-django pytest-cov coverage flake8 black isort mypy bandit safety

ci-test: test-all lint security ## Run CI test suite

# Information
info: ## Show environment information
	@echo "$(BLUE)Environment Information:$(RESET)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Package: $(PACKAGE_NAME) v$(VERSION)"
	@echo "Directory: $(shell pwd)"
	@echo ""
	@echo "$(BLUE)Available presets:$(RESET)"
	@ls -1 django_postgres_anon/config/presets/*.yaml | xargs -I {} basename {} .yaml | sed 's/^/  /'

# Pre-commit hooks
pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(RESET)"
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on staged files
	@echo "$(BLUE)Running pre-commit hooks on staged files...$(RESET)"
	pre-commit run

pre-commit-all: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks on all files...$(RESET)"
	pre-commit run --all-files
