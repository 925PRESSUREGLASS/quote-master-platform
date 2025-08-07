# Project Structure & Testing Infrastructure Map

## Directory Structure Analysis

```
925WEB/                                 # Root project directory
├── tests/                              # Main testing directory
│   ├── __init__.py                     # Test package initialization
│   ├── conftest.py                     # Primary pytest configuration
│   ├── unit/                           # Unit tests directory
│   │   ├── __init__.py
│   │   └── test_auth.py                # Authentication unit tests
│   ├── integration/                    # Integration tests directory
│   │   ├── __init__.py
│   │   └── test_api_auth.py            # API authentication integration tests
│   └── e2e/                           # End-to-end tests directory
│       ├── __init__.py
│       └── test_user_journey.py        # User journey tests
│
├── claude-upload-files/4-tests/        # Claude analysis reference directory
│   ├── conftest.py                     # Reference test configuration
│   ├── test_api_auth.py                # Reference API auth tests
│   ├── test_auth.py                    # Reference auth tests
│   ├── BUILD_INFORMATION.md            # Comprehensive build information
│   ├── CLAUDE_SONNET_ANALYSIS.md       # Claude Sonnet analysis & recommendations
│   └── PROJECT_STRUCTURE_MAP.md        # This file
│
├── src/                               # Main application source code
│   ├── __init__.py
│   ├── main.py                        # FastAPI application entry point
│   ├── api/                           # API layer
│   │   ├── __init__.py
│   │   ├── main.py                    # API router configuration
│   │   ├── dependencies.py            # Dependency injection
│   │   ├── models/                    # Pydantic models
│   │   ├── routers/                   # API route handlers
│   │   ├── schemas/                   # Request/response schemas
│   │   └── v1/                        # API version 1 endpoints
│   ├── core/                          # Core application logic
│   │   ├── __init__.py
│   │   ├── config.py                  # Application configuration
│   │   ├── database.py                # Database connection & session
│   │   ├── exceptions.py              # Custom exceptions
│   │   └── security.py                # Security utilities
│   ├── models/                        # Database models
│   │   ├── __init__.py
│   │   ├── user.py                    # User model
│   │   ├── quote.py                   # Quote model
│   │   ├── analytics.py               # Analytics model
│   │   ├── voice_recording.py         # Voice recording model
│   │   ├── pricing_rule.py            # Pricing rules model
│   │   └── service_quote.py           # Service quote model
│   ├── services/                      # Business logic services
│   │   ├── __init__.py
│   │   ├── auth.py                    # Authentication service
│   │   ├── ai/                        # AI integration services
│   │   ├── analytics/                 # Analytics services
│   │   ├── quote/                     # Quote generation services
│   │   └── voice/                     # Voice processing services
│   └── workers/                       # Background task workers
│       ├── __init__.py
│       ├── background_tasks.py        # Background task definitions
│       └── celery_app.py              # Celery configuration
│
├── frontend/                          # React/TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── quotes/                # Quote-related components
│   │   │   └── ui/                    # UI components
│   │   ├── pages/
│   │   │   └── quotes/                # Quote pages
│   │   ├── services/
│   │   │   ├── api.ts                 # API client
│   │   │   └── quotes.ts              # Quote service
│   │   └── types/
│   │       └── index.ts               # TypeScript types
│   └── package.json                   # Frontend dependencies
│
├── requirements/                      # Python dependencies
│   ├── base.txt                       # Base requirements
│   ├── dev.txt                        # Development requirements
│   └── prod.txt                       # Production requirements
│
├── scripts/                           # Utility scripts
├── monitoring/                        # Monitoring configuration
├── nginx/                             # Nginx configuration
├── alembic/                          # Database migrations
└── docs/                             # Documentation
```

## Test Infrastructure Components

### Core Testing Files

#### Primary Configuration
- **`tests/conftest.py`**: Main pytest configuration with fixtures for:
  - Database testing (PostgreSQL with async SQLAlchemy)
  - Authentication testing (JWT tokens, user fixtures)
  - API testing (FastAPI TestClient, async HTTP client)
  - Environment configuration overrides

#### Reference Configuration  
- **`claude-upload-files/4-tests/conftest.py`**: Reference implementation showing:
  - Complete async testing setup
  - Comprehensive fixture examples
  - Test markers and collection customization
  - Performance testing foundations

### Current Test Coverage

#### Authentication Testing (70% coverage)
```
tests/unit/test_auth.py                 # Password hashing, JWT validation
tests/integration/test_api_auth.py      # Login/logout flows, protected endpoints
```

#### Missing Critical Tests (15% coverage)
```
# HIGH PRIORITY - Missing Files:
tests/unit/test_ai_service.py           # AI provider integration
tests/unit/test_pricing_engine.py       # Perth suburb pricing logic
tests/unit/test_email_service.py        # Email automation
tests/integration/test_quote_workflow.py # End-to-end quote generation
tests/performance/test_api_load.py      # Performance benchmarking
```

## Testing Strategy by Component

### AI Services Testing
**Location**: `src/services/ai/`
**Test Files Needed**:
- `tests/unit/test_ai_service.py` - Mock AI provider responses
- `tests/integration/test_ai_endpoints.py` - API endpoint testing
- `tests/performance/test_ai_response_time.py` - Performance testing

