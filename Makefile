# Quote Master Pro - Development Makefile
.PHONY: help install dev test lint typecheck fmt clean build up down logs migrate alembic-auto seed cov test-unit test-int test-e2e

# Default target
help: ## Show this help message
	@echo "Quote Master Pro - Development Commands"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment setup
install: ## Install all dependencies
	pip install -r requirements.txt
	pip install -r requirements/dev.txt
	pre-commit install

dev: ## Setup development environment
	python -m venv .venv
	.venv/Scripts/activate && pip install --upgrade pip
	.venv/Scripts/activate && pip install -r requirements.txt
	.venv/Scripts/activate && pip install -r requirements/dev.txt
	.venv/Scripts/activate && pre-commit install
	@echo "Development environment ready! Activate with: .venv/Scripts/activate"

# Code quality
lint: ## Run linting (flake8, black check, isort check)
	@echo "Running flake8..."
	flake8 src tests --max-line-length=88 --extend-ignore=E203,W503
	@echo "Checking black formatting..."
	black --check --diff src tests
	@echo "Checking import sorting..."
	isort --check-only --diff src tests
	@echo "✓ All linting checks passed!"

typecheck: ## Run type checking with mypy
	@echo "Running mypy type checking..."
	mypy src --ignore-missing-imports --no-strict-optional
	@echo "✓ Type checking passed!"

fmt: ## Format code (black, isort)
	@echo "Formatting code with black..."
	black src tests
	@echo "Sorting imports with isort..."
	isort src tests
	@echo "✓ Code formatting complete!"

# Testing
test: ## Run all tests
	@echo "Running all tests..."
	pytest -v --cov=src --cov-report=term-missing --cov-report=html
	@echo "✓ All tests completed!"

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/unit -v
	@echo "✓ Unit tests completed!"

test-int: ## Run integration tests only
	@echo "Running integration tests..."
	pytest tests/integration -v
	@echo "✓ Integration tests completed!"

test-e2e: ## Run end-to-end tests only
	@echo "Running E2E tests..."
	pytest tests/e2e -v
	@echo "✓ E2E tests completed!"

cov: ## Generate test coverage report
	@echo "Generating coverage report..."
	pytest --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "✓ Coverage report generated! Open htmlcov/index.html to view"

# Docker operations
build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Docker images built!"

up: ## Start all services with Docker Compose
	@echo "Starting services..."
	docker-compose up -d
	@echo "✓ Services started! Check 'make logs' for output"

down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped!"

logs: ## Show logs from all services
	docker-compose logs -f

# Database operations
migrate: ## Run database migrations
	@echo "Running database migrations..."
	alembic upgrade head
	@echo "✓ Database migrations completed!"

alembic-auto: ## Auto-generate migration from model changes
	@echo "Auto-generating migration..."
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"
	@echo "✓ Migration generated! Review and run 'make migrate'"

seed: ## Seed database with test data
	@echo "Seeding database..."
	python scripts/seed_database.py
	@echo "✓ Database seeded!"

# Development server
serve: ## Start development server
	@echo "Starting development server..."
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start production server
	@echo "Starting production server..."
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Monitoring and observability
monitor-up: ## Start monitoring stack (Grafana, Prometheus)
	@echo "Starting monitoring stack..."
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo "✓ Monitoring stack started!"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"

monitor-down: ## Stop monitoring stack
	@echo "Stopping monitoring stack..."
	docker-compose -f docker-compose.monitoring.yml down
	@echo "✓ Monitoring stack stopped!"

# Utilities
clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache dist build *.egg-info
	@echo "✓ Cleanup completed!"

check: ## Run all code quality checks (lint + typecheck)
	@echo "Running all code quality checks..."
	$(MAKE) lint
	$(MAKE) typecheck
	@echo "✓ All quality checks passed!"

ci: ## Run CI pipeline locally (lint, typecheck, test)
	@echo "Running CI pipeline locally..."
	$(MAKE) check
	$(MAKE) test
	@echo "✓ CI pipeline completed successfully!"

# Security
security: ## Run security checks
	@echo "Running security checks..."
	bandit -r src/
	safety check --json
	@echo "✓ Security checks completed!"

# Documentation
docs: ## Generate documentation
	@echo "Generating documentation..."
	cd docs && make html
	@echo "✓ Documentation generated! Open docs/_build/html/index.html"

docs-serve: ## Serve documentation locally
	@echo "Serving documentation..."
	cd docs/_build/html && python -m http.server 8080
	@echo "Documentation available at: http://localhost:8080"

# Quick development workflow
quick-check: fmt lint typecheck ## Quick code quality check and format

# Environment info
env-info: ## Show environment information
	@echo "Environment Information:"
	@echo "======================"
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Virtual environment: $$VIRTUAL_ENV"
	@echo "Current directory: $$(pwd)"
	@echo "Git branch: $$(git branch --show-current)"
	@echo "Git status: $$(git status --porcelain | wc -l) files changed"

# Database utilities
db-reset: ## Reset database (drop all tables and recreate)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "✓ Database reset completed!"; \
	else \
		echo "Database reset cancelled."; \
	fi

db-shell: ## Open database shell
	@echo "Opening database shell..."
	python -c "from src.core.database import get_db_url; print('Database URL:', get_db_url())"
	sqlite3 quote_master_pro.db

# Performance testing
perf: ## Run performance tests
	@echo "Running performance tests..."
	pytest tests/performance -v
	@echo "✓ Performance tests completed!"

# API utilities
api-docs: ## Open API documentation in browser
	@echo "API documentation available at:"
	@echo "  - Swagger UI: http://localhost:8000/docs"
	@echo "  - ReDoc: http://localhost:8000/redoc"

# Full development cycle
full-test: clean install lint typecheck test ## Full development test cycle

# Production deployment helpers
deploy-check: ## Check if ready for deployment
	@echo "Checking deployment readiness..."
	$(MAKE) ci
	@echo "Checking environment variables..."
	python scripts/check_env.py
	@echo "✓ Deployment check completed!"
