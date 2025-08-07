"""
Enhanced Quote Management Router with Advanced AI Integration
Integrates OpenTelemetry tracing, circuit breakers, and smart routing.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import structlog

from src.core.database import get_db
from src.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user,
    check_quote_quota
)
from src.api.models.user import User
from src.api.models.quote import Quote, QuoteCategory, QuoteFavorite, QuoteStatus
from src.api.schemas.quote import (
    QuoteCreate, QuoteUpdate, QuoteResponse, QuoteGenerate, 
    QuoteSearchRequest, QuoteSearchResponse
)

# Enhanced AI Service imports
from src.services.ai.enhanced_ai_service import get_ai_service, AIRequest, ServiceCategory
from src.services.ai.monitoring.tracing import trace_ai_operation, add_trace_attributes
from src.services.ai.monitoring.smart_routing import RoutingStrategy

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])

@router.post("/generate/enhanced", response_model=QuoteResponse)
async def generate_enhanced_quote(
    quote_request: QuoteGenerate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate a quote using the enhanced AI service with comprehensive monitoring.
    
    This endpoint provides:
    - Intelligent provider selection and load balancing
    - Circuit breaker protection and automatic failover
    - Comprehensive OpenTelemetry tracing
    - Performance metrics and cost tracking
    - Smart caching and quality scoring
    """
    
    with trace_ai_operation(
        "enhanced_quote_generation",
        "api",
        "generation",
        {
            "user.id": str(current_user.id),
            "user.email": current_user.email,
            "quote.service_type": quote_request.service_type,
            "quote.property_type": getattr(quote_request, 'property_type', None),
            "request.client_ip": request.client.host,
            "request.user_agent": request.headers.get("user-agent", "")[:100]
        }
    ) as span:
        
        try:
            # Check user quota
            await check_quote_quota(current_user, db)
            
            # Get enhanced AI service
            ai_service = await get_ai_service()
            
            # Map service type to category
            service_category = _map_service_type_to_category(quote_request.service_type)
            
            # Prepare AI request with enhanced options
            ai_request = AIRequest(
                prompt=_build_enhanced_prompt(quote_request),
                context=_build_context_from_request(quote_request),
                category=service_category,
                tone=getattr(quote_request, 'tone', 'professional'),
                max_tokens=getattr(quote_request, 'max_tokens', 800),
                temperature=getattr(quote_request, 'temperature', 0.7),
                user_id=str(current_user.id),
                session_id=request.headers.get("X-Session-ID"),
                preferred_provider=getattr(quote_request, 'preferred_ai_provider', None),
                routing_strategy=_get_routing_strategy(quote_request, current_user)
            )
            
            span.set_attribute("ai_request.routing_strategy", 
                             ai_request.routing_strategy.value if ai_request.routing_strategy else "default")
            
            # Generate quote with enhanced AI service
            ai_response = await ai_service.generate_quote(ai_request)
            
            # Add AI response metrics to tracing
            span.set_attribute("ai_response.provider", ai_response.provider.value)
            span.set_attribute("ai_response.model", ai_response.model)
            span.set_attribute("ai_response.tokens_used", ai_response.tokens_used)
            span.set_attribute("ai_response.cost", ai_response.cost)
            span.set_attribute("ai_response.quality_score", ai_response.quality_score)
            span.set_attribute("ai_response.response_time", ai_response.response_time)
            span.set_attribute("ai_response.cached", ai_response.cached)
            
            # Save quote to database
            db_quote = Quote(
                user_id=current_user.id,
                service_type=quote_request.service_type,
                property_type=getattr(quote_request, 'property_type', None),
                quote_text=ai_response.text,
                ai_provider=ai_response.provider.value,
                ai_model=ai_response.model,
                tokens_used=ai_response.tokens_used,
                generation_cost=ai_response.cost,
                quality_score=ai_response.quality_score,
                response_time_ms=ai_response.response_time * 1000,
                request_id=ai_response.request_id,
                trace_id=request.headers.get("traceparent", "").split("-")[1] if request.headers.get("traceparent") else None,
                cached_response=ai_response.cached,
                routing_metadata=ai_response.routing_metadata or {},
                status=QuoteStatus.ACTIVE
            )
            
            db.add(db_quote)
            db.commit()
            db.refresh(db_quote)
            
            # Schedule background tasks
            background_tasks.add_task(
                _post_generation_analytics,
                db_quote.id,
                ai_response,
                current_user.id
            )
            
            # Prepare response
            response = QuoteResponse(
                id=db_quote.id,
                service_type=db_quote.service_type,
                property_type=db_quote.property_type,
                quote_text=db_quote.quote_text,
                status=db_quote.status,
                created_at=db_quote.created_at,
                updated_at=db_quote.updated_at,
                # Enhanced metadata
                ai_metadata={
                    "provider": ai_response.provider.value,
                    "model": ai_response.model,
                    "tokens_used": ai_response.tokens_used,
                    "cost": ai_response.cost,
                    "quality_score": ai_response.quality_score,
                    "response_time": ai_response.response_time,
                    "cached": ai_response.cached,
                    "routing_strategy": ai_request.routing_strategy.value if ai_request.routing_strategy else None
                }
            )
            
            logger.info(
                "Enhanced quote generated successfully",
                quote_id=db_quote.id,
                user_id=current_user.id,
                provider=ai_response.provider.value,
                tokens=ai_response.tokens_used,
                cost=ai_response.cost,
                quality=ai_response.quality_score,
                cached=ai_response.cached
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Enhanced quote generation failed",
                user_id=current_user.id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            span.set_status("ERROR")
            span.record_exception(e)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate quote: {str(e)}"
            )

