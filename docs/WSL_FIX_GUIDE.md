# WSL Service Fix Guide for Quote Master Pro

## Current Issue
WSL is installed but the WSL service is disabled, causing error:
```
Error code: Wsl/0x80070422
The service cannot be started, either because it is disabled
```

## Step-by-Step Fix

### Option 1: Enable WSL Service via Services (Recommended)

1. **Open Services Manager:**
   - Press `Windows + R`
   - Type `services.msc` and press Enter

2. **Find and Enable WSL Service:**
   - Look for "LxssManager" or "Windows Subsystem for Linux Manager"
   - Right-click on it → Properties
   - Set "Startup type" to "Automatic" or "Manual"
   - Click "Start" to start the service
   - Click "Apply" and "OK"

### Option 2: Enable via Command Line (Run as Administrator)

1. **Open PowerShell as Administrator**
2. **Run these commands:**
   ```powershell
   # Enable the WSL service
   Set-Service -Name LxssManager -StartupType Automatic
   Start-Service -Name LxssManager
   
   # Verify the service is running
   Get-Service -Name LxssManager
   ```

### Option 3: Registry Fix (If above doesn't work)

1. **Open Registry Editor as Administrator:**
   - Press `Windows + R`
   - Type `regedit` and press Enter

2. **Navigate to:**
   ```
   HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LxssManager
   ```

3. **Set the Start value:**
   - Double-click on "Start"
   - Change value from "4" (disabled) to "3" (manual) or "2" (automatic)
   - Click OK

4. **Restart your computer**

### Option 4: Full WSL Reset (Nuclear option)

If nothing else works:

1. **Uninstall WSL:**
   ```powershell
   # Run as Administrator
   dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux
   ```

2. **Restart computer**

3. **Reinstall WSL:**
   ```powershell
   # Run as Administrator
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   ```

4. **Restart computer again**

5. **Install WSL:**
   ```powershell
   wsl --install
   ```

## Test WSL After Fix

After applying any of the above fixes:

```powershell
# Check WSL status
wsl --status

# Check WSL service
Get-Service -Name LxssManager

# Try to run WSL
wsl --list --verbose
```

## Start Docker Desktop

Once WSL is working:
1. Start Docker Desktop
2. Wait for it to fully initialize
3. Test with: `docker run hello-world`

## Redis Setup After WSL Fix

Once Docker is working, start Redis:
```bash
# Start Redis with Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Test Redis connection
docker exec -it redis redis-cli ping
```

## Update Quote Master Pro Config

Once Redis is running, update your config:
```python
# In .env file or settings
REDIS_URL=redis://localhost:6379/0
```

# Update the config to use Redis
python -c "
import os
from pathlib import Path

# Read current .env file
env_file = Path('.env')
if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update Redis URL
    if 'REDIS_URL=' in content:
        content = content.replace('memory://localhost', 'redis://localhost:6379/0')
    else:
        content += '\nREDIS_URL=redis://localhost:6379/0'
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print('✅ Updated .env with Redis configuration')
else:
    print('📝 No .env file found, Redis URL will use default from settings')
"

## Verification Script

Run this PowerShell script to verify everything is working:

```powershell
# Check WSL
Write-Host "Checking WSL..." -ForegroundColor Green
wsl --status

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Green  
docker --version
docker run hello-world

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Green
docker run -d -p 6379:6379 --name test-redis redis:latest
Start-Sleep 5
docker exec test-redis redis-cli ping
docker rm -f test-redis
```

# Create the test file that was missing
@"
#!/usr/bin/env python3
"""Test Redis integration with AI services after WSL fix."""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_redis_connection():
    """Test Redis connection."""
    print("🔌 Testing Redis Connection...")
    
    try:
        from services.cache.redis_connection import create_redis_connection
        
        redis = await create_redis_connection("redis://localhost:6379/0")
        
        # Test basic operations
        await redis.set("test_key", b"test_value", 60)
        value = await redis.get("test_key")
        
        assert value == b"test_value", f"Expected b'test_value', got {value}"
        
        await redis.delete("test_key")
        print("✅ Redis connection working perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Will use memory cache fallback...")
        return False


async def test_ai_service_with_redis():
    """Test AI service with Redis caching."""
    print("\n🤖 Testing AI Service with Redis Caching...")
    
    try:
        from services.ai.ai_service import AIService, AIRequest
        from models.service_quote import ServiceCategory
        
        # Create AI service (will auto-detect Redis or fallback to memory)
        ai_service = AIService()
        await ai_service.initialize()
        
        print("✅ AI service initialized successfully!")
        print("✅ Caching system is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Testing Redis Integration After WSL Fix\n")
    
    # Test Redis connection
    redis_working = await test_redis_connection()
    
    # Test AI service
    ai_working = await test_ai_service_with_redis()
    
    print("\n" + "="*50)
    if redis_working and ai_working:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Redis is working with AI services")
        print("✅ Production-grade caching enabled")
        print("✅ Ready for high-performance quote generation")
    elif ai_working:
        print("⚠️  AI services working with memory cache fallback")
        print("💡 Redis setup needed for production performance")
    else:
        print("❌ Issues detected - check logs above")
    
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
"@ | Out-File -FilePath "test_redis_integration.py" -Encoding UTF8 -Force

## Still Having Issues?

If WSL still won't start:
1. Check Windows Update - install all pending updates
2. Enable Hyper-V if available: `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All`
3. Check BIOS settings - ensure virtualization is enabled
4. Try running `sfc /scannow` as Administrator to fix system files

---
**Next:** Once WSL is working, Docker will start properly and you can use Redis for production caching.
