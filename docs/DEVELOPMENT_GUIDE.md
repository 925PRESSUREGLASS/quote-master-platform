# Quote Master Pro - Development Guide

## 📋 Table of Contents

- [🚀 Quick Setup](#-quick-setup)
- [🛠️ Development Environment](#️-development-environment)
- [📦 Package Management](#-package-management)
- [🔧 Configuration](#-configuration)
- [🧪 Testing](#-testing)
- [📊 Code Quality](#-code-quality)
- [🐛 Debugging](#-debugging)
- [🔄 Workflow](#-workflow)
- [📈 Performance](#-performance)
- [🤝 Contributing](#-contributing)

---

## 🚀 Quick Setup

### **Prerequisites**

Ensure you have the following installed:

```bash
# Check versions
python --version          # 3.11+
node --version            # 18+
npm --version             # 8+
docker --version          # 20+
git --version             # 2.30+
```

### **One-Command Setup**

```bash
# Clone and setup everything
git clone https://github.com/925PRESSUREGLASS/quote-master-platform.git
cd quote-master-platform
make dev-setup  # Runs full development setup
```

### **Manual Setup Steps**

```bash
# 1. Backend setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements/dev.txt

# 2. Frontend setup
cd frontend
npm install
cd ..

# 3. Environment configuration
cp .env.example .env
# Edit .env with your API keys and settings

# 4. Database setup
alembic upgrade head
python scripts/seed_data.py

# 5. Pre-commit hooks
pre-commit install
```

---

## 🛠️ Development Environment

### **Development Servers**

#### **Option 1: Docker Compose (Recommended)**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### **Option 2: Manual Start**
```bash
# Terminal 1: Backend API
source .venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Background workers (optional)
celery -A src.workers.celery_app worker --loglevel=info

# Terminal 4: Monitoring (optional)
docker-compose -f docker-compose.monitoring.yml up -d
```

### **Development URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | React development server |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | System health status |
| **Grafana** | http://localhost:3001 | Monitoring dashboards |
| **Prometheus** | http://localhost:9090 | Metrics collection |

---

## 📦 Package Management

### **Backend Dependencies**

```bash
# Install new package
pip install package-name

# Add to requirements
pip freeze | grep package-name >> requirements.txt

# Development dependencies
pip install package-name
echo "package-name" >> requirements/dev.txt

# Update dependencies
pip install --upgrade -r requirements.txt
```

### **Frontend Dependencies**

```bash
cd frontend

# Install new package
npm install package-name

# Development dependency
npm install --save-dev package-name

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

### **Dependency Management Best Practices**

- Pin exact versions in production (`==` for Python, exact versions for npm)
- Use version ranges in development (`>=` for Python, `^` for npm)
- Regularly update and test dependencies
- Document breaking changes in CHANGELOG.md

---

## 🔧 Configuration

### **Environment Files**

```bash
# Development
.env                    # Local development settings
.env.example           # Example configuration (committed)

# Testing
.env.test              # Test environment overrides

# Production
.env.production        # Production settings (not committed)
```

### **Configuration Structure**

```python
# src/core/config.py
class Settings(BaseSettings):
    # Application
    app_name: str = "Quote Master Pro"
    environment: str = "development"
    debug: bool = True

    # AI Services
    openai_api_key: str
    anthropic_api_key: str

    # Database
    database_url: str = "sqlite:///./quote_master_pro.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
```

### **Required Environment Variables**

```bash
# Core Settings
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=True

# AI Service API Keys (REQUIRED)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional AI Services
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Database
DATABASE_URL=sqlite:///./quote_master_pro.db
# DATABASE_URL=postgresql://user:pass@localhost/dbname  # For PostgreSQL

# Cache
REDIS_URL=redis://localhost:6379/0

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

---

## 🧪 Testing

### **Test Structure**

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                      # Fast, isolated unit tests
│   ├── test_auth.py          # Authentication logic
│   ├── test_quote_engine.py  # Quote generation
│   └── test_ai_service.py    # AI service logic
├── integration/              # Service integration tests
│   ├── test_api_auth.py     # Authentication API
│   ├── test_api_quotes.py   # Quote generation API
│   └── test_ai_integration.py # AI service integration
├── e2e/                     # End-to-end user journey tests
│   ├── test_user_journey.py # Complete user workflows
│   └── test_system.py      # Full system tests
├── performance/             # Load and performance tests
│   └── test_ai_performance.py
└── security/               # Security validation tests
    └── test_security_validation.py
```

### **Running Tests**

```bash
# All tests with coverage
make test

# Specific test categories
make test-unit          # Fast unit tests
make test-int          # Integration tests
make test-e2e          # End-to-end tests
make test-perf         # Performance tests

# Test with specific options
pytest tests/unit -v                    # Verbose unit tests
pytest tests/unit/test_auth.py         # Specific test file
pytest -k "test_user_registration"     # Test by name pattern
pytest --cov=src --cov-report=html     # Coverage report
```

### **Writing Tests**

#### **Unit Test Example**
```python
# tests/unit/test_quote_engine.py
import pytest
from src.services.quote.engine import QuoteEngine

class TestQuoteEngine:
    @pytest.fixture
    def quote_engine(self):
        return QuoteEngine()

    def test_generate_quote_success(self, quote_engine):
        """Test successful quote generation."""
        prompt = "inspiration for success"
        result = quote_engine.generate(prompt)

        assert result is not None
        assert len(result.text) > 0
        assert result.quality_score > 0.5
```

#### **Integration Test Example**
```python
# tests/integration/test_api_quotes.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestQuoteAPI:
    def test_generate_quote_endpoint(self, authenticated_user):
        """Test quote generation API endpoint."""
        headers = {"Authorization": f"Bearer {authenticated_user.access_token}"}
        data = {
            "prompt": "motivation for work",
            "style": "inspirational",
            "max_tokens": 150
        }

        response = client.post("/api/v1/quotes/generate",
                             json=data, headers=headers)

        assert response.status_code == 200
        assert "text" in response.json()
        assert "quality_score" in response.json()
```

### **Test Configuration**

```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --tb=short
    --cov=src
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=90
    --durations=10
    --strict-markers
asyncio_mode = auto
```

---

## 📊 Code Quality

### **Code Quality Tools**

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Code formatting | `pyproject.toml` |
| **isort** | Import sorting | `pyproject.toml` |
| **Flake8** | Linting | `setup.cfg` |
| **MyPy** | Type checking | `mypy.ini` |
| **Pre-commit** | Git hooks | `.pre-commit-config.yaml` |

### **Code Quality Commands**

```bash
# Format code
make fmt               # Format with black and isort
black src tests        # Format specific directories
isort src tests        # Sort imports

# Linting
make lint             # Run all linting tools
flake8 src tests      # Check code style
mypy src              # Type checking

# All quality checks
make check            # Run all quality tools
make ci               # Full CI pipeline locally
```

### **Pre-commit Configuration**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

### **Code Style Guidelines**

#### **Python Code Style**
- **Line Length**: 88 characters (Black default)
- **Import Order**: isort with Black compatibility
- **Docstrings**: Google style docstrings
- **Type Hints**: Full type annotations for public APIs
- **Error Handling**: Explicit exception handling with logging

```python
# Good example
async def generate_quote(
    prompt: str,
    style: Optional[str] = None,
    max_tokens: int = 150
) -> QuoteResponse:
    """Generate an AI quote based on the given prompt.

    Args:
        prompt: The input prompt for quote generation
        style: Optional style preference (inspirational, motivational, etc.)
        max_tokens: Maximum tokens in the generated response

    Returns:
        QuoteResponse object containing the generated quote and metadata

    Raises:
        AIServiceError: When AI service fails to generate quote
        ValidationError: When input parameters are invalid
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Quote generation failed: {e}")
        raise AIServiceError("Failed to generate quote") from e
```

#### **TypeScript Code Style**
- **ESLint + Prettier**: Consistent formatting
- **Strict TypeScript**: No implicit any types
- **Interface over Type**: Use interfaces for object shapes
- **Functional Components**: Prefer function components with hooks

```typescript
// Good example
interface QuoteGenerationProps {
  onQuoteGenerated: (quote: Quote) => void;
  initialPrompt?: string;
  style?: QuoteStyle;
}

const QuoteGenerator: React.FC<QuoteGenerationProps> = ({
  onQuoteGenerated,
  initialPrompt = "",
  style = "inspirational"
}) => {
  const [prompt, setPrompt] = useState(initialPrompt);
  const [loading, setLoading] = useState(false);

  const generateQuote = useCallback(async () => {
    setLoading(true);
    try {
      const quote = await quoteService.generate({ prompt, style });
      onQuoteGenerated(quote);
    } catch (error) {
      console.error('Quote generation failed:', error);
    } finally {
      setLoading(false);
    }
  }, [prompt, style, onQuoteGenerated]);

  return (
    // Component JSX
  );
};
```

---

## 🐛 Debugging

### **Backend Debugging**

#### **Development Debugging**
```python
# Add to code for debugging
import pdb; pdb.set_trace()  # Interactive debugger

# Or use logging
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message with data: %s", data)
```

#### **VS Code Debug Configuration**
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug FastAPI",
            "type": "python",
            "request": "launch",
            "program": "src/api/main.py",
            "args": [],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        }
    ]
}
```

### **Frontend Debugging**

#### **Browser DevTools**
- Use React Developer Tools extension
- Network tab for API debugging
- Console for JavaScript errors
- Performance tab for optimization

#### **VS Code Extensions**
- ES7+ React/Redux/React-Native snippets
- TypeScript Importer
- Auto Rename Tag
- Bracket Pair Colorizer

### **Logging Configuration**

```python
# src/core/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

---

## 🔄 Workflow

### **Git Workflow**

```bash
# 1. Start new feature
git checkout -b feature/amazing-feature

# 2. Make changes
git add .
git commit -m "feat: add amazing feature"

# 3. Push and create PR
git push origin feature/amazing-feature
# Create Pull Request on GitHub

# 4. After PR approval
git checkout main
git pull origin main
git branch -d feature/amazing-feature
```

### **Commit Message Convention**

```bash
# Format: type(scope): description

feat: add new quote generation endpoint
fix: resolve AI service timeout issue
docs: update API documentation
style: format code with black
refactor: restructure quote service
test: add unit tests for auth service
chore: update dependencies
```

### **Pull Request Process**

1. **Create Feature Branch**: `feature/description` or `fix/description`
2. **Write Tests**: Ensure new code has tests
3. **Run Quality Checks**: `make check` passes
4. **Update Documentation**: Update relevant docs
5. **Create PR**: Use the PR template
6. **Code Review**: Address reviewer feedback
7. **Merge**: Squash and merge after approval

### **Release Process**

```bash
# 1. Update version
bump2version patch  # or minor, major

# 2. Create release branch
git checkout -b release/v1.2.3

# 3. Update CHANGELOG.md
# Add release notes and breaking changes

# 4. Create release PR
# PR to main branch

# 5. After merge, create git tag
git tag v1.2.3
git push origin v1.2.3

# 6. GitHub Actions will handle deployment
```

---

## 📈 Performance

### **Performance Monitoring**

```bash
# Start monitoring stack
make monitor-up

# Access dashboards
open http://localhost:3001  # Grafana
open http://localhost:9090  # Prometheus
```

### **Performance Testing**

```bash
# Load testing with locust
pip install locust
locust -f tests/performance/locustfile.py

# Profile specific endpoints
python -m cProfile -s tottime scripts/profile_endpoint.py
```

### **Optimization Guidelines**

#### **Backend Performance**
- Use async/await for I/O operations
- Implement connection pooling for databases
- Cache frequently accessed data
- Use background tasks for heavy operations
- Monitor database query performance

#### **Frontend Performance**
- Code splitting with React.lazy()
- Memoize expensive computations
- Optimize image loading and sizing
- Use React Query for server state
- Implement virtual scrolling for large lists

---

## 🤝 Contributing

### **Development Setup Checklist**

- [ ] Repository cloned and setup complete
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized with test data
- [ ] Pre-commit hooks installed
- [ ] Development servers running
- [ ] Tests passing (`make test`)
- [ ] Code quality checks passing (`make check`)

### **Before Submitting PR**

- [ ] Feature branch created from latest main
- [ ] New tests written for changes
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code formatted and linted
- [ ] Commit messages follow convention
- [ ] PR description filled out completely

### **Getting Help**

- **Documentation**: Check `docs/` directory
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Code Review**: Tag team members for review
- **Slack/Discord**: Internal team communication

---

This development guide provides comprehensive information for developers working on Quote Master Pro. Keep this document updated as the project evolves and new tools or processes are introduced.
