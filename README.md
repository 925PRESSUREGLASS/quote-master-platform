# Quote Master Pro

> 🚀 **AI-Powered Quote Generation Platform** with Advanced Voice Processing, Psychology Integration, and Multi-Provider AI Orchestration

[![Build Status](https://github.com/925PRESSUREGLASS/quote-master-platform/workflows/CI/badge.svg)](https://github.com/925PRESSUREGLASS/quote-master-platform/actions)
[![CodeQL](https://github.com/925PRESSUREGLASS/quote-master-platform/workflows/CodeQL/badge.svg)](https://github.com/925PRESSUREGLASS/quote-master-platform/security)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

---

## 📋 Table of Contents

- [🌟 Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [🔧 Development](#-development)
- [📊 API Documentation](#-api-documentation)
- [🐳 Docker Deployment](#-docker-deployment)
- [📈 Monitoring](#-monitoring)
- [🧪 Testing](#-testing)
- [📁 Project Structure](#-project-structure)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🌟 Features

### 🤖 **AI-Powered Quote Generation**
- **Multi-Provider AI Integration**: Seamlessly integrate OpenAI GPT-4, Anthropic Claude, and Azure OpenAI
- **Smart Provider Orchestration**: Intelligent model selection with automatic fallback and load balancing
- **Circuit Breaker Protection**: Resilient AI service with automatic failure detection and recovery
- **Quality Scoring & Validation**: Advanced quality assessment with psychological analysis
- **Style & Tone Adaptation**: Generate quotes matching specific authors, styles, or emotional tones

### 🎤 **Advanced Voice Processing**
- **Speech-to-Text**: High-accuracy voice recognition using OpenAI Whisper
- **Multi-Language Support**: Process recordings in 50+ languages
- **Voice-to-Quote Pipeline**: Transform spoken thoughts directly into inspirational quotes
- **Audio Analysis**: Sentiment analysis, emotional tone detection, and speaker insights
- **Real-time Processing**: Stream voice input with live transcription and quote generation

### 🧠 **Psychology Integration**
- **Emotional Intelligence**: Analyze psychological themes and emotional impact scores
- **Personality Mapping**: Match quotes to MBTI types, Big Five traits, and user preferences
- **Therapeutic Applications**: Generate contextual quotes for mental health and wellness
- **Behavioral Analytics**: Track user patterns and personalize quote recommendations
- **Mood-Based Generation**: Adaptive quotes based on detected emotional states

### 📊 **Analytics & Monitoring**
- **Real-time Dashboards**: Comprehensive analytics with business KPIs and system metrics
- **User Engagement Tracking**: Detailed insights into quote usage, favorites, and sharing
- **AI Performance Metrics**: Monitor model performance, costs, and response times
- **OpenTelemetry Integration**: Distributed tracing with Grafana and Prometheus
- **Cost Optimization**: Track and optimize AI service costs across providers

### 🔧 **Modern Architecture**
- **FastAPI Backend**: High-performance async API with automatic OpenAPI documentation
- **React TypeScript Frontend**: Modern, responsive UI with Tailwind CSS and Framer Motion
- **Microservices Ready**: Modular architecture with independent service scaling
- **Container-First**: Full Docker containerization with Docker Compose orchestration
- **CI/CD Pipeline**: Automated testing, security scans, and multi-environment deployment

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend"
        A[React TypeScript App]
        B[Tailwind CSS]
        C[React Router]
    end

    subgraph "API Gateway"
        D[FastAPI Server]
        E[Authentication Middleware]
        F[Rate Limiting]
    end

    subgraph "AI Orchestration Layer"
        G[AI Service Manager]
        H[Circuit Breaker]
        I[Load Balancer]
    end

    subgraph "AI Providers"
        J[OpenAI GPT-4]
        K[Anthropic Claude]
        L[Azure OpenAI]
    end

    subgraph "Data Layer"
        M[PostgreSQL/SQLite]
        N[Redis Cache]
        O[File Storage]
    end

    subgraph "Monitoring"
        P[OpenTelemetry]
        Q[Prometheus]
        R[Grafana]
    end

    A --> D
    D --> G
    G --> H
    H --> J & K & L
    D --> M & N
    D --> P
    P --> Q --> R
```

### **Tech Stack**

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Framer Motion, React Query |
| **Backend** | FastAPI 0.104+, Python 3.11+, Pydantic V2, SQLAlchemy 2.0 |
| **AI Services** | OpenAI GPT-4, Anthropic Claude, Azure OpenAI, Whisper |
| **Database** | PostgreSQL 15+ (Production), SQLite (Development) |
| **Cache** | Redis 7+, Memory Cache (Fallback) |
| **Monitoring** | OpenTelemetry, Prometheus, Grafana, Jaeger |
| **Deployment** | Docker, Docker Compose, GitHub Actions |
| **Security** | JWT Authentication, OAuth 2.0, Rate Limiting, CORS |

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+ with pip
- Node.js 18+ with npm
- Docker & Docker Compose (optional)
- Git

### **1. Clone Repository**

```bash
git clone https://github.com/925PRESSUREGLASS/quote-master-platform.git
cd quote-master-platform
```

### **2. Backend Setup**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### **3. Database Setup**

```bash
# Initialize database
alembic upgrade head

# Seed with sample data (optional)
python scripts/seed_data.py
```

### **4. Frontend Setup**

```bash
cd frontend
npm install
```

### **5. Start Development**

```bash
# Terminal 1: Backend
python -m uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Monitoring (optional)
docker-compose -f docker-compose.monitoring.yml up -d
```

**🎉 Access your application:**
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Grafana**: http://localhost:3001 (admin/admin)

---

## 🔧 Development

### **Using Make Commands**

The project includes a comprehensive Makefile for development workflows:

```bash
# Code Quality
make lint          # Run all linting tools
make fmt           # Format code with black and isort
make typecheck     # Run mypy type checking
make check         # Run all quality checks

# Testing
make test          # Run all tests with coverage
make test-unit     # Unit tests only
make test-int      # Integration tests only
make test-e2e      # End-to-end tests only

# Development Server
make serve         # Start development server
make serve-prod    # Start production server

# Database
make migrate       # Run database migrations
make db-reset      # Reset database (DESTRUCTIVE)
make seed          # Seed database with test data

# Docker Operations
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make logs          # View service logs

# Monitoring
make monitor-up    # Start monitoring stack
make monitor-down  # Stop monitoring stack
```

### **Environment Configuration**

Create `.env` file with required settings:

```bash
# Application
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# AI Services (REQUIRED)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_API_KEY=your-azure-key  # Optional
AZURE_OPENAI_ENDPOINT=https://...    # Optional

# Database
DATABASE_URL=sqlite:///./quote_master_pro.db
# DATABASE_URL=postgresql://user:pass@localhost/dbname  # Production

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

---

## 📊 API Documentation

### **Interactive API Docs**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### **Core Endpoints**

#### **Authentication**
```http
POST /api/v1/auth/register     # Register new user
POST /api/v1/auth/login        # User login
POST /api/v1/auth/refresh      # Refresh JWT token
POST /api/v1/auth/logout       # User logout
```

#### **Quote Generation**
```http
POST /api/v1/quotes/generate                    # Generate quote
POST /api/v1/quotes/generate/enhanced           # Enhanced AI generation
POST /api/v1/quotes/generate/stream             # Streaming generation
GET  /api/v1/quotes/ai-service/health           # AI service health
POST /api/v1/quotes/ai-service/circuit-breaker/reset/{provider}  # Reset circuit breaker
```

#### **Voice Processing**
```http
POST /api/v1/voice/transcribe           # Transcribe audio to text
POST /api/v1/voice/quote-from-voice     # Generate quote from voice
GET  /api/v1/voice/recordings           # List recordings
DELETE /api/v1/voice/recordings/{id}    # Delete recording
```

#### **Analytics**
```http
GET /api/v1/analytics/dashboard         # User dashboard data
GET /api/v1/analytics/quotes            # Quote analytics
GET /api/v1/analytics/usage             # Usage statistics
```

### **Example Requests**

#### Generate Quote
```bash
curl -X POST "http://localhost:8000/api/v1/quotes/generate/enhanced" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "inspiration for overcoming challenges",
    "style": "motivational",
    "tone": "positive",
    "max_tokens": 150,
    "include_psychology": true
  }'
```

#### Voice to Quote
```bash
curl -X POST "http://localhost:8000/api/v1/voice/quote-from-voice" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio_file=@recording.wav" \
  -F "style=inspirational"
```

---

## 🐳 Docker Deployment

### **Development with Docker**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Production Deployment**

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Include monitoring
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

### **Services Overview**

| Service | Port | Description |
|---------|------|-------------|
| **API** | 8000 | FastAPI backend server |
| **Frontend** | 3000 | React development server |
| **Database** | 5432 | PostgreSQL database |
| **Redis** | 6379 | Cache and session store |
| **Grafana** | 3001 | Monitoring dashboards |
| **Prometheus** | 9090 | Metrics collection |

---

## 📈 Monitoring

### **Observability Stack**

The platform includes comprehensive monitoring with:

- **📊 Grafana Dashboards**: Business KPIs, system metrics, AI service monitoring
- **📈 Prometheus Metrics**: Application metrics, custom business metrics
- **🔍 Distributed Tracing**: OpenTelemetry with Jaeger for request tracing
- **⚡ Real-time Alerting**: Prometheus AlertManager with webhook integration

### **Key Metrics Tracked**

- **Business Metrics**: Quote generation rates, user engagement, revenue metrics
- **AI Service Metrics**: Request latency, success rates, cost per request, model performance
- **System Metrics**: API response times, database performance, cache hit rates
- **User Experience**: Page load times, error rates, user journey analytics

### **Access Monitoring**

```bash
# Start monitoring stack
make monitor-up

# Access dashboards
open http://localhost:3001  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

---

## 🧪 Testing

### **Test Structure**

```
tests/
├── unit/                 # Fast, isolated unit tests
├── integration/          # Service integration tests
├── e2e/                 # End-to-end user journey tests
├── performance/         # Load and performance tests
└── security/           # Security validation tests
```

### **Running Tests**

```bash
# All tests with coverage
make test

# Specific test types
make test-unit          # Unit tests only
make test-int           # Integration tests
make test-e2e           # End-to-end tests
make test-perf          # Performance tests

# Coverage report
make cov               # Generate HTML coverage report
```

### **Test Configuration**

- **Framework**: pytest with async support
- **Coverage**: 90%+ requirement with htmlcov reporting
- **Fixtures**: Comprehensive test data and mock services
- **CI Integration**: Automated testing in GitHub Actions

---

## 📁 Project Structure

```
quote-master-platform/
├── 📁 src/                          # Backend source code
│   ├── 📁 api/                      # FastAPI application
│   │   ├── 📁 routers/             # API route handlers
│   │   ├── 📁 schemas/             # Pydantic request/response models
│   │   ├── 📁 models/              # Database models
│   │   └── 📁 middleware/          # Custom middleware
│   ├── 📁 services/                # Business logic services
│   │   ├── 📁 ai/                  # AI service integrations
│   │   ├── 📁 quote/               # Quote generation engine
│   │   ├── 📁 voice/               # Voice processing
│   │   ├── 📁 cache/               # Caching services
│   │   └── 📁 monitoring/          # Observability
│   ├── 📁 core/                    # Core utilities
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Database setup
│   │   └── security.py             # Security utilities
│   └── 📁 workers/                 # Background task workers
├── 📁 frontend/                     # React TypeScript frontend
│   ├── 📁 src/
│   │   ├── 📁 components/          # React components
│   │   ├── 📁 pages/               # Route components
│   │   ├── 📁 services/            # API clients
│   │   ├── 📁 hooks/               # Custom React hooks
│   │   └── 📁 store/               # State management
│   └── 📁 public/                  # Static assets
├── 📁 tests/                       # Test suites
├── 📁 docs/                        # Documentation
├── 📁 scripts/                     # Utility scripts
├── 📁 monitoring/                  # Monitoring configuration
│   ├── 📁 grafana/                 # Grafana dashboards
│   └── 📁 prometheus/              # Prometheus config
├── 📁 infrastructure/              # Infrastructure as Code
├── 🐳 docker-compose*.yml          # Docker orchestration
├── 📋 requirements*.txt            # Python dependencies
├── ⚙️ Makefile                     # Development commands
└── 📄 README.md                    # This file
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

### **Development Workflow**

1. **Fork & Clone**: Fork the repository and clone your fork
2. **Branch**: Create a feature branch (`git checkout -b feature/amazing-feature`)
3. **Develop**: Make your changes with tests
4. **Quality**: Run `make check` to ensure code quality
5. **Test**: Run `make test` to verify all tests pass
6. **Commit**: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)
7. **Push**: Push to your fork (`git push origin feature/amazing-feature`)
8. **PR**: Open a Pull Request with detailed description

### **Code Standards**

- **Python**: Black formatting, isort imports, flake8 linting, mypy typing
- **TypeScript**: ESLint + Prettier, strict TypeScript configuration
- **Testing**: 90%+ coverage requirement
- **Documentation**: Comprehensive docstrings and README updates

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 and Whisper AI models
- **Anthropic** for Claude AI integration
- **FastAPI** for the excellent Python web framework
- **React Team** for the frontend framework
- **Open Source Community** for the amazing tools and libraries

---

## 📞 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/925PRESSUREGLASS/quote-master-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/925PRESSUREGLASS/quote-master-platform/discussions)

---

<div align="center">

**Made with ❤️ by the Quote Master Pro Team**

[⭐ Star us on GitHub](https://github.com/925PRESSUREGLASS/quote-master-platform) | [🐛 Report Bug](https://github.com/925PRESSUREGLASS/quote-master-platform/issues) | [💡 Request Feature](https://github.com/925PRESSUREGLASS/quote-master-platform/issues)

</div>
