# Redis Setup Guide for Quote Master Pro

## Current Issue
WSL is disabled, which prevents Docker Desktop from running properly. This affects our Redis setup needed for AI service caching and rate limiting.

## Solution Options

### Option 1: Fix WSL and Use Docker (Recommended)

**Step 1: Enable WSL with Administrator privileges**
```batch
# Right-click PowerShell -> "Run as Administrator"
# Then run this script:
.\scripts\fix_wsl.bat
```

**Step 2: After restart, verify WSL**
```powershell
wsl --list --verbose
wsl --set-default-version 2
```

**Step 3: Start Docker Desktop and Redis**
```bash
docker-compose up redis -d
```

### Option 2: Install Redis on Windows directly

**Download Redis for Windows:**
1. Go to: https://github.com/microsoftarchive/redis/releases
2. Download Redis-x64-3.0.504.msi
3. Install Redis as Windows service

**Start Redis:**
```cmd
redis-server
# Default: localhost:6379
```

### Option 3: Use Redis Cloud (Free tier)
1. Sign up at: https://redis.com/try-free/
2. Create free database
3. Update `.env` with cloud connection string

### Option 4: Use Memory Cache (Temporary)
For development without Redis, we can use in-memory caching:

```python
# In .env file, set:
REDIS_URL=memory://localhost
```

## Current Setup Status

✅ **AI Services Ready**: Both AI Service and Unified Quote Generator are implemented
✅ **Docker Compose**: Redis configuration exists in docker-compose.yml
❌ **WSL**: Currently disabled (Error: 0x80070422)
❌ **Docker Desktop**: Cannot start without WSL2
❌ **Redis**: Not running

## Quick Fix for Development

I'll create a memory-based cache adapter so you can test the AI services immediately while we fix WSL.
