# 🚀 Quote Master Pro - PRODUCTION SECURITY & MIDDLEWARE

## Context
You are implementing Quote Master Pro, an enterprise-grade AI-powered quote generation platform. This is PRODUCTION SECURITY & MIDDLEWARE of a 9-phase implementation plan.

## Current Project Structure
- **Backend**: FastAPI with SQLAlchemy, multi-provider AI service (OpenAI/Claude/Azure)
- **Frontend**: React with TypeScript, Tailwind CSS
- **Database**: PostgreSQL with Redis caching
- **Architecture**: Clean architecture with domain-driven design

## Phase Objective

*Duration: 3-4 days | Priority: CRITICAL*

### Goals
- Implement enterprise-grade security middleware
- Add comprehensive authentication and authorization
- Set up distributed rate limiting and DDoS protection

### Implementation Tasks

#### 3.1 Security Middleware Stack
```python
src/middleware/security/
├── __init__.py
├── auth_middleware.py          # JWT validation & refresh
├── rate_limiter.py            # Distributed rate limiting
├── cors_handler.py            # Advanced CORS configuration
├── security_headers.py        # Security headers injection
├── input_sanitizer.py         # Input sanitization
└── csrf_protection.py         # CSRF token management
```

#### 3.2 Authentication & Authorization
```python
src/services/auth/
├── __init__.py
├── jwt_service.py             # JWT token management
├── oauth_providers.py         # OAuth2 integration
├── rbac_service.py           # Role-based access control
├── session_manager.py         # Session management
├── password_service.py        # Password hashing/validation
└── mfa_service.py            # Multi-factor authentication
```

#### 3.3 Rate Limiting & DDoS Protection
```python
src/middleware/protection/
├── __init__.py
├── distributed_rate_limiter.py   # Redis-based rate limiting
├── ddos_protection.py            # DDoS attack mitigation
├── request_validator.py          # Request validation
├── ip_whitelist.py               # IP whitelist management
└── abuse_detector.py             # Abuse pattern detection
```

#### 3.4 Monitoring & Observability
```python
src/middleware/monitoring/
├── __init__.py
├── request_tracker.py         # Request tracking
├── performance_monitor.py     # Performance monitoring
├── error_tracker.py           # Error tracking & reporting
├── audit_logger.py            # Security audit logging
└── metrics_collector.py       # Custom metrics collection
```

### Deliverables
- [ ] Enterprise security middleware implementation
- [ ] JWT-based authentication system
- [ ] Role-based access control (RBAC)
- [ ] Distributed rate limiting
- [ ] DDoS protection mechanisms
- [ ] Comprehensive audit logging

---



## Implementation Instructions
1. Generate complete, production-ready implementations
2. Include comprehensive error handling and logging
3. Add type hints for Python code and proper TypeScript types
4. Follow existing code patterns and architecture
5. Include docstrings and comments for complex logic
6. Consider performance, security, and scalability
7. Generate corresponding test files where applicable

## Quality Requirements
- ✅ Production-ready code with error handling
- ✅ Comprehensive logging and monitoring
- ✅ Type safety (Python type hints, TypeScript)
- ✅ Security best practices
- ✅ Performance optimization
- ✅ Documentation and comments

## File Generation Format
When generating files, use this format:
```
# File: path/to/file.py
# Dependencies: package1>=1.0.0, package2>=2.0.0
# Description: Brief description of the file purpose

[Complete file content here]
```

Generate all files needed for this phase. Ask if you need clarification on any requirements.
