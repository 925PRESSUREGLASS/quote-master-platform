"""
Cache Management API Router
Provides endpoints for cache monitoring, management, and statistics
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import structlog

from src.api.dependencies import get_current_active_user
from src.api.models.user import User
from src.services.cache.response_cache import cache_service, CacheStrategy, CacheTier
from src.services.cache.redis_connection import get_redis_manager

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/cache", tags=["cache-management"])

def require_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin user role"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/stats")
async def get_cache_statistics(
    endpoint: Optional[str] = Query(None, description="Filter stats by endpoint"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get cache performance statistics
    
    Returns hit rates, miss counts, error rates, and other cache metrics.
    """
    try:
        stats = await cache_service.get_cache_stats(endpoint)
        
        # Add additional metadata
        redis_manager = get_redis_manager()
        
        # Get Redis connection status
        redis_status = {
            "connected": redis_manager.connected,
            "host": redis_manager.host,
            "port": redis_manager.port,
            "db": redis_manager.db
        }
        
        # Get memory cache stats
        memory_cache_size = len(redis_manager.memory_cache) if redis_manager.memory_cache else 0
        
        return {
            "cache_stats": stats,
            "redis_status": redis_status,
            "memory_cache_size": memory_cache_size,
            "timestamp": datetime.now().isoformat(),
            "filter": {"endpoint": endpoint} if endpoint else None
        }
        
    except Exception as e:
        logger.error("Error getting cache statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )

@router.get("/health")
async def get_cache_health(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get cache system health status
    
    Returns the health status of Redis and memory cache systems.
    """
    try:
        redis_manager = get_redis_manager()
        
        # Test Redis connection
        redis_healthy = False
        redis_latency = None
        
        try:
            start_time = datetime.now()
            test_key = f"health_check:{int(start_time.timestamp())}"
            await redis_manager.async_set(test_key, "ping", ex=10)
            result = await redis_manager.async_get(test_key)
            await redis_manager.async_delete(test_key)
            
            end_time = datetime.now()
            redis_latency = (end_time - start_time).total_seconds() * 1000
            redis_healthy = result == "ping"
            
        except Exception as e:
            logger.warning("Redis health check failed", error=str(e))
        
        # Memory cache is always available
        memory_cache_healthy = True
        memory_cache_size = len(redis_manager.memory_cache) if redis_manager.memory_cache else 0
        
        health_status = {
            "overall_status": "healthy" if (redis_healthy or memory_cache_healthy) else "unhealthy",
            "redis": {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connected": redis_manager.connected,
                "latency_ms": round(redis_latency, 2) if redis_latency else None,
                "host": redis_manager.host,
                "port": redis_manager.port
            },
            "memory_cache": {
                "status": "healthy" if memory_cache_healthy else "unhealthy",
                "size": memory_cache_size
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Error checking cache health", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check cache health"
        )

@router.post("/invalidate")
async def invalidate_cache_entries(
    pattern: Optional[str] = Query(None, description="Pattern to match cache keys"),
    endpoint: Optional[str] = Query(None, description="Endpoint to invalidate"),
    user_id: Optional[str] = Query(None, description="User ID to invalidate"),
    current_user: User = Depends(require_admin_user)
):
    """
    Invalidate cache entries by pattern, endpoint, or user ID
    
    Admin only endpoint for cache management.
    """
    try:
        if not any([pattern, endpoint, user_id]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of pattern, endpoint, or user_id must be provided"
            )
        
        deleted_count = await cache_service.invalidate_cache(
            pattern=pattern,
            endpoint=endpoint,
            user_id=user_id
        )
        
        logger.info("Cache invalidation completed", 
                   deleted_count=deleted_count,
                   admin_user=current_user.email,
                   pattern=pattern,
                   endpoint=endpoint,
                   user_id=user_id)
        
        return {
            "message": "Cache invalidation completed",
            "deleted_count": deleted_count,
            "invalidated_by": current_user.email,
            "criteria": {
                "pattern": pattern,
                "endpoint": endpoint,
                "user_id": user_id
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error invalidating cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate cache entries"
        )

@router.post("/clear")
async def clear_all_cache(
    confirm: bool = Query(False, description="Confirmation required to clear all cache"),
    current_user: User = Depends(require_admin_user)
):
    """
    Clear all cache entries
    
    Admin only endpoint with confirmation required.
    WARNING: This will clear ALL cached data.
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required. Set confirm=true to proceed."
            )
        
        redis_manager = get_redis_manager()
        
        # Clear Redis database
        redis_cleared = False
        if redis_manager.connected:
            redis_cleared = redis_manager.flushdb()
        
        # Clear memory cache
        if redis_manager.memory_cache:
            redis_manager.memory_cache.clear()
        
        logger.warning("All cache cleared", 
                      admin_user=current_user.email,
                      redis_cleared=redis_cleared)
        
        return {
            "message": "All cache cleared successfully",
            "redis_cleared": redis_cleared,
            "memory_cache_cleared": True,
            "cleared_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error clearing cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@router.get("/keys")
async def list_cache_keys(
    pattern: str = Query("*", description="Pattern to match cache keys"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of keys to return"),
    current_user: User = Depends(require_admin_user)
):
    """
    List cache keys matching a pattern
    
    Admin only endpoint for cache inspection.
    """
    try:
        redis_manager = get_redis_manager()
        
        # Get keys matching pattern
        all_keys = redis_manager.keys(pattern)
        
        # Limit results
        keys = all_keys[:limit] if len(all_keys) > limit else all_keys
        
        # Get additional info for each key
        key_info = []
        for key in keys[:20]:  # Limit detailed info to 20 keys for performance
            try:
                # Check if key exists and get TTL if available
                exists = redis_manager.exists(key)
                if exists:
                    key_info.append({
                        "key": key,
                        "exists": True,
                        "type": "cached_response" if key.startswith("qmp:response:") else "other"
                    })
                else:
                    key_info.append({
                        "key": key,
                        "exists": False
                    })
            except Exception as e:
                key_info.append({
                    "key": key,
                    "error": str(e)
                })
        
        return {
            "pattern": pattern,
            "total_keys": len(all_keys),
            "returned_keys": len(keys),
            "keys": keys,
            "key_details": key_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error listing cache keys", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list cache keys"
        )

@router.get("/config")
async def get_cache_configuration(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current cache configuration
    """
    try:
        redis_manager = get_redis_manager()
        
        config = {
            "redis_config": {
                "host": redis_manager.host,
                "port": redis_manager.port,
                "db": redis_manager.db,
                "connected": redis_manager.connected
            },
            "cache_strategies": [strategy.value for strategy in CacheStrategy],
            "cache_tiers": [tier.value for tier in CacheTier],
            "ttl_config": cache_service.ttl_config,
            "strategy_config": {
                strategy.value: config 
                for strategy, config in cache_service.strategy_config.items()
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return config
        
    except Exception as e:
        logger.error("Error getting cache configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache configuration"
        )
