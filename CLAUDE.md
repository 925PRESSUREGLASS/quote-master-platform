# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quote Master Pro is an AI-powered quote generation platform with voice processing and psychology integration. It features a FastAPI backend with a React TypeScript frontend, supporting multiple AI providers (OpenAI, Anthropic), voice processing, and comprehensive monitoring.

## Development Commands

### Backend (Python/FastAPI)
- **Development server**: `make serve` or `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`
- **Production server**: `make serve-prod`
- **Install dependencies**: `make install` or `pip install -r requirements.txt`
- **Run all tests**: `make test` (includes unit, integration, and e2e tests)
- **Run specific test types**: `make test-unit`, `make test-int`, `make test-e2e`
- **Lint and format**: `make lint` (flake8, black check, isort check)
- **Format code**: `make fmt` (black, isort)
- **Type checking**: `make typecheck` (mypy)
- **Quick quality check**: `make quick-check` (format + lint + typecheck)
- **Full CI pipeline**: `make ci` (lint + typecheck + test)

### Frontend (React/TypeScript)
- **Development server**: `cd frontend && npm run dev`
- **Build**: `cd frontend && npm run build`
- **Type checking**: `cd frontend && npm run type-check`
- **Lint**: `cd frontend && npm run lint`
- **Format**: `cd frontend && npm run format`

### Database Operations
- **Run migrations**: `make migrate` (alembic upgrade head)
- **Auto-generate migration**: `make alembic-auto`
- **Reset database**: `make db-reset` (drops all tables and recreates)
- **Database shell**: `make db-shell`

### Docker Operations
- **Build images**: `make build`
- **Start services**: `make up`
- **Stop services**: `make down`
- **View logs**: `make logs`

### Monitoring
- **Start monitoring stack**: `make monitor-up` (Grafana at localhost:3000, Prometheus at localhost:9090)
- **Stop monitoring**: `make monitor-down`

## Architecture Overview

### Backend Structure
- **FastAPI Application**: `src/api/main.py` - Main FastAPI app with comprehensive monitoring, CORS, and middleware
- **Configuration**: `src/core/config.py` - Centralized settings using pydantic-settings
- **Database**: `src/core/database.py` - SQLAlchemy async setup with health checks
- **Models**: `src/models/` - SQLAlchemy models for users, quotes, analytics, voice recordings
- **API Routes**: `src/api/routers/` - Modular routers for auth, quotes, voice, analytics, admin
- **Services Layer**: `src/services/` - Business logic including AI services, caching, monitoring

### AI Service Architecture
- **Multi-provider Support**: `src/services/ai/ai_service.py` - Supports OpenAI, Anthropic, Azure OpenAI
- **Orchestrator**: `src/services/ai/orchestrator.py` - Intelligent provider selection and fallback
- **Enhanced AI Service**: `src/services/ai/enhanced_ai_service.py` - Production-ready service with monitoring
- **Monitoring**: `src/services/ai/monitoring/` - Tracing, circuit breakers, smart routing

### Frontend Structure
- **React App**: `frontend/src/App.tsx` - Main application with routing
- **Pages**: `frontend/src/pages/` - Route components organized by feature
- **Components**: `frontend/src/components/` - Reusable UI components
- **Services**: `frontend/src/services/` - API clients and business logic
- **Context**: `frontend/src/store/` - React context for auth, analytics, theme

### Cache System
- **Redis Integration**: `src/services/cache/` - Redis connection with memory fallback
- **Response Caching**: Smart caching for AI responses and API calls
- **Cache Middleware**: `src/api/middleware/cache_middleware.py` - Request-level caching

### Monitoring & Observability
- **OpenTelemetry**: Comprehensive tracing and metrics
- **Prometheus**: Application metrics and monitoring
- **Grafana**: Dashboards for business KPIs and system metrics
- **Structured Logging**: Using structlog for consistent logging

## Testing Strategy

The project uses pytest with comprehensive test organization:
- **Unit Tests**: `tests/unit/` - Fast, isolated component tests
- **Integration Tests**: `tests/integration/` - Service interaction tests
- **E2E Tests**: `tests/e2e/` - Full system workflow tests
- **Performance Tests**: `tests/performance/` - Load and performance benchmarks
- **Security Tests**: `tests/security/` - Security validation tests

Test markers: `unit`, `integration`, `performance`, `security`, `slow`

## Database

- **ORM**: SQLAlchemy with async support
- **Migrations**: Alembic for database schema management
- **Development**: SQLite (`quote_master_pro.db`)
- **Production**: PostgreSQL support configured

## Environment Variables

Key environment variables are managed through `src/core/config.py`:
- AI service keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Database: `DATABASE_URL`
- Redis: `REDIS_URL` (defaults to memory cache)
- Security: `SECRET_KEY`

## Code Quality

The project enforces strict code quality standards:
- **Black**: Code formatting (88 character line limit)
- **isort**: Import sorting
- **flake8**: Linting with E203, W503 ignored
- **mypy**: Type checking with `--ignore-missing-imports`
- **pytest**: 90% code coverage requirement

Always run `make check` before committing to ensure code quality standards are met.
