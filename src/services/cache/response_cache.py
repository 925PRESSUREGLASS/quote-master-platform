"""
Enhanced Redis Cache Service for Quote Master Pro
Provides intelligent response caching with configurable TTL and cache strategies
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from enum import Enum
import logging
import asyncio

from src.services.cache.redis_connection import get_redis_manager, generate_cache_key
from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheStrategy(Enum):
    """Cache strategy types for different content"""
    AGGRESSIVE = "aggressive"    # Long TTL, cache everything
    CONSERVATIVE = "conservative"  # Short TTL, selective caching
    SMART = "smart"              # Dynamic TTL based on content type
    NONE = "none"                # No caching

class CacheTier(Enum):
    """Cache tiers for different data importance"""
    HOT = "hot"        # Frequently accessed, short TTL
    WARM = "warm"      # Moderately accessed, medium TTL  
    COLD = "cold"      # Rarely accessed, long TTL

class ResponseCacheService:
    """Enhanced response caching service with intelligent strategies"""
    
    def __init__(self):
        self.redis_manager = get_redis_manager()
        self.cache_prefix = "qmp:response:"
        self.stats_prefix = "qmp:cache_stats:"
        
        # Cache TTL configurations (in seconds)
        self.ttl_config = {
            CacheTier.HOT: 300,      # 5 minutes
            CacheTier.WARM: 1800,    # 30 minutes  
            CacheTier.COLD: 3600     # 1 hour
        }
        
        # Cache strategies configuration
        self.strategy_config = {
            CacheStrategy.AGGRESSIVE: {
                "default_ttl": 3600,
                "quote_generation": 1800,
                "user_preferences": 7200,
                "system_config": 14400
            },
            CacheStrategy.CONSERVATIVE: {
                "default_ttl": 300,
                "quote_generation": 600,
                "user_preferences": 1800,
                "system_config": 3600
            },
            CacheStrategy.SMART: {
                "default_ttl": 1800,
                "quote_generation": 900,
                "user_preferences": 3600,
                "system_config": 7200
            }
        }
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """Generate a cache key for endpoint and parameters"""
        key_components = [endpoint]
        
        if user_id:
            key_components.append(f"user:{user_id}")
        
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items()) if params else []
        param_string = json.dumps(sorted_params, sort_keys=True, default=str)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        key_components.append(param_hash)
        
        return self.cache_prefix + ":".join(key_components)
    
    def _get_ttl_for_content(self, content_type: str, strategy: CacheStrategy = CacheStrategy.SMART) -> int:
        """Get TTL based on content type and strategy"""
        if strategy == CacheStrategy.NONE:
            return 0
        
        config = self.strategy_config.get(strategy, self.strategy_config[CacheStrategy.SMART])
        return config.get(content_type, config["default_ttl"])
    
    def _should_cache(self, endpoint: str, response_data: Any, user_tier: str = "standard") -> bool:
        """Determine if response should be cached based on various factors"""
        
        # Don't cache error responses
        if isinstance(response_data, dict) and response_data.get("error"):
            return False
        
        # Don't cache user-specific sensitive data
        sensitive_endpoints = ["auth", "payment", "personal"]
        if any(sensitive in endpoint.lower() for sensitive in sensitive_endpoints):
            return False
        
        # Don't cache real-time data
        realtime_endpoints = ["live", "status", "health"]
        if any(realtime in endpoint.lower() for realtime in realtime_endpoints):
            return False
        
        return True
    
    async def get_cached_response(
        self, 
        endpoint: str, 
        params: Dict[str, Any], 
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        try:
            cache_key = self._get_cache_key(endpoint, params, user_id)
            
            # Get from Redis
            cached_data = await self.redis_manager.async_get(cache_key)
            
            if cached_data:
                # Update cache hit statistics
                await self._update_cache_stats("hits", endpoint)
                
                # Check if cached data has metadata
                if isinstance(cached_data, dict) and "_cache_meta" in cached_data:
                    cache_meta = cached_data["_cache_meta"]
                    
                    # Check if cache is still valid (additional freshness check)
                    created_at = datetime.fromisoformat(cache_meta["created_at"])
                    max_age = cache_meta.get("max_age", 3600)
                    
                    if (datetime.now() - created_at).total_seconds() > max_age:
                        # Cache expired, remove it
                        await self.redis_manager.async_delete(cache_key)
                        await self._update_cache_stats("expired", endpoint)
                        return None
                    
                    # Return cached response without metadata
                    response_data = {k: v for k, v in cached_data.items() if k != "_cache_meta"}
                    
                    # Add cache hit header info
                    response_data["_cache_hit"] = True
                    response_data["_cached_at"] = cache_meta["created_at"]
                    
                    logger.info(f"Cache HIT for {endpoint}", extra={"cache_key": cache_key})
                    return response_data
                
                return cached_data
            
            # Update cache miss statistics
            await self._update_cache_stats("misses", endpoint)
            logger.debug(f"Cache MISS for {endpoint}", extra={"cache_key": cache_key})
            return None
            
        except Exception as e:
            logger.warning(f"Cache get error for {endpoint}: {e}")
            await self._update_cache_stats("errors", endpoint)
            return None
    
    async def cache_response(
        self,
        endpoint: str,
        params: Dict[str, Any],
        response_data: Any,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.SMART,
        tier: CacheTier = CacheTier.WARM
    ) -> bool:
        """Cache response data with intelligent TTL and metadata"""
        try:
            # Check if we should cache this response
            if not self._should_cache(endpoint, response_data):
                logger.debug(f"Skipping cache for {endpoint} (policy)")
                return False
            
            cache_key = self._get_cache_key(endpoint, params, user_id)
            
            # Determine TTL
            if ttl is None:
                # Determine content type from endpoint
                content_type = "default_ttl"
                if "quote" in endpoint.lower():
                    content_type = "quote_generation"
                elif "user" in endpoint.lower():
                    content_type = "user_preferences"
                elif "config" in endpoint.lower() or "setting" in endpoint.lower():
                    content_type = "system_config"
                
                ttl = self._get_ttl_for_content(content_type, strategy)
            
            # Don't cache if TTL is 0
            if ttl <= 0:
                return False
            
            # Prepare cache data with metadata
            cache_data = response_data.copy() if isinstance(response_data, dict) else {"data": response_data}
            
            cache_data["_cache_meta"] = {
                "created_at": datetime.now().isoformat(),
                "ttl": ttl,
                "max_age": ttl,
                "endpoint": endpoint,
                "strategy": strategy.value,
                "tier": tier.value,
                "version": "1.0"
            }
            
            # Store in Redis
            success = await self.redis_manager.async_set(cache_key, cache_data, ex=ttl)
            
            if success:
                await self._update_cache_stats("sets", endpoint)
                logger.info(f"Cached response for {endpoint}", extra={
                    "cache_key": cache_key, 
                    "ttl": ttl,
                    "strategy": strategy.value
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error for {endpoint}: {e}")
            await self._update_cache_stats("errors", endpoint)
            return False
    
    async def invalidate_cache(
        self,
        pattern: Optional[str] = None,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> int:
        """Invalidate cached responses by pattern, endpoint, or user"""
        try:
            if pattern:
                # Use pattern directly
                cache_pattern = f"{self.cache_prefix}{pattern}"
            elif endpoint:
                # Build pattern for endpoint
                if user_id:
                    cache_pattern = f"{self.cache_prefix}{endpoint}:user:{user_id}:*"
                else:
                    cache_pattern = f"{self.cache_prefix}{endpoint}:*"
            else:
                # Default pattern for all caches
                cache_pattern = f"{self.cache_prefix}*"
            
            # Get matching keys
            keys = self.redis_manager.keys(cache_pattern)
            
            if keys:
                # Delete keys
                deleted_count = 0
                for key in keys:
                    if await self.redis_manager.async_delete(key):
                        deleted_count += 1
                
                await self._update_cache_stats("invalidations", f"pattern:{cache_pattern}")
                logger.info(f"Invalidated {deleted_count} cache entries", extra={
                    "pattern": cache_pattern,
                    "deleted_count": deleted_count
                })
                
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    async def _update_cache_stats(self, metric: str, endpoint: str):
        """Update cache statistics"""
        try:
            stats_key = f"{self.stats_prefix}{metric}:{endpoint}"
            current_count = await self.redis_manager.async_get(stats_key) or 0
            await self.redis_manager.async_set(
                stats_key, 
                int(current_count) + 1, 
                ex=86400  # Keep stats for 24 hours
            )
            
            # Update daily totals
            daily_key = f"{self.stats_prefix}daily:{datetime.now().strftime('%Y-%m-%d')}:{metric}"
            daily_count = await self.redis_manager.async_get(daily_key) or 0
            await self.redis_manager.async_set(
                daily_key,
                int(daily_count) + 1,
                ex=86400 * 7  # Keep daily stats for a week
            )
            
        except Exception as e:
            logger.warning(f"Cache stats update error: {e}")
    
    async def get_cache_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = {}
            
            if endpoint:
                # Get stats for specific endpoint
                patterns = [f"{self.stats_prefix}*:{endpoint}"]
            else:
                # Get all stats
                patterns = [f"{self.stats_prefix}*"]
            
            for pattern in patterns:
                keys = self.redis_manager.keys(pattern)
                for key in keys:
                    value = await self.redis_manager.async_get(key) or 0
                    # Extract metric and endpoint from key
                    key_parts = key.replace(self.stats_prefix, "").split(":")
                    metric = key_parts[0]
                    if metric not in stats:
                        stats[metric] = {}
                    
                    if len(key_parts) > 1:
                        endpoint_name = ":".join(key_parts[1:])
                        stats[metric][endpoint_name] = int(value)
                    else:
                        stats[metric]["total"] = int(value)
            
            # Calculate hit rate if we have hits and misses
            if "hits" in stats and "misses" in stats:
                for endpoint_name in stats["hits"]:
                    if endpoint_name in stats["misses"]:
                        hits = stats["hits"][endpoint_name]
                        misses = stats["misses"][endpoint_name]
                        total_requests = hits + misses
                        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
                        
                        if "hit_rates" not in stats:
                            stats["hit_rates"] = {}
                        stats["hit_rates"][endpoint_name] = round(hit_rate, 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global cache service instance
cache_service = ResponseCacheService()

# Convenience functions
async def get_cached_response(endpoint: str, params: Dict[str, Any], user_id: Optional[str] = None):
    """Get cached response"""
    return await cache_service.get_cached_response(endpoint, params, user_id)

async def cache_response(endpoint: str, params: Dict[str, Any], response_data: Any, 
                        user_id: Optional[str] = None, ttl: Optional[int] = None):
    """Cache response"""
    return await cache_service.cache_response(endpoint, params, response_data, user_id, ttl)

async def invalidate_cache(pattern: Optional[str] = None, endpoint: Optional[str] = None, 
                          user_id: Optional[str] = None):
    """Invalidate cache"""
    return await cache_service.invalidate_cache(pattern, endpoint, user_id)

async def get_cache_stats(endpoint: Optional[str] = None):
    """Get cache stats"""
    return await cache_service.get_cache_stats(endpoint)
