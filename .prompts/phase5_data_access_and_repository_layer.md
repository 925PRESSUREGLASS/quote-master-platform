# 🚀 Quote Master Pro - DATA ACCESS & REPOSITORY LAYER

## Context
You are implementing Quote Master Pro, an enterprise-grade AI-powered quote generation platform. This is DATA ACCESS & REPOSITORY LAYER of a 9-phase implementation plan.

## Current Project Structure
- **Backend**: FastAPI with SQLAlchemy, multi-provider AI service (OpenAI/Claude/Azure)
- **Frontend**: React with TypeScript, Tailwind CSS
- **Database**: PostgreSQL with Redis caching
- **Architecture**: Clean architecture with domain-driven design

## Phase Objective

*Duration: 3-4 days | Priority: MEDIUM*

### Goals
- Implement repository pattern with Unit of Work
- Add advanced caching strategies
- Optimize database performance

### Implementation Tasks

#### 5.1 Repository Pattern Implementation
```python
src/repositories/
├── base/
│   ├── __init__.py
│   ├── repository.py          # Generic repository base
│   ├── unit_of_work.py       # Transaction management
│   ├── specifications.py     # Query specifications
│   └── pagination.py         # Pagination utilities
├── implementations/
│   ├── user_repository.py     # User data access
│   ├── quote_repository.py    # Quote operations
│   ├── analytics_repository.py # Analytics data
│   └── audit_repository.py    # Audit trail
└── cache/
    ├── cache_manager.py       # Multi-tier caching
    ├── invalidation.py        # Cache invalidation
    ├── warming.py             # Cache warming strategies
    └── distributed_cache.py   # Distributed cache management
```

#### 5.2 Database Optimization
```python
src/database/
├── __init__.py
├── connection_manager.py      # Connection pooling
├── query_optimizer.py        # Query optimization
├── migration_manager.py       # Database migrations
├── backup_manager.py          # Automated backups
└── performance_monitor.py     # Database performance monitoring
```

### Deliverables
- [ ] Repository pattern with Unit of Work
- [ ] Multi-tier caching strategy
- [ ] Database query optimization
- [ ] Automated backup system
- [ ] Database performance monitoring

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
