"""
Response optimization and caching service for Quote Master Pro.
Implements intelligent caching strategies for API responses and database queries.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

import redis.asyncio as redis

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheStrategy(str, Enum):
    """Cache strategy types"""

    NO_CACHE = "no_cache"
    SHORT_TERM = "short_term"  # 5 minutes
    MEDIUM_TERM = "medium_term"  # 1 hour
    LONG_TERM = "long_term"  # 24 hours
    PERMANENT = "permanent"  # 7 days


@dataclass
class CacheConfig:
    """Cache configuration for different data types"""

    ttl: int  # Time to live in seconds
    strategy: CacheStrategy
    compress: bool = False
    invalidate_on: List[str] = None  # Events that should invalidate this cache


class ResponseOptimizer:
    """
    Advanced caching and response optimization service.
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_configs = self._initialize_cache_configs()
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "errors": 0}

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL, decode_responses=True, encoding="utf-8"
                )
                await self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed, using memory cache: {e}")
            self.redis_client = None

    def _initialize_cache_configs(self) -> Dict[str, CacheConfig]:
        """Initialize cache configurations for different data types"""
        return {
            # Quote-related caching
            "quote_pricing": CacheConfig(
                ttl=300,  # 5 minutes
                strategy=CacheStrategy.SHORT_TERM,
                invalidate_on=["pricing_update"],
            ),
            "quote_details": CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.MEDIUM_TERM,
                invalidate_on=["quote_update"],
            ),
            "suburb_data": CacheConfig(
                ttl=86400,  # 24 hours
                strategy=CacheStrategy.LONG_TERM,
                invalidate_on=["suburb_update"],
            ),
            "service_types": CacheConfig(
                ttl=86400,  # 24 hours
                strategy=CacheStrategy.LONG_TERM,
                invalidate_on=["service_update"],
            ),
            "ai_responses": CacheConfig(
                ttl=3600, strategy=CacheStrategy.MEDIUM_TERM, compress=True  # 1 hour
            ),
            "user_quotes_list": CacheConfig(
                ttl=300,  # 5 minutes
                strategy=CacheStrategy.SHORT_TERM,
                invalidate_on=["user_quote_update"],
            ),
            "analytics_data": CacheConfig(
                ttl=1800,  # 30 minutes
                strategy=CacheStrategy.MEDIUM_TERM,
                invalidate_on=["analytics_update"],
            ),
        }

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        # Sort parameters for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True)

        # Create hash for long parameter strings
        params_hash = hashlib.md5(params_str.encode()).hexdigest()

        return f"qmp:{prefix}:{params_hash}"

    async def get(self, cache_type: str, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_cache_key(cache_type, **kwargs)

        try:
            # Try Redis first
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached_data)

            # Fallback to memory cache
            if cache_key in self.memory_cache:
                data, expiry = self.memory_cache[cache_key]
                if time.time() < expiry:
                    self.cache_stats["hits"] += 1
                    return data
                else:
                    # Expired, remove from memory cache
                    del self.memory_cache[cache_key]

            self.cache_stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(self, cache_type: str, value: Any, **kwargs):
        """Set value in cache"""
        if cache_type not in self.cache_configs:
            logger.warning(f"Unknown cache type: {cache_type}")
            return

        config = self.cache_configs[cache_type]
        cache_key = self._generate_cache_key(cache_type, **kwargs)

        try:
            # Serialize data
            serialized_data = json.dumps(value, default=str)

            # Store in Redis if available
            if self.redis_client:
                await self.redis_client.setex(cache_key, config.ttl, serialized_data)

            # Store in memory cache as fallback
            expiry = time.time() + config.ttl
            self.memory_cache[cache_key] = (value, expiry)

            # Clean up expired memory cache entries periodically
            if len(self.memory_cache) > 1000:
                await self._cleanup_memory_cache()

            self.cache_stats["sets"] += 1

        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            self.cache_stats["errors"] += 1

    async def invalidate(self, cache_type: str, **kwargs):
        """Invalidate specific cache entry"""
        cache_key = self._generate_cache_key(cache_type, **kwargs)

        try:
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(cache_key)

            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]

        except Exception as e:
            logger.error(f"Cache invalidation error for key {cache_key}: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            # Redis pattern invalidation
            if self.redis_client:
                keys = await self.redis_client.keys(f"qmp:{pattern}:*")
                if keys:
                    await self.redis_client.delete(*keys)

            # Memory cache pattern invalidation
            keys_to_remove = [
                key
                for key in self.memory_cache.keys()
                if key.startswith(f"qmp:{pattern}:")
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]

        except Exception as e:
            logger.error(f"Pattern invalidation error for {pattern}: {e}")

    async def clear_all(self):
        """Clear all cache entries"""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys("qmp:*")
                if keys:
                    await self.redis_client.delete(*keys)

            self.memory_cache.clear()
            logger.info("All cache entries cleared")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    async def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, expiry) in self.memory_cache.items()
            if current_time >= expiry
        ]

        for key in expired_keys:
            del self.memory_cache[key]

        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (
            (self.cache_stats["hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "sets": self.cache_stats["sets"],
            "errors": self.cache_stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "redis_available": self.redis_client is not None,
        }


# Global instance
_response_optimizer = None


async def get_response_optimizer() -> ResponseOptimizer:
    """Get global response optimizer instance"""
    global _response_optimizer
    if _response_optimizer is None:
        _response_optimizer = ResponseOptimizer()
        await _response_optimizer.initialize()
    return _response_optimizer


def cached_response(cache_type: str, **cache_kwargs):
    """
    Decorator for caching function responses.

    Usage:
    @cached_response("quote_pricing", service_type="window_cleaning")
    async def calculate_quote_price(service_type, area, suburb):
        # expensive calculation
        return price
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = await get_response_optimizer()

            # Create cache key from function arguments
            cache_params = dict(cache_kwargs)
            cache_params.update(kwargs)

            # Try to get from cache first
            cached_result = await optimizer.get(cache_type, **cache_params)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await optimizer.set(cache_type, result, **cache_params)

            return result

        return wrapper

    return decorator


class QuoteResponseOptimizer:
    """
    Specialized optimizer for quote-related responses.
    """

    @staticmethod
    async def cache_pricing_calculation(
        service_type: str,
        area_sqm: float,
        suburb: str,
        difficulty: float,
        result: Dict[str, Any],
    ):
        """Cache pricing calculation result"""
        optimizer = await get_response_optimizer()
        await optimizer.set(
            "quote_pricing",
            result,
            service_type=service_type,
            area_sqm=area_sqm,
            suburb=suburb,
            difficulty=difficulty,
        )

    @staticmethod
    async def get_cached_pricing(
        service_type: str, area_sqm: float, suburb: str, difficulty: float
    ) -> Optional[Dict[str, Any]]:
        """Get cached pricing calculation"""
        optimizer = await get_response_optimizer()
        return await optimizer.get(
            "quote_pricing",
            service_type=service_type,
            area_sqm=area_sqm,
            suburb=suburb,
            difficulty=difficulty,
        )

    @staticmethod
    async def cache_ai_response(
        prompt_hash: str, provider: str, response: Dict[str, Any]
    ):
        """Cache AI service response"""
        optimizer = await get_response_optimizer()
        await optimizer.set(
            "ai_responses", response, prompt_hash=prompt_hash, provider=provider
        )

    @staticmethod
    async def get_cached_ai_response(
        prompt_hash: str, provider: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        optimizer = await get_response_optimizer()
        return await optimizer.get(
            "ai_responses", prompt_hash=prompt_hash, provider=provider
        )

    @staticmethod
    async def invalidate_user_quotes(user_id: int):
        """Invalidate user-specific quote caches"""
        optimizer = await get_response_optimizer()
        await optimizer.invalidate_pattern(f"user_quotes_{user_id}")

    @staticmethod
    async def cache_suburb_list(suburbs: List[Dict[str, Any]]):
        """Cache Perth suburbs list"""
        optimizer = await get_response_optimizer()
        await optimizer.set("suburb_data", suburbs)

    @staticmethod
    async def get_cached_suburb_list() -> Optional[List[Dict[str, Any]]]:
        """Get cached suburbs list"""
        optimizer = await get_response_optimizer()
        return await optimizer.get("suburb_data")


class DatabaseQueryOptimizer:
    """
    Database query optimization and caching.
    """

    @staticmethod
    async def cache_query_result(query_type: str, result: Any, **query_params):
        """Cache database query result"""
        optimizer = await get_response_optimizer()
        cache_key = f"db_{query_type}"
        await optimizer.set(cache_key, result, **query_params)

    @staticmethod
    async def get_cached_query_result(query_type: str, **query_params) -> Optional[Any]:
        """Get cached database query result"""
        optimizer = await get_response_optimizer()
        cache_key = f"db_{query_type}"
        return await optimizer.get(cache_key, **query_params)

    @staticmethod
    async def invalidate_table_cache(table_name: str):
        """Invalidate all cache entries for a specific table"""
        optimizer = await get_response_optimizer()
        await optimizer.invalidate_pattern(f"db_*_{table_name}")


# Utility functions
async def warm_cache():
    """Pre-populate cache with commonly used data"""
    try:
        # This would typically load frequently accessed data
        # like suburb lists, service types, etc.
        logger.info("Cache warming initiated")

        # Example: Pre-load suburb data
        # suburbs = await get_all_suburbs()
        # await QuoteResponseOptimizer.cache_suburb_list(suburbs)

    except Exception as e:
        logger.error(f"Cache warming error: {e}")


async def cache_health_check() -> Dict[str, Any]:
    """Check cache system health"""
    optimizer = await get_response_optimizer()
    stats = optimizer.get_stats()

    health_status = {
        "status": "healthy" if stats["errors"] < 10 else "degraded",
        "redis_available": stats["redis_available"],
        "cache_stats": stats,
        "timestamp": datetime.now().isoformat(),
    }

    return health_status
