# Claude Upload Files - Quote Master Pro

This folder contains organized copies of the most important files from the Quote Master Pro project for easy upload to Claude.

## � **Documentation Files** (Upload First for Context)
- `REPO_STRUCTURE_MAP.md` - Visual repository overview with technology stack info
- `CLAUDE_FILE_UPLOAD_GUIDE.md` - File selection strategies and upload tips
- `README.md` - This guide

## �📁 Folder Structure

### **1-core-config/** (Always Upload First)
Essential configuration files that define the project structure:
- `README.md` - Project overview and documentation
- `pyproject.toml` - Python dependencies and project configuration
- `docker-compose.yml` - Container orchestration setup
- `Dockerfile` - Container build instructions
- `.gitignore` - Git ignore patterns
- `requirements.txt` - Python package requirements

### **2-backend-core/** (High Priority)
Core backend application files:
- `main.py` - FastAPI application entry point
- `api_main.py` - API router setup
- `dependencies.py` - Dependency injection setup
- `config.py` - Application configuration
- `database.py` - Database connection setup  
- `security.py` - Authentication & security logic
- `exceptions.py` - Custom exception handling
- `model_user.py` - User database model
- `model_quote.py` - Quote database model
- `model_analytics.py` - Analytics database model
- `service_auth.py` - Authentication service

### **3-frontend-core/** (High Priority)
Core frontend application files:
- `package.json` - Frontend dependencies and scripts
- `vite.config.ts` - Build tool configuration
- `tsconfig.json` - TypeScript configuration
- `tailwind.config.js` - CSS framework configuration
- `index.html` - HTML entry point
- `main.tsx` - React application entry point
- `App.tsx` - Main React component
- `index.css` - Global styles
- `api.ts` - API client service
- `auth.ts` - Frontend authentication service
- `types.ts` - TypeScript type definitions

### **4-tests/** (Medium Priority)
Key testing files:
- `conftest.py` - Test configuration and fixtures
- `test_auth.py` - Authentication unit tests
- `test_api_auth.py` - Authentication integration tests

## 🎯 Upload Strategy

### **Quick Start (Upload These First):**

1. **Documentation files** (REPO_STRUCTURE_MAP.md, CLAUDE_FILE_UPLOAD_GUIDE.md)
2. All files from `1-core-config/`
3. `main.py` and `App.tsx` from backend/frontend folders
4. Any specific files related to your question

### **For Comprehensive Analysis:**
Upload all files in order: 1-core-config → 2-backend-core → 3-frontend-core → 4-tests

### **For Specific Issues:**
- **Authentication problems**: Upload `1-core-config/` + auth-related files
- **Frontend issues**: Upload `1-core-config/` + `3-frontend-core/`
- **Backend issues**: Upload `1-core-config/` + `2-backend-core/`
- **Setup/deployment**: Upload `1-core-config/` only

## 💡 Tips
- Start with configuration files (folder 1) to give Claude context
- Add specific files based on your question or issue
- The files are renamed for clarity (e.g., `api_main.py` instead of `main.py`)
- All files are copies - originals remain untouched

---
**Total Files**: ~20 core files covering the most important aspects of the Quote Master Pro platform.
