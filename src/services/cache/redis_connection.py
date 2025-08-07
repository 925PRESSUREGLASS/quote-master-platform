"""
Redis Connection Manager for Quote Master Pro
Provides centralized Redis connection management with fallback to memory cache
"""
import redis
import redis.asyncio as redis_async
import asyncio
import logging
from typing import Any, Optional, Dict
from datetime import timedelta
import json
import pickle
import hashlib

logger = logging.getLogger(__name__)

class RedisConnectionManager:
    """Redis connection manager with automatic failover to memory cache"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.async_redis_client = None
        self.memory_cache = {}  # Fallback cache
        self.connected = False
        
    def connect(self):
        """Establish Redis connection with fallback handling"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logger.info("✅ Redis connection established")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}, using memory cache")
            self.connected = False
            return False
    
    async def async_connect(self):
        """Establish async Redis connection"""
        try:
            self.async_redis_client = redis_async.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                decode_responses=True
            )
            # Test connection
            await self.async_redis_client.ping()
            self.connected = True
            logger.info("✅ Async Redis connection established")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Async Redis connection failed: {e}, using memory cache")
            self.connected = False
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis or memory cache"""
        if self.connected and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except:
                        return value
                return None
            except Exception as e:
                logger.warning(f"Redis get error: {e}, falling back to memory")
                self.connected = False
        
        # Fallback to memory cache
        return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Redis or memory cache"""
        if self.connected and self.redis_client:
            try:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return self.redis_client.set(key, serialized_value, ex=ex)
            except Exception as e:
                logger.warning(f"Redis set error: {e}, falling back to memory")
                self.connected = False
        
        # Fallback to memory cache
        self.memory_cache[key] = value
        # Simple TTL simulation for memory cache
        if ex:
            asyncio.create_task(self._expire_memory_key(key, ex))
        return True
    
    async def _expire_memory_key(self, key: str, seconds: int):
        """Simple TTL for memory cache"""
        await asyncio.sleep(seconds)
        self.memory_cache.pop(key, None)
    
    async def async_get(self, key: str) -> Optional[Any]:
        """Async get value from Redis or memory cache"""
        if self.connected and self.async_redis_client:
            try:
                value = await self.async_redis_client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except:
                        return value
                return None
            except Exception as e:
                logger.warning(f"Async Redis get error: {e}, falling back to memory")
                self.connected = False
        
        # Fallback to memory cache
        return self.memory_cache.get(key)
    
    async def async_set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Async set value in Redis or memory cache"""
        if self.connected and self.async_redis_client:
            try:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                return await self.async_redis_client.set(key, serialized_value, ex=ex)
            except Exception as e:
                logger.warning(f"Async Redis set error: {e}, falling back to memory")
                self.connected = False
        
        # Fallback to memory cache
        self.memory_cache[key] = value
        if ex:
            asyncio.create_task(self._expire_memory_key(key, ex))
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis or memory cache"""
        if self.connected and self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
                self.connected = False
        
        # Fallback to memory cache
        return bool(self.memory_cache.pop(key, None))
    
    async def async_delete(self, key: str) -> bool:
        """Async delete key from Redis or memory cache"""
        if self.connected and self.async_redis_client:
            try:
                return bool(await self.async_redis_client.delete(key))
            except Exception as e:
                logger.warning(f"Async Redis delete error: {e}")
                self.connected = False
        
        # Fallback to memory cache
        return bool(self.memory_cache.pop(key, None))
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if self.connected and self.redis_client:
            try:
                return bool(self.redis_client.exists(key))
            except Exception as e:
                logger.warning(f"Redis exists error: {e}")
                self.connected = False
        
        return key in self.memory_cache
    
    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        if self.connected and self.redis_client:
            try:
                return self.redis_client.keys(pattern)
            except Exception as e:
                logger.warning(f"Redis keys error: {e}")
                self.connected = False
        
        # Simple pattern matching for memory cache
        if pattern == "*":
            return list(self.memory_cache.keys())
        else:
            # Basic pattern matching (simplified)
            import fnmatch
            return [key for key in self.memory_cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    def flushdb(self) -> bool:
        """Flush database"""
        if self.connected and self.redis_client:
            try:
                return self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis flushdb error: {e}")
                self.connected = False
        
        # Clear memory cache
        self.memory_cache.clear()
        return True
    
    def close(self):
        """Close connections"""
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass
        
        if self.async_redis_client:
            try:
                asyncio.create_task(self.async_redis_client.close())
            except:
                pass
        
        self.connected = False
        logger.info("Redis connections closed")

# Global Redis connection manager instance
redis_manager = RedisConnectionManager()

def get_redis_manager() -> RedisConnectionManager:
    """Get the global Redis manager instance"""
    return redis_manager

# Convenience functions for direct use
def cache_get(key: str) -> Optional[Any]:
    """Get from cache"""
    return redis_manager.get(key)

def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set in cache"""
    return redis_manager.set(key, value, ex=ttl)

async def async_cache_get(key: str) -> Optional[Any]:
    """Async get from cache"""
    return await redis_manager.async_get(key)

async def async_cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Async set in cache"""
    return await redis_manager.async_set(key, value, ex=ttl)

def cache_delete(key: str) -> bool:
    """Delete from cache"""
    return redis_manager.delete(key)

def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments"""
    key_string = ":".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()

# Initialize connection on import
redis_manager.connect()
