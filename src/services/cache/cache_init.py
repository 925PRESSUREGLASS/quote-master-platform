"""Cache initialization with Redis fallback to memory cache."""

import logging
from typing import Optional

import redis
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from src.core.config import get_settings

from .memory_cache import MemoryCache
from .response_cache import CacheInterface

logger = logging.getLogger(__name__)
settings = get_settings()

# Global cache instance
_cache_instance: Optional[CacheInterface] = None


class RedisCacheWithFallback(CacheInterface):
    """Redis cache with memory cache fallback."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache = MemoryCache()
        self._redis_available = False
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection with fallback."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test connection
            self.redis_client.ping()
            self._redis_available = True
            logger.info("Redis cache initialized successfully")
        except (ConnectionError, TimeoutError, ResponseError, Exception) as e:
            logger.warning(f"Redis unavailable, using memory cache fallback: {e}")
            self.redis_client = None
            self._redis_available = False

    def _check_redis_health(self) -> bool:
        """Check if Redis is available."""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            if not self._redis_available:
                logger.info("Redis connection restored")
                self._redis_available = True
            return True
        except (ConnectionError, TimeoutError, ResponseError):
            if self._redis_available:
                logger.warning("Redis connection lost, falling back to memory cache")
                self._redis_available = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if self._check_redis_health():
            try:
                return self.redis_client.get(key)
            except (ConnectionError, TimeoutError, ResponseError):
                self._redis_available = False

        # Fallback to memory cache
        return await self.memory_cache.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        success = False

        # Try Redis first
        if self._check_redis_health():
            try:
                if ttl:
                    self.redis_client.setex(key, ttl, value)
                else:
                    self.redis_client.set(key, value)
                success = True
            except (ConnectionError, TimeoutError, ResponseError):
                self._redis_available = False

        # Always store in memory cache as backup
        await self.memory_cache.set(key, value, ttl)
        return success

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        success = False

        if self._check_redis_health():
            try:
                self.redis_client.delete(key)
                success = True
            except (ConnectionError, TimeoutError, ResponseError):
                self._redis_available = False

        # Delete from memory cache
        await self.memory_cache.delete(key)
        return success

    async def clear(self) -> bool:
        """Clear all cache."""
        success = False

        if self._check_redis_health():
            try:
                self.redis_client.flushdb()
                success = True
            except (ConnectionError, TimeoutError, ResponseError):
                self._redis_available = False

        # Clear memory cache
        await self.memory_cache.clear()
        return success

    def is_redis_available(self) -> bool:
        """Check if Redis is currently available."""
        return self._redis_available


async def get_cache() -> CacheInterface:
    """Get cache instance (singleton)."""
    global _cache_instance
    if _cache_instance is None:
        if settings.enable_caching:
            _cache_instance = RedisCacheWithFallback()
        else:
            _cache_instance = MemoryCache()
    return _cache_instance


async def init_cache() -> CacheInterface:
    """Initialize cache system."""
    cache = await get_cache()
    logger.info(f"Cache system initialized: {type(cache).__name__}")
    return cache
