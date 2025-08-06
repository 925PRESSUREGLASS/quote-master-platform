# Quote Master Pro - File Upload Guide for Claude

This guide helps you select the most important files to upload to Claude for code analysis, debugging, or enhancement requests.

## 🎯 **Priority Files for Code Analysis**

### **📁 Core Configuration Files** (Always Upload)
```
├── README.md                    # Project overview and setup instructions
├── pyproject.toml              # Python dependencies and project config
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Container build instructions
├── .gitignore                  # Git ignore patterns
└── requirements.txt            # Python package requirements
```

### **🔧 Backend Core Files** (High Priority)
```
src/
├── main.py                     # FastAPI application entry point
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py                 # API router setup
│   ├── dependencies.py        # Dependency injection
│   └── routers/               # API endpoints (upload specific routes)
├── core/
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection setup
│   ├── exceptions.py          # Custom exceptions
│   └── security.py            # Authentication & security
├── models/                    # Database models
│   ├── user.py
│   ├── quote.py
│   ├── analytics.py
│   └── voice_recording.py
└── services/                  # Business logic
    ├── auth.py
    ├── ai/                    # AI service implementations
    ├── analytics/             # Analytics processing
    ├── quote/                 # Quote generation logic
    └── voice/                 # Voice processing
```

### **⚛️ Frontend Core Files** (High Priority)
```
frontend/
├── package.json               # Dependencies and scripts
├── vite.config.ts            # Build configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Styling configuration
├── index.html                # HTML entry point
└── src/
    ├── main.tsx              # React app entry point
    ├── App.tsx               # Main app component
    ├── index.css             # Global styles
    ├── components/           # React components
    │   ├── auth/            # Authentication components
    │   ├── layout/          # Layout components
    │   └── ui/              # UI components
    ├── pages/               # Page components
    │   ├── HomePage.tsx
    │   ├── auth/
    │   ├── dashboard/
    │   ├── quotes/
    │   └── analytics/
    ├── hooks/               # Custom React hooks
    │   ├── useAuth.ts
    │   └── useAnalytics.ts
    ├── services/            # API client services
    │   ├── api.ts
    │   └── auth.ts
    ├── store/              # State management
    │   ├── AuthContext.tsx
    │   ├── ThemeContext.tsx
    │   └── AnalyticsContext.tsx
    └── types/              # TypeScript definitions
        └── index.ts
```

### **🧪 Testing Files** (Medium Priority)
```
tests/
├── conftest.py               # Test configuration
├── unit/                     # Unit tests
│   ├── test_auth.py
│   └── test_quote_engine.py
├── integration/              # Integration tests
│   ├── test_api_auth.py
│   └── test_api_quotes.py
└── e2e/                     # End-to-end tests
    └── test_user_journey.py
```

### **🛠️ DevOps & Configuration** (Low Priority)
```
├── docker-compose.dev.yml    # Development containers
├── Dockerfile.dev           # Development container build
├── Makefile                 # Build automation
├── pytest.ini              # Test configuration
├── scripts/                 # Utility scripts
│   ├── start.sh
│   ├── dev.sh
│   └── seed_data.py
├── monitoring/              # Monitoring configuration
│   ├── prometheus.yml
│   └── grafana/
└── nginx/                   # Web server configuration
    ├── nginx.conf
    └── default.conf
```

## 🎯 **Upload Strategy by Use Case**

### **For Bug Fixes or Debugging:**
1. **Error-related files** (where the bug occurs)
2. **Configuration files** (pyproject.toml, package.json)
3. **Main entry points** (main.py, App.tsx)
4. **Relevant service/component files**

### **For New Features:**
1. **README.md** (understanding project scope)
2. **Related service files** (where feature will be added)
3. **API router files** (if backend feature)
4. **Component files** (if frontend feature)
5. **Type definitions** (types/index.ts)

### **For Architecture Review:**
1. **All configuration files**
2. **Main entry points** (main.py, App.tsx)
3. **Core module structure** (core/, services/)
4. **Database models**
5. **API structure** (routers/)

### **For Performance Optimization:**
1. **Configuration files**
2. **Service implementations**
3. **Database models and queries**
4. **Frontend components with performance concerns**

## 📝 **File Size Considerations**

**Small Files (Always Safe to Upload):**
- Configuration files (.json, .toml, .yml)
- Python modules (<500 lines)
- TypeScript components (<300 lines)
- README and documentation

**Medium Files (Upload Selectively):**
- Large components (>300 lines)
- Service implementations (>500 lines)
- Test files

**Large Files (Upload Only If Necessary):**
- Compiled assets
- Large data files
- Generated files

## 🚀 **Quick Upload Commands**

To get specific files for upload:

```bash
# Get main configuration files
type README.md pyproject.toml package.json

# Get main entry points  
type src/main.py frontend/src/main.tsx frontend/src/App.tsx

# Get specific service (example: auth)
type src/services/auth.py src/core/security.py

# Get API structure
type src/api/main.py src/api/dependencies.py
```

---

**💡 Tip**: Start with configuration files and main entry points, then add specific files based on your question or issue!
