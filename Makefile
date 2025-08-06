# Quote Master Pro - Makefile

.PHONY: help install dev build test clean deploy docker-build docker-up docker-down

# Default target
help:
	@echo "Quote Master Pro - Available Commands:"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make test        - Run all tests"
	@echo ""
	@echo "🏗️  Production:"
	@echo "  make build       - Build production images"
	@echo "  make deploy      - Deploy to production"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-up   - Start with Docker Compose"
	@echo "  make docker-down - Stop Docker services"
	@echo "  make docker-logs - View service logs"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make format      - Format code"
	@echo "  make lint        - Run linting"

# Install dependencies
install:
	@echo "📦 Installing backend dependencies..."
	pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Dependencies installed!"

# Development environment
dev:
	@echo "🚀 Starting development environment..."
	./scripts/dev.sh

# Build production
build:
	@echo "🏗️  Building production images..."
	docker-compose build

# Run tests
test:
	@echo "🧪 Running tests..."
	./scripts/test.sh

# Clean artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf __pycache__ .pytest_cache
	rm -rf frontend/dist frontend/node_modules/.cache
	docker system prune -f

# Format code
format:
	@echo "✨ Formatting code..."
	black src/
	isort src/
	cd frontend && npm run format

# Lint code
lint:
	@echo "🔍 Linting code..."
	flake8 src/
	mypy src/
	cd frontend && npm run lint

# Docker commands
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing service logs..."
	docker-compose logs -f

# Production deployment
deploy: build
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Make sure to set production environment variables!"
	docker-compose -f docker-compose.yml up -d