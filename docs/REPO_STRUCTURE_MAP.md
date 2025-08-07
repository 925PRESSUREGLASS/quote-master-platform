# Quote Master Pro - Repository Structure Map

> **AI-Powered Quote Generation Platform with Voice Processing and Psychology Integration**

## 🏗️ **Project Overview**

```
quote-master-platform/
├── 📄 Core Project Files
├── 🐍 Python Backend (FastAPI)
├── ⚛️ React Frontend (TypeScript)
├── 🐳 Docker Configuration
├── 🔧 DevOps & Monitoring
├── 🧪 Testing Suite
└── 📚 Documentation
```

## 📁 **Detailed Structure**

### 📄 **Root Level - Configuration**
```
├── README.md                   # Project documentation
├── pyproject.toml             # Python project configuration
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Production containers
├── docker-compose.dev.yml     # Development containers
├── Dockerfile                 # Production container build
├── Dockerfile.dev            # Development container build
├── Makefile                  # Build automation commands
├── pytest.ini               # Test configuration
└── .gitignore               # Git ignore patterns
```

### 🐍 **Backend - Python FastAPI Application**
```
src/
├── main.py                   # 🚀 Application entry point
├── __init__.py
├── 
├── api/                      # 🌐 API Layer
│   ├── __init__.py
│   ├── main.py              # API router configuration
│   ├── dependencies.py      # Dependency injection
│   ├── models/             # Pydantic request/response models
│   ├── routers/            # API endpoint routes
│   ├── schemas/            # Data validation schemas
│   └── v1/                 # API versioning
│
├── core/                    # 🔧 Core System Components
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection & sessions
│   ├── exceptions.py       # Custom exception handling
│   └── security.py         # Authentication & security
│
├── models/                  # 🗄️ Database Models (SQLAlchemy)
│   ├── __init__.py
│   ├── user.py            # User model & relationships
│   ├── quote.py           # Quote model & metadata
│   ├── analytics.py       # Analytics & tracking
│   └── voice_recording.py # Voice processing data
│
├── services/               # 💼 Business Logic Layer
│   ├── __init__.py
│   ├── auth.py            # Authentication service
│   ├── ai/                # 🤖 AI Integration Services
│   │   ├── __init__.py
│   │   ├── openai_service.py
│   │   └── anthropic_service.py
│   ├── analytics/         # 📊 Analytics Processing
│   ├── quote/            # 💭 Quote Generation Logic
│   └── voice/            # 🎤 Voice Processing
│
├── workers/               # ⚡ Background Task Processing
│   ├── __init__.py
│   └── background_tasks.py
│
└── utils/                # 🛠️ Utility Functions
    └── helpers.py
```

### ⚛️ **Frontend - React TypeScript Application**
```
frontend/
├── index.html              # 🏠 HTML entry point
├── package.json           # NPM dependencies & scripts
├── vite.config.ts         # Build tool configuration
├── tsconfig.json          # TypeScript configuration
├── tsconfig.node.json     # Node.js TypeScript config
├── tailwind.config.js     # CSS framework config
├── postcss.config.js      # CSS processing
├── .eslintrc.cjs         # Code linting rules
├── .prettierrc           # Code formatting
│
└── src/
    ├── main.tsx          # 🚀 React app entry point
    ├── App.tsx           # Main application component
    ├── index.css         # Global styles
    │
    ├── components/       # 🧩 Reusable UI Components
    │   ├── auth/        # 🔐 Authentication components
    │   │   ├── AdminRoute.tsx
    │   │   └── ProtectedRoute.tsx
    │   ├── layout/      # 📐 Layout components
    │   │   ├── Header.tsx
    │   │   ├── Layout.tsx
    │   │   └── Sidebar.tsx
    │   └── ui/          # 🎨 Base UI components
    │
    ├── pages/           # 📄 Route-based page components
    │   ├── HomePage.tsx
    │   ├── NotFoundPage.tsx
    │   ├── admin/       # Admin dashboard pages
    │   ├── analytics/   # Analytics & reports
    │   ├── auth/        # Login, register, etc.
    │   ├── dashboard/   # User dashboard
    │   ├── profile/     # User profile management
    │   ├── quotes/      # Quote generation & management
    │   ├── settings/    # Application settings
    │   └── voice/       # Voice processing interface
    │
    ├── hooks/           # 🪝 Custom React hooks
    │   ├── useAnalytics.ts
    │   └── useAuth.ts
    │
    ├── services/        # 🌐 API Client Services
    │   ├── api.ts       # Base API client
    │   └── auth.ts      # Authentication API calls
    │
    ├── store/           # 🗂️ State Management (Context)
    │   ├── AnalyticsContext.tsx
    │   ├── AuthContext.tsx
    │   └── ThemeContext.tsx
    │
    ├── types/           # 📝 TypeScript Type Definitions
    │   └── index.ts
    │
    └── utils/           # 🛠️ Utility Functions
        └── cn.ts        # Class name utilities
```

