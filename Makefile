# Quote Master Pro - Makefile

.PHONY: help install dev build start stop restart logs clean test lint format backup restore docs

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.yml -f docker-compose.dev.yml
PYTHON := python3
PIP := pip3

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Quote Master Pro - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ================================
# Installation and Setup
# ================================

install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@if [ -d frontend ]; then cd frontend && npm install; fi

setup-env: ## Setup environment files
	@echo "$(GREEN)Setting up environment files...$(NC)"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@if [ ! -f .env.dev ]; then cp .env.dev .env.dev; echo "Using .env.dev file"; fi
	@if [ -d frontend ] && [ ! -f frontend/.env ]; then cp frontend/.env.example frontend/.env; echo "Created frontend/.env file"; fi

init: setup-env ## Initialize the project (first time setup)
	@echo "$(GREEN)Initializing Quote Master Pro...$(NC)"
	@make install
	@make build
	@echo "$(GREEN)Initialization complete!$(NC)"

# ================================
# Development Commands
# ================================

dev: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

dev-frontend: ## Start frontend development server
	@echo "$(GREEN)Starting frontend development server...$(NC)"
	@cd frontend && npm run dev

dev-api: ## Start API in development mode
	@echo "$(GREEN)Starting API in development mode...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up api

dev-worker: ## Start worker in development mode
	@echo "$(GREEN)Starting worker in development mode...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up worker

dev-tools: ## Start development tools (adminer, redis-commander)
	@echo "$(GREEN)Starting development tools...$(NC)"
	@$(DOCKER_COMPOSE_DEV) --profile dev-tools up -d

# ================================
# Production Commands
# ================================

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build

start: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	@chmod +x scripts/start.sh
	@./scripts/start.sh

stop: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@$(DOCKER_COMPOSE_DEV) down

restart: stop start ## Restart all services

restart-api: ## Restart only the API service
	@echo "$(YELLOW)Restarting API service...$(NC)"
	@$(DOCKER_COMPOSE) restart api

restart-worker: ## Restart only the worker service
	@echo "$(YELLOW)Restarting worker service...$(NC)"
	@$(DOCKER_COMPOSE) restart worker

# ================================
# Database Commands
# ================================

db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api alembic upgrade head

db-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api alembic downgrade -1

db-reset: ## Reset database (WARNING: This will delete all data!)
	@echo "$(RED)Resetting database (this will delete all data!)$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) down; \
		docker volume rm quote-master-pro_postgres_data || true; \
		$(DOCKER_COMPOSE) up -d db; \
		sleep 10; \
		make db-migrate; \
	fi

db-seed: ## Seed database with sample data
	@echo "$(GREEN)Seeding database with sample data...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m src.scripts.seed_data

db-backup: ## Create database backup
	@echo "$(GREEN)Creating database backup...$(NC)"
	@chmod +x scripts/backup.sh
	@./scripts/backup.sh

db-restore: ## Restore database from backup
	@echo "$(GREEN)Restoring database from backup...$(NC)"
	@chmod +x scripts/restore.sh
	@./scripts/restore.sh

# ================================
# Monitoring and Logs
# ================================

logs: ## Show logs for all services
	@$(DOCKER_COMPOSE) logs -f

logs-api: ## Show API logs
	@$(DOCKER_COMPOSE) logs -f api

logs-worker: ## Show worker logs
	@$(DOCKER_COMPOSE) logs -f worker

logs-db: ## Show database logs
	@$(DOCKER_COMPOSE) logs -f db

status: ## Show service status
	@echo "$(GREEN)Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps

monitoring: ## Start monitoring stack (Prometheus + Grafana)
	@echo "$(GREEN)Starting monitoring stack...$(NC)"
	@$(DOCKER_COMPOSE) --profile monitoring up -d

# ================================
# Testing Commands
# ================================

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m pytest

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m pytest tests/unit

test-integration: ## Run integration tests only
	@echo "$(GREEN)Running integration tests...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m pytest tests/integration

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m pytest --cov=src --cov-report=html

test-frontend: ## Run frontend tests
	@echo "$(GREEN)Running frontend tests...$(NC)"
	@cd frontend && npm test

# ================================
# Code Quality Commands
# ================================

lint: ## Run linting for Python code
	@echo "$(GREEN)Running Python linting...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m flake8 src/
	@$(DOCKER_COMPOSE) run --rm api python -m black --check src/
	@$(DOCKER_COMPOSE) run --rm api python -m isort --check-only src/

lint-frontend: ## Run linting for frontend code
	@echo "$(GREEN)Running frontend linting...$(NC)"
	@cd frontend && npm run lint

format: ## Format Python code
	@echo "$(GREEN)Formatting Python code...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m black src/
	@$(DOCKER_COMPOSE) run --rm api python -m isort src/

format-frontend: ## Format frontend code
	@echo "$(GREEN)Formatting frontend code...$(NC)"
	@cd frontend && npm run format

type-check: ## Run type checking
	@echo "$(GREEN)Running type checking...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m mypy src/

# ================================
# Utility Commands
# ================================

shell: ## Open shell in API container
	@$(DOCKER_COMPOSE) run --rm api bash

shell-db: ## Open PostgreSQL shell
	@$(DOCKER_COMPOSE) exec db psql -U postgres -d quote_master

shell-redis: ## Open Redis shell
	@$(DOCKER_COMPOSE) exec redis redis-cli

clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f

clean-all: ## Clean up everything (images, volumes, containers)
	@echo "$(RED)Cleaning up everything...$(NC)"
	@read -p "This will remove all Docker images, volumes, and containers. Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE) down -v --remove-orphans; \
		docker system prune -af; \
		docker volume prune -f; \
	fi

docs: ## Generate API documentation
	@echo "$(GREEN)Generating API documentation...$(NC)"
	@$(DOCKER_COMPOSE) run --rm api python -m src.scripts.generate_docs

docs-serve: ## Serve documentation locally
	@echo "$(GREEN)Serving documentation...$(NC)"
	@echo "API Docs available at: http://localhost:8000/docs"
	@echo "ReDoc available at: http://localhost:8000/redoc"

# ================================
# Production Deployment
# ================================

deploy-staging: ## Deploy to staging environment
	@echo "$(GREEN)Deploying to staging...$(NC)"
	@# Add staging deployment commands here

deploy-production: ## Deploy to production environment
	@echo "$(GREEN)Deploying to production...$(NC)"
	@# Add production deployment commands here

# ================================
# Backup and Restore
# ================================

backup: ## Create full system backup
	@echo "$(GREEN)Creating full system backup...$(NC)"
	@chmod +x scripts/backup.sh
	@./scripts/backup.sh

restore: ## Restore from backup
	@echo "$(GREEN)Restoring from backup...$(NC)"
	@chmod +x scripts/restore.sh
	@./scripts/restore.sh

# ================================
# Health Checks
# ================================

health: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@curl -f http://localhost:8000/health || echo "API health check failed"
	@curl -f http://localhost:9090/-/healthy || echo "Prometheus health check failed"
	@curl -f http://localhost:3001/api/health || echo "Grafana health check failed"

# ================================
# Quick Commands
# ================================

quick-start: install build start ## Quick start for first time users
	@echo "$(GREEN)Quote Master Pro is ready!$(NC)"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

quick-dev: setup-env dev ## Quick development start
	@echo "$(GREEN)Development environment is ready!$(NC)"