@router.get("/ai-service/health", response_model=Dict[str, Any])
async def get_ai_service_health(
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive health status of the AI service infrastructure."""
    
    try:
        ai_service = await get_ai_service()
        health_status = await ai_service.get_health_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "ai_service": health_status,
            "user_access": {
                "user_id": current_user.id,
                "access_level": "full" if current_user.is_active else "limited"
            }
        }
        
    except Exception as e:
        logger.error("AI service health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/ai-service/circuit-breaker/reset/{provider}")
async def reset_circuit_breaker(
    provider: str,
    current_user: User = Depends(get_current_active_user)  # Admin only in production
):
    """Manually reset a circuit breaker for a specific AI provider."""
    
    try:
        ai_service = await get_ai_service()
        
        from src.services.ai.monitoring.circuit_breaker import circuit_breaker_manager
        success = await circuit_breaker_manager.reset_circuit_breaker(provider)
        
        if success:
            logger.info(f"Circuit breaker reset for provider: {provider}", user_id=current_user.id)
            return {"message": f"Circuit breaker reset for {provider}", "success": True}
        else:
            return {"message": f"Provider {provider} not found", "success": False}
            
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker for {provider}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )

@router.post("/generate/stream", response_class=StreamingResponse)
async def generate_quote_stream(
    quote_request: QuoteGenerate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a quote with streaming response for real-time updates.
    Useful for showing generation progress to users.
    """
    
    async def quote_stream():
        """Generator for streaming quote generation progress."""
        
        try:
            # Send initial status
            yield f"data: {{'status': 'initializing', 'message': 'Preparing AI service...'}}\n\n"
            
            ai_service = await get_ai_service()
            yield f"data: {{'status': 'provider_selection', 'message': 'Selecting optimal AI provider...'}}\n\n"
            
            # Build AI request
            service_category = _map_service_type_to_category(quote_request.service_type)
            ai_request = AIRequest(
                prompt=_build_enhanced_prompt(quote_request),
                context=_build_context_from_request(quote_request),
                category=service_category,
                user_id=str(current_user.id)
            )
            
            # Get provider selection
            provider = await ai_service.router.select_provider(
                request_tokens=ai_request.max_tokens
            )
            
            yield f"data: {{'status': 'generating', 'provider': '{provider}', 'message': 'Generating quote...'}}\n\n"
            
            # Generate quote
            ai_response = await ai_service.generate_quote(ai_request)
            
            # Save to database
            db_quote = Quote(
                user_id=current_user.id,
                service_type=quote_request.service_type,
                quote_text=ai_response.text,
                ai_provider=ai_response.provider.value,
                ai_model=ai_response.model,
                tokens_used=ai_response.tokens_used,
                generation_cost=ai_response.cost,
                quality_score=ai_response.quality_score,
                status=QuoteStatus.ACTIVE
            )
            
            db.add(db_quote)
            db.commit()
            db.refresh(db_quote)
            
            # Send final result
            result = {
                'status': 'completed',
                'quote_id': db_quote.id,
                'quote_text': ai_response.text,
                'metadata': {
                    'provider': ai_response.provider.value,
                    'model': ai_response.model,
                    'tokens_used': ai_response.tokens_used,
                    'cost': ai_response.cost,
                    'quality_score': ai_response.quality_score,
                    'cached': ai_response.cached
                }
            }
            
            import json
            yield f"data: {json.dumps(result)}\n\n"
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__
            }
            import json
            yield f"data: {json.dumps(error_result)}\n\n"
    
    return StreamingResponse(
        quote_stream(),
        media_type="text/stream-event",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

# Utility functions

def _map_service_type_to_category(service_type: str) -> Optional[ServiceCategory]:
    """Map quote service type to AI service category."""
    
    mapping = {
        "window_cleaning": ServiceCategory.WINDOW_CLEANING,
        "pressure_washing": ServiceCategory.PRESSURE_WASHING,
        "gutter_cleaning": ServiceCategory.GUTTER_CLEANING,
        "solar_panel_cleaning": ServiceCategory.SOLAR_PANEL_CLEANING,
        "roof_cleaning": ServiceCategory.ROOF_CLEANING,
        "driveway_cleaning": ServiceCategory.DRIVEWAY_CLEANING,
        "building_wash": ServiceCategory.BUILDING_WASH,
        "graffiti_removal": ServiceCategory.GRAFFITI_REMOVAL
    }
    
    return mapping.get(service_type.lower())

def _get_routing_strategy(quote_request: QuoteGenerate, user: User) -> Optional[RoutingStrategy]:
    """Determine routing strategy based on request and user preferences."""
    
    # Business logic for routing strategy selection
    if hasattr(quote_request, 'priority') and quote_request.priority == "cost_optimized":
        return RoutingStrategy.COST_OPTIMIZED
    elif hasattr(quote_request, 'priority') and quote_request.priority == "performance":
        return RoutingStrategy.PERFORMANCE_BASED
    elif user.is_premium:  # Assuming premium users get performance-based routing
        return RoutingStrategy.PERFORMANCE_BASED
    else:
        return RoutingStrategy.COST_OPTIMIZED

def _build_enhanced_prompt(quote_request: QuoteGenerate) -> str:
    """Build enhanced prompt with more context and specificity."""
    
    base_prompt = f"Generate a professional quote for {quote_request.service_type} services."
    
    # Add property-specific details
    if hasattr(quote_request, 'property_type'):
        base_prompt += f" Property type: {quote_request.property_type}."
    
    if hasattr(quote_request, 'property_size'):
        base_prompt += f" Property size: {quote_request.property_size}."
    
    if hasattr(quote_request, 'frequency'):
        base_prompt += f" Service frequency: {quote_request.frequency}."
    
    if hasattr(quote_request, 'additional_requirements'):
        base_prompt += f" Special requirements: {quote_request.additional_requirements}."
    
    base_prompt += " Include pricing breakdown, service details, and timeline."
    
    return base_prompt

def _build_context_from_request(quote_request: QuoteGenerate) -> Optional[str]:
    """Build context string from quote request details."""
    
    context_parts = []
    
    if hasattr(quote_request, 'location'):
        context_parts.append(f"Location: {quote_request.location}")
    
    if hasattr(quote_request, 'urgency'):
        context_parts.append(f"Urgency: {quote_request.urgency}")
    
    if hasattr(quote_request, 'budget_range'):
        context_parts.append(f"Budget range: {quote_request.budget_range}")
    
    return "; ".join(context_parts) if context_parts else None

async def _post_generation_analytics(quote_id: int, ai_response, user_id: int):
    """Background task for post-generation analytics and logging."""
    
    try:
        # Log analytics data
        logger.info(
            "Quote generation analytics",
            quote_id=quote_id,
            user_id=user_id,
            provider=ai_response.provider.value,
            model=ai_response.model,
            tokens_used=ai_response.tokens_used,
            cost=ai_response.cost,
            quality_score=ai_response.quality_score,
            response_time=ai_response.response_time,
            cached=ai_response.cached
        )
        
        # Could add more analytics tasks here:
        # - Update user usage statistics
        # - Track provider performance
        # - Update cost tracking
        # - Quality feedback loop
        
    except Exception as e:
        logger.error("Post-generation analytics failed", error=str(e))
