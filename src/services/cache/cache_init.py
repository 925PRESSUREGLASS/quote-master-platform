"""
Redis Cache Initialization and Configuration
Ensures Redis connection is properly initialized for the application
"""

import asyncio
import logging
from typing import Dict, Any
import time

from src.services.cache.redis_connection import get_redis_manager
from src.services.cache.response_cache import cache_service
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def initialize_redis_cache() -> Dict[str, Any]:
    """
    Initialize Redis cache system with health checks and configuration validation
    
    Returns:
        Dict containing initialization results and configuration info
    """
    try:
        logger.info("Initializing Redis cache system...")
        
        # Get Redis manager
        redis_manager = get_redis_manager()
        
        # Test sync connection
        sync_connected = redis_manager.connect()
        
        # Test async connection  
        async_connected = await redis_manager.async_connect()
        
        # Perform basic functionality tests
        test_results = await _run_cache_tests(redis_manager)
        
        # Get system info
        system_info = _get_system_info(redis_manager)
        
        initialization_result = {
            "status": "success" if (sync_connected or async_connected) else "failed",
            "redis_config": {
                "host": redis_manager.host,
                "port": redis_manager.port,
                "db": redis_manager.db,
                "connected": redis_manager.connected
            },
            "connections": {
                "sync": sync_connected,
                "async": async_connected
            },
            "test_results": test_results,
            "system_info": system_info,
            "cache_service": {
                "strategies": [strategy.value for strategy in cache_service.__class__.__dict__.get("CacheStrategy", [])],
                "ttl_config": getattr(cache_service, 'ttl_config', {}),
                "prefix": getattr(cache_service, 'cache_prefix', 'unknown')
            },
            "timestamp": time.time()
        }
        
        if sync_connected or async_connected:
            logger.info("✅ Redis cache initialization completed successfully",
                       extra={"sync_connected": sync_connected, "async_connected": async_connected})
        else:
            logger.warning("⚠️ Redis cache initialization completed with fallback to memory cache")
        
        return initialization_result
        
    except Exception as e:
        logger.error(f"❌ Redis cache initialization failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback": "memory_cache",
            "timestamp": time.time()
        }

async def _run_cache_tests(redis_manager) -> Dict[str, Any]:
    """Run basic cache functionality tests"""
    test_results = {
        "basic_operations": False,
        "async_operations": False,
        "ttl_support": False,
        "performance": {}
    }
    
    try:
        # Test basic sync operations
        test_key = f"test:cache_init:{int(time.time())}"
        test_value = {"test": "value", "timestamp": time.time()}
        
        # Sync test
        start_time = time.time()
        redis_manager.set(test_key, test_value, ex=60)
        retrieved_value = redis_manager.get(test_key)
        sync_time = (time.time() - start_time) * 1000
        
        if retrieved_value and isinstance(retrieved_value, dict) and retrieved_value.get("test") == "value":
            test_results["basic_operations"] = True
            test_results["performance"]["sync_roundtrip_ms"] = round(sync_time, 2)
        
        # Clean up sync test
        redis_manager.delete(test_key)
        
        # Test async operations
        async_test_key = f"test:async_cache_init:{int(time.time())}"
        start_time = time.time()
        await redis_manager.async_set(async_test_key, test_value, ex=60)
        async_retrieved = await redis_manager.async_get(async_test_key)
        async_time = (time.time() - start_time) * 1000
        
        if async_retrieved and isinstance(async_retrieved, dict) and async_retrieved.get("test") == "value":
            test_results["async_operations"] = True
            test_results["performance"]["async_roundtrip_ms"] = round(async_time, 2)
        
        # Clean up async test
        await redis_manager.async_delete(async_test_key)
        
        # Test TTL support
        ttl_test_key = f"test:ttl:{int(time.time())}"
        redis_manager.set(ttl_test_key, "ttl_test", ex=1)
        
        if redis_manager.exists(ttl_test_key):
            test_results["ttl_support"] = True
        
        logger.info("Cache functionality tests completed", extra=test_results)
        
    except Exception as e:
        logger.warning(f"Cache tests failed: {e}")
        test_results["error"] = str(e)
    
    return test_results

def _get_system_info(redis_manager) -> Dict[str, Any]:
    """Get system information"""
    system_info = {
        "memory_cache_enabled": True,
        "memory_cache_size": len(redis_manager.memory_cache) if redis_manager.memory_cache else 0,
        "settings": {
            "cache_enabled": settings.enable_caching,
            "redis_host": settings.redis_host,
            "redis_port": settings.redis_port,
            "redis_db": settings.redis_db,
            "cache_ttl": settings.cache_ttl,
            "cache_prefix": settings.cache_prefix
        }
    }
    
    return system_info

async def cleanup_redis_cache():
    """Cleanup Redis cache connections"""
    try:
        logger.info("Cleaning up Redis cache connections...")
        redis_manager = get_redis_manager()
        redis_manager.close()
        logger.info("✅ Redis cache cleanup completed")
    except Exception as e:
        logger.error(f"❌ Redis cache cleanup failed: {e}")

# Convenience function for health checks
async def check_cache_health() -> Dict[str, Any]:
    """Quick health check for cache system"""
    try:
        redis_manager = get_redis_manager()
        
        # Quick connectivity test
        test_key = f"health:{int(time.time())}"
        start_time = time.time()
        
        # Try Redis first
        if redis_manager.connected:
            await redis_manager.async_set(test_key, "ping", ex=10)
            result = await redis_manager.async_get(test_key)
            await redis_manager.async_delete(test_key)
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "backend": "redis",
                "latency_ms": round(latency, 2),
                "connected": True
            }
        else:
            # Test memory cache
            redis_manager.memory_cache[test_key] = "ping"
            result = redis_manager.memory_cache.get(test_key)
            del redis_manager.memory_cache[test_key]
            
            return {
                "status": "healthy",
                "backend": "memory",
                "latency_ms": 0,
                "connected": False,
                "note": "Using memory cache fallback"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "backend": "unknown"
        }
