"""
Response Caching Middleware for FastAPI
Provides automatic response caching with configurable strategies
"""

import json
import time
from typing import Callable, Dict, Any, Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging

from src.services.cache.response_cache import cache_service, CacheStrategy, CacheTier

logger = logging.getLogger(__name__)

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic response caching"""
    
    def __init__(
        self,
        app,
        enabled: bool = True,
        default_strategy: CacheStrategy = CacheStrategy.SMART,
        default_tier: CacheTier = CacheTier.WARM,
        cacheable_methods: Optional[List[str]] = None,
        cacheable_status_codes: Optional[List[int]] = None,
        cache_control_header: bool = True
    ):
        super().__init__(app)
        self.enabled = enabled
        self.default_strategy = default_strategy
        self.default_tier = default_tier
        self.cacheable_methods = cacheable_methods or ["GET", "POST"]
        self.cacheable_status_codes = cacheable_status_codes or [200, 201]
        self.cache_control_header = cache_control_header
        
        # Configure endpoint-specific caching rules
        self.endpoint_config = {
            "/api/v1/quotes/generate": {
                "strategy": CacheStrategy.SMART,
                "tier": CacheTier.WARM,
                "ttl": 900,  # 15 minutes
                "cache_key_params": ["service_type", "property_type", "tone"]
            },
            "/api/v1/quotes/generate/enhanced": {
                "strategy": CacheStrategy.SMART,
                "tier": CacheTier.HOT,
                "ttl": 600,  # 10 minutes
                "cache_key_params": ["service_type", "property_type", "tone", "max_tokens"]
            },
            "/api/v1/quotes/search": {
                "strategy": CacheStrategy.AGGRESSIVE,
                "tier": CacheTier.WARM,
                "ttl": 1800,  # 30 minutes
                "cache_key_params": ["query", "category", "limit", "offset"]
            },
            "/api/v1/service-quotes": {
                "strategy": CacheStrategy.CONSERVATIVE,
                "tier": CacheTier.WARM,
                "ttl": 300,   # 5 minutes
                "cache_key_params": ["service_type", "location", "property_type"]
            },
            "/api/v1/analytics": {
                "strategy": CacheStrategy.AGGRESSIVE,
                "tier": CacheTier.COLD,
                "ttl": 3600,  # 1 hour
                "cache_key_params": ["metric", "period", "user_id"]
            }
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method"""
        
        # Skip caching if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip caching for non-cacheable methods
        if request.method not in self.cacheable_methods:
            return await call_next(request)
        
        # Get endpoint configuration
        endpoint = request.url.path
        config = self._get_endpoint_config(endpoint)
        
        # Skip caching if explicitly disabled for endpoint
        if config.get("strategy") == CacheStrategy.NONE:
            return await call_next(request)
        
        # Get user ID if available
        user_id = await self._extract_user_id(request)
        
        # Build cache parameters
        cache_params = await self._build_cache_params(request, config)
        
        # Try to get cached response
        start_time = time.time()
        cached_response = await cache_service.get_cached_response(
            endpoint, cache_params, user_id
        )
        
        if cached_response:
            # Return cached response
            cache_time = time.time() - start_time
            logger.info(f"Cache HIT for {endpoint}", extra={
                "cache_time_ms": round(cache_time * 1000, 2),
                "user_id": user_id
            })
            
            response = self._build_response_from_cache(cached_response)
            
            # Add cache headers
            if self.cache_control_header:
                self._add_cache_headers(response, cached_response, hit=True)
            
            return response
        
        # Cache miss - proceed with request
        cache_time = time.time() - start_time
        logger.debug(f"Cache MISS for {endpoint}", extra={
            "cache_time_ms": round(cache_time * 1000, 2),
            "user_id": user_id
        })
        
        # Process request
        response = await call_next(request)
        
        # Cache response if conditions are met
        if self._should_cache_response(response, config):
            await self._cache_response(
                endpoint, cache_params, response, user_id, config
            )
        
        # Add cache headers
        if self.cache_control_header:
            self._add_cache_headers(response, None, hit=False)
        
        return response
    
    def _get_endpoint_config(self, endpoint: str) -> Dict[str, Any]:
        """Get configuration for specific endpoint"""
        # Try exact match first
        if endpoint in self.endpoint_config:
            return self.endpoint_config[endpoint]
        
        # Try pattern matching
        for pattern, config in self.endpoint_config.items():
            if endpoint.startswith(pattern.rstrip("*")):
                return config
        
        # Return default configuration
        return {
            "strategy": self.default_strategy,
            "tier": self.default_tier,
            "ttl": None,
            "cache_key_params": []
        }
    
    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (from JWT token, session, etc.)"""
        try:
            # Try to get from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # In a real implementation, you would decode the JWT token
                # For now, we'll use a simple approach
                return "user_from_token"
            
            # Try to get from request state (set by auth middleware)
            if hasattr(request.state, "current_user") and request.state.current_user:
                return str(request.state.current_user.id)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting user ID: {e}")
            return None
    
    async def _build_cache_params(self, request: Request, config: Dict[str, Any]) -> Dict[str, Any]:
        """Build cache parameters from request"""
        params = {}
        
        # Get query parameters
        for key, value in request.query_params.items():
            if not config.get("cache_key_params") or key in config["cache_key_params"]:
                params[f"query.{key}"] = value
        
        # Get request body for POST requests
        if request.method == "POST":
            try:
                body = await request.body()
                if body:
                    body_json = json.loads(body.decode())
                    
                    # Filter body parameters based on config
                    if config.get("cache_key_params"):
                        for param in config["cache_key_params"]:
                            if param in body_json:
                                params[f"body.{param}"] = body_json[param]
                    else:
                        # Include all non-sensitive body parameters
                        for key, value in body_json.items():
                            if not self._is_sensitive_param(key):
                                params[f"body.{key}"] = value
                                
            except Exception as e:
                logger.warning(f"Error parsing request body for caching: {e}")
        
        # Add request method
        params["method"] = request.method
        
        return params
    
    def _is_sensitive_param(self, param_name: str) -> bool:
        """Check if parameter contains sensitive data"""
        sensitive_params = {
            "password", "token", "secret", "key", "auth", "credential",
            "ssn", "social_security", "credit_card", "payment", "billing"
        }
        param_lower = param_name.lower()
        return any(sensitive in param_lower for sensitive in sensitive_params)
    
    def _should_cache_response(self, response: Response, config: Dict[str, Any]) -> bool:
        """Determine if response should be cached"""
        # Check status code
        if response.status_code not in self.cacheable_status_codes:
            return False
        
        # Check cache strategy
        if config.get("strategy") == CacheStrategy.NONE:
            return False
        
        # Check response headers for cache control
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    async def _cache_response(
        self, 
        endpoint: str, 
        params: Dict[str, Any], 
        response: Response, 
        user_id: Optional[str],
        config: Dict[str, Any]
    ):
        """Cache the response"""
        try:
            # Extract response data
            response_data = await self._extract_response_data(response)
            
            if response_data is not None:
                await cache_service.cache_response(
                    endpoint=endpoint,
                    params=params,
                    response_data=response_data,
                    user_id=user_id,
                    ttl=config.get("ttl"),
                    strategy=config.get("strategy", self.default_strategy),
                    tier=config.get("tier", self.default_tier)
                )
                
        except Exception as e:
            logger.warning(f"Error caching response for {endpoint}: {e}")
    
    async def _extract_response_data(self, response: Response) -> Optional[Dict[str, Any]]:
        """Extract data from response for caching"""
        try:
            if hasattr(response, 'body') and response.body:
                body = response.body
                if isinstance(body, bytes):
                    body_str = body.decode('utf-8')
                    return {
                        "body": json.loads(body_str),
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
            return None
        except Exception as e:
            logger.warning(f"Error extracting response data: {e}")
            return None
    
    def _build_response_from_cache(self, cached_data: Dict[str, Any]) -> Response:
        """Build response from cached data"""
        try:
            if "_cache_hit" in cached_data:
                # Remove cache metadata
                response_data = {k: v for k, v in cached_data.items() 
                               if not k.startswith("_cache")}
            else:
                response_data = cached_data
            
            # If cached data has body, use it; otherwise use the data directly
            if "body" in response_data and "status_code" in response_data:
                return JSONResponse(
                    content=response_data["body"],
                    status_code=response_data["status_code"],
                    headers=response_data.get("headers", {})
                )
            else:
                return JSONResponse(content=response_data)
                
        except Exception as e:
            logger.error(f"Error building response from cache: {e}")
            # Return a generic error response
            return JSONResponse(
                content={"error": "Cache error", "message": str(e)},
                status_code=500
            )
    
    def _add_cache_headers(self, response: Response, cached_data: Optional[Dict[str, Any]], hit: bool):
        """Add cache-related headers to response"""
        try:
            if hit:
                response.headers["X-Cache"] = "HIT"
                if cached_data and "_cached_at" in cached_data:
                    response.headers["X-Cache-Date"] = cached_data["_cached_at"]
            else:
                response.headers["X-Cache"] = "MISS"
            
            response.headers["X-Cache-Service"] = "QuoteMasterPro-Redis"
            
        except Exception as e:
            logger.warning(f"Error adding cache headers: {e}")

# Cache middleware configuration for different environments
def get_cache_middleware_config(environment: str = "production") -> Dict[str, Any]:
    """Get cache middleware configuration based on environment"""
    
    configs = {
        "development": {
            "enabled": True,
            "default_strategy": CacheStrategy.CONSERVATIVE,
            "default_tier": CacheTier.HOT,
            "cache_control_header": True
        },
        "staging": {
            "enabled": True,
            "default_strategy": CacheStrategy.SMART,
            "default_tier": CacheTier.WARM,
            "cache_control_header": True
        },
        "production": {
            "enabled": True,
            "default_strategy": CacheStrategy.SMART,
            "default_tier": CacheTier.WARM,
            "cache_control_header": True
        }
    }
    
    return configs.get(environment, configs["production"])