**Key Test Scenarios**:
- OpenAI API integration
- Anthropic API integration  
- Azure AI integration
- Provider fallback logic
- Rate limiting handling
- Error response management

### Quote Generation Testing
**Location**: `src/services/quote/`
**Test Files Needed**:
- `tests/unit/test_pricing_engine.py` - Pricing calculations
- `tests/unit/test_unified_generator.py` - Quote generation logic
- `tests/integration/test_quote_workflow.py` - Complete workflow

**Key Test Scenarios**:
- Perth suburb pricing variations
- Service type modifiers
- Material cost calculations
- Timeline estimation
- Quote personalization
- PDF generation

### Database Model Testing
**Location**: `src/models/`
**Current Coverage**: Partial (through integration tests)
**Enhancement Needed**:
- Model validation testing
- Relationship testing
- Migration testing
- Performance optimization testing

### API Endpoint Testing
**Location**: `src/api/routers/`
**Current Coverage**: Authentication endpoints only
**Missing Coverage**:
- Quote management endpoints
- Analytics endpoints
- Voice recording endpoints
- Admin endpoints

## Test Environment Configuration

### Database Setup
```python
# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/quote_master_test"

# Key features:
- Isolated test database
- Transaction rollback per test
- Async SQLAlchemy support
- Proper cleanup after test runs
```

### Mock Configuration  
```python
# AI Service Mocking
@patch('openai.AsyncOpenAI')
@patch('anthropic.AsyncAnthropic') 
@patch('azure.ai.openai.AsyncOpenAI')

# Email Service Mocking
@patch('smtplib.SMTP')
@patch('sendgrid.SendGridAPIClient')

# External API Mocking
@patch('httpx.AsyncClient')
```

### Environment Variables
```bash
# Test environment variables
ENVIRONMENT=test
DATABASE_URL=postgresql+asyncpg://localhost/quote_master_test
JWT_SECRET_KEY=test-secret-key
OPENAI_API_KEY=test-openai-key
ANTHROPIC_API_KEY=test-anthropic-key
REDIS_URL=redis://localhost:6379/15
```

## Performance Testing Infrastructure

### Load Testing Setup
```python
# Performance test configuration
- Concurrent user simulation (10-100 users)
- API response time monitoring (<2s target)
- Database query performance analysis
- Memory usage profiling
- Error rate monitoring (>99% success rate)
```

### Benchmarking Tools
- `pytest-benchmark` for function-level benchmarking
- `locust` for load testing (future enhancement)
- `pytest-asyncio` for async performance testing
- Custom performance fixtures in conftest.py

## CI/CD Integration Points

### GitHub Actions Integration
- Automated test execution on push/PR
- Multi-environment testing (PostgreSQL, Redis)
- Code coverage reporting
- Performance regression detection
- Security vulnerability scanning

### Test Execution Commands
```bash
# Development testing commands
pytest                                  # Run all tests
pytest tests/unit/ -v                  # Unit tests only  
pytest tests/integration/ -v           # Integration tests only
pytest -m "not slow"                   # Skip slow tests
pytest --cov=src --cov-report=html     # Coverage report
pytest tests/performance/              # Performance tests
```

## Documentation Integration

### Test Documentation Files
- `BUILD_INFORMATION.md` - Comprehensive build and testing information
- `CLAUDE_SONNET_ANALYSIS.md` - AI-focused analysis and recommendations  
- `PROJECT_STRUCTURE_MAP.md` - This structural overview
- `README.md` (project root) - Setup and execution instructions

### Code Documentation
- Docstrings in all test functions
- Type hints for test parameters
- Clear test naming conventions
- Fixture documentation in conftest.py

## Development Workflow Integration

### Pre-commit Hooks (Recommended)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit/
        language: system
        pass_filenames: false
        always_run: true
```

### IDE Integration
- VS Code pytest extension configuration
- Test discovery settings
- Debug configuration for tests
- Code coverage visualization

## Security Testing Framework

### Security Test Categories
- Authentication/authorization testing
- Input validation testing  
- SQL injection prevention
- XSS attack prevention
- JWT token security testing
- API rate limiting testing

### Security Test Implementation
```python
# Security testing patterns
@pytest.mark.security
async def test_sql_injection_prevention()
async def test_jwt_token_expiration()
async def test_api_rate_limiting()
async def test_input_sanitization()
```

## Monitoring & Alerting Integration

### Test Metrics Monitoring
- Test execution time tracking
- Coverage percentage monitoring
- Failure rate alerting
- Performance regression detection

### Integration with Monitoring Stack
- Prometheus metrics collection
- Grafana dashboard visualization
- Alert manager configuration
- Log aggregation for test failures

## Conclusion

This project structure provides a solid foundation for comprehensive testing but requires significant expansion in AI services and business logic coverage. The recommended approach is to implement testing in phases, starting with the most critical business logic components (AI services, pricing engine) and expanding to comprehensive integration and performance testing.

**Key Implementation Priorities**:
1. AI service mocking and testing infrastructure
2. Perth suburb pricing logic comprehensive testing
3. End-to-end quote generation workflow testing  
4. Performance monitoring and CI/CD integration
5. Security testing implementation