### 🧪 **Testing Suite**
```
tests/
├── __init__.py
├── conftest.py             # Test configuration & fixtures
├── 
├── unit/                   # 🔬 Unit Tests
│   ├── __init__.py
│   ├── test_auth.py       # Authentication logic tests
│   └── test_quote_engine.py # Quote generation tests
├── 
├── integration/            # 🔗 Integration Tests
│   ├── __init__.py
│   ├── test_api_auth.py   # API authentication tests
│   └── test_api_quotes.py # Quote API tests
└── 
└── e2e/                   # 🎭 End-to-End Tests
    ├── __init__.py
    └── test_user_journey.py # Complete user workflows
```

### 🐳 **DevOps & Infrastructure**
```
├── .github/               # 🚀 GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml        # Continuous Integration
│       ├── cd.yml        # Continuous Deployment
│       ├── security.yml  # Security scanning
│       ├── release.yml   # Release automation
│       └── maintenance.yml
│
├── monitoring/           # 📊 System Monitoring
│   ├── prometheus.yml    # Metrics collection
│   └── grafana/         # Dashboards & visualization
│       └── provisioning/
│           ├── dashboards/
│           └── datasources/
│
├── nginx/               # 🌐 Web Server Configuration
│   ├── nginx.conf       # Main nginx config
│   └── default.conf     # Default site config
│
├── requirements/        # 📦 Environment-specific deps
│   ├── base.txt        # Base requirements
│   ├── dev.txt         # Development requirements
│   └── prod.txt        # Production requirements
│
└── scripts/            # 🛠️ Utility Scripts
    ├── backup.sh       # Database backup
    ├── dev.sh          # Development setup
    ├── init-db.sql     # Database initialization
    ├── restore.sh      # Database restore
    ├── seed_data.py    # Sample data creation
    ├── start.sh        # Production startup
    └── test.sh         # Test runner
```

### 📚 **Documentation & Guides**
```
├── README.md                    # Main project documentation
├── CLAUDE_FILE_UPLOAD_GUIDE.md  # File selection guide
├── claude-upload-files/         # Organized files for AI analysis
│   ├── 1-core-config/          # Configuration files
│   ├── 2-backend-core/         # Backend essentials
│   ├── 3-frontend-core/        # Frontend essentials
│   └── 4-tests/                # Key test files
└── file_structure_export.txt    # Complete file listing
```

## 🏷️ **Key Features by Directory**

| Directory | Purpose | Technologies |
|-----------|---------|-------------|
| `src/` | Backend API & business logic | FastAPI, SQLAlchemy, Python 3.11+ |
| `frontend/src/` | User interface & client logic | React 18, TypeScript, Vite, Tailwind |
| `tests/` | Quality assurance & testing | pytest, pytest-asyncio |
| `monitoring/` | System observability | Prometheus, Grafana |
| `nginx/` | Web server & reverse proxy | nginx |
| `scripts/` | DevOps automation | Bash, Python scripts |

## 🚀 **Quick Navigation**

- **🐛 Bug Fixing**: Start with `src/` and `frontend/src/`
- **🆕 New Features**: Check `src/services/` and `frontend/src/pages/`
- **⚙️ Configuration**: Look in root level and `src/core/`
- **🧪 Testing**: Explore `tests/` directory
- **🚀 Deployment**: Check Docker files and `scripts/`
- **📊 Monitoring**: See `monitoring/` and `nginx/`

---

**📝 Note**: This map shows the logical organization. Some directories may not exist yet but represent the planned structure for the complete application.
