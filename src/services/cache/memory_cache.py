"""
Memory Cache Adapter for Quote Master Pro AI Services

This module provides an in-memory cache implementation that can be used
as a fallback when Redis is not available. Perfect for development and testing.

Author: Quote Master Pro Development Team
Version: 1.0.0
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import threading
from dataclasses import asdict


class MemoryCache:
    """Thread-safe in-memory cache implementation."""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize memory cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        
        # Start cleanup task
        self._cleanup_task = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_task.start()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if 'expires_at' not in entry:
            return False
        return datetime.now().timestamp() > entry['expires_at']
    
    def _cleanup_expired(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items()
                        if self._is_expired(entry)
                    ]
                    for key in expired_keys:
                        del self._cache[key]
                
                # Sleep for 60 seconds before next cleanup
                time.sleep(60)
            except Exception:
                # Continue cleanup on any error
                time.sleep(60)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None
            
            return entry['value']
    
    async def set(self, key: str, value: Union[str, dict, list], ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Convert complex objects to JSON strings
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        
        expires_at = datetime.now().timestamp() + ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now().timestamp()
            }
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return False
            
            return True
    
    async def incr(self, key: str) -> int:
        """Increment integer value in cache."""
        with self._lock:
            current = await self.get(key)
            if current is None:
                new_value = 1
            else:
                try:
                    new_value = int(current) + 1
                except (ValueError, TypeError):
                    new_value = 1
            
            await self.set(key, str(new_value))
            return new_value
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        with self._lock:
            if key not in self._cache:
                return False
            
            self._cache[key]['expires_at'] = datetime.now().timestamp() + ttl
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_keys = len(self._cache)
            expired_keys = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            
            return {
                'total_keys': total_keys,
                'expired_keys': expired_keys,
                'active_keys': total_keys - expired_keys,
                'cache_type': 'memory'
            }


# Global memory cache instance
_memory_cache_instance = None
_cache_lock = threading.Lock()


def get_memory_cache() -> MemoryCache:
    """Get singleton memory cache instance."""
    global _memory_cache_instance
    
    if _memory_cache_instance is None:
        with _cache_lock:
            if _memory_cache_instance is None:
                _memory_cache_instance = MemoryCache()
    
    return _memory_cache_instance


# Redis-compatible interface for easy switching
class MemoryRedis:
    """Redis-compatible interface using memory cache."""
    
    def __init__(self):
        self.cache = get_memory_cache()
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value (returns bytes to match Redis interface)."""
        value = await self.cache.get(key)
        return value.encode('utf-8') if value else None
    
    async def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None) -> bool:
        """Set value with expiration."""
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        return await self.cache.set(key, value, ex)
    
    async def delete(self, key: str) -> int:
        """Delete key (returns 1 if deleted, 0 if not found)."""
        deleted = await self.cache.delete(key)
        return 1 if deleted else 0
    
    async def exists(self, key: str) -> int:
        """Check if key exists (returns 1 if exists, 0 if not)."""
        exists = await self.cache.exists(key)
        return 1 if exists else 0
    
    async def incr(self, key: str) -> int:
        """Increment counter."""
        return await self.cache.incr(key)
    
    async def expire(self, key: str, time: int) -> int:
        """Set expiration (returns 1 if successful)."""
        success = await self.cache.expire(key, time)
        return 1 if success else 0
    
    async def ping(self) -> bytes:
        """Ping command (always returns PONG for memory cache)."""
        return b'PONG'


async def create_redis_connection(redis_url: str) -> Union[MemoryRedis, Any]:
    """
    Create Redis connection with fallback to memory cache.
    
    Args:
        redis_url: Redis URL or 'memory://localhost' for memory cache
        
    Returns:
        Redis connection or MemoryRedis instance
    """
    if redis_url.startswith('memory://'):
        return MemoryRedis()
    
    try:
        # Try to import and connect to real Redis
        import redis.asyncio as aioredis
        
        redis_client = aioredis.from_url(redis_url, decode_responses=False)
        
        # Test connection
        await redis_client.ping()
        return redis_client
        
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("🔄 Falling back to memory cache")
        return MemoryRedis()


# Test function
async def test_memory_cache():
    """Test memory cache functionality."""
    cache = get_memory_cache()
    
    print("🧪 Testing Memory Cache...")
    
    # Test basic operations
    await cache.set("test_key", "test_value", 60)
    value = await cache.get("test_key")
    assert value == "test_value", f"Expected 'test_value', got '{value}'"
    
    # Test JSON serialization
    test_data = {"message": "Hello", "timestamp": datetime.now()}
    await cache.set("json_key", test_data, 60)
    json_value = await cache.get("json_key")
    assert json_value is not None, "JSON value should not be None"
    
    # Test counter
    count = await cache.incr("counter")
    assert count == 1, f"Expected counter to be 1, got {count}"
    
    # Test expiration
    await cache.set("expire_test", "will_expire", 1)
    exists_before = await cache.exists("expire_test")
    assert exists_before, "Key should exist before expiration"
    
    print("✅ Basic cache operations work")
    
    # Test Redis-compatible interface
    redis_cache = MemoryRedis()
    await redis_cache.set("redis_test", b"redis_value", 60)
    redis_value = await redis_cache.get("redis_test")
    assert redis_value == b"redis_value", f"Expected b'redis_value', got {redis_value}"
    
    # Test ping
    pong = await redis_cache.ping()
    assert pong == b'PONG', f"Expected b'PONG', got {pong}"
    
    print("✅ Redis-compatible interface works")
    
    # Show statistics
    stats = cache.get_stats()
    print(f"📊 Cache stats: {stats}")
    
    print("🎉 Memory cache test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_memory_cache())
