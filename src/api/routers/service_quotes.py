"""
Service Quotes API Router
Endpoints for window and pressure cleaning service quotes
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_current_user
from src.models.service_quote import PerthSuburb, PropertyType, QuoteStatus, ServiceType
from src.models.user import User
from src.services.quote import get_service_quote_service

router = APIRouter(tags=["service-quotes"])


# Request/Response Models
class ServiceQuoteRequest(BaseModel):
    """Request model for creating service quotes"""

    service_type: ServiceType = Field(..., description="Type of service")
    property_type: PropertyType = Field(..., description="Type of property")
    suburb: PerthSuburb = Field(..., description="Perth suburb location")
    customer_name: str = Field(
        ..., min_length=2, max_length=100, description="Customer name"
    )
    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    property_address: Optional[str] = Field(None, description="Property address")
    window_count: Optional[int] = Field(
        None, ge=1, le=200, description="Number of windows"
    )
    square_meters: Optional[float] = Field(
        None, ge=1, le=10000, description="Area in square meters"
    )
    storeys: int = Field(1, ge=1, le=10, description="Number of storeys")
    access_difficulty: str = Field("easy", description="Access difficulty level")
    customer_notes: Optional[str] = Field(
        None, max_length=1000, description="Additional notes"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_type": "window_cleaning",
                "property_type": "residential_house",
                "suburb": "cottesloe",
                "customer_name": "John Smith",
                "customer_email": "john@example.com",
                "customer_phone": "0412345678",
                "property_address": "123 Beach Road, Cottesloe WA 6011",
                "window_count": 15,
                "storeys": 2,
                "access_difficulty": "medium",
                "customer_notes": "Large windows facing the beach",
            }
        }


class ServiceQuoteResponse(BaseModel):
    """Response model for service quotes"""

    quote_id: int
    quote_number: str
    pricing: Dict[str, Any]
    quote_details: Dict[str, Any]
    service_specifications: Dict[str, Any]
    validity: Dict[str, Any]
    customer_info: Dict[str, Any]
    status: str
    created_at: str


class QuoteStatusUpdate(BaseModel):
    """Request model for updating quote status"""

    status: QuoteStatus = Field(..., description="New quote status")


class VoiceQuoteRequest(BaseModel):
    """Request model for creating quote from voice recording"""

    voice_recording_id: int = Field(..., description="Voice recording ID")


# Endpoints
@router.post("/service-quotes/calculate", response_model=ServiceQuoteResponse)
async def create_service_quote(
    request: ServiceQuoteRequest,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Calculate and create a new service quote
    """
    try:
        quote_data = service.create_service_quote(
            user_id=current_user.id,
            service_type=request.service_type,
            property_type=request.property_type,
            suburb=request.suburb,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            customer_phone=request.customer_phone,
            property_address=request.property_address,
            window_count=request.window_count,
            square_meters=request.square_meters,
            storeys=request.storeys,
            access_difficulty=request.access_difficulty,
            customer_notes=request.customer_notes,
        )

        return ServiceQuoteResponse(**quote_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create service quote: {str(e)}",
        )


@router.post("/service-quotes/from-voice", response_model=ServiceQuoteResponse)
async def create_quote_from_voice(
    request: VoiceQuoteRequest,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Create service quote from voice recording
    """
    try:
        quote_data = service.create_quote_from_voice(
            user_id=current_user.id, voice_recording_id=request.voice_recording_id
        )

        return ServiceQuoteResponse(**quote_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create quote from voice: {str(e)}",
        )


@router.get("/{quote_id}")
async def get_service_quote(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Get service quote by ID
    """
    quote = service.get_service_quote(quote_id, current_user.id)

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service quote not found"
        )

    return quote


@router.get("/service-quotes/")
async def get_user_quotes(
    status_filter: Optional[QuoteStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Get all service quotes for current user
    """
    quotes = service.get_user_quotes(
        user_id=current_user.id, status=status_filter, limit=limit, offset=offset
    )

    return {"quotes": quotes, "total": len(quotes), "limit": limit, "offset": offset}


@router.put("/service-quotes/{quote_id}/status")
async def update_quote_status(
    quote_id: int,
    request: QuoteStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Update quote status
    """
    success = service.update_quote_status(
        quote_id=quote_id, user_id=current_user.id, status=request.status
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service quote not found or update failed",
        )

    return {"message": "Quote status updated successfully"}


@router.post("/service-quotes/{quote_id}/recalculate")
async def recalculate_quote_pricing(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Recalculate pricing for existing quote
    """
    updated_quote = service.recalculate_quote_pricing(
        quote_id=quote_id, user_id=current_user.id
    )

    if not updated_quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service quote not found"
        )

    return updated_quote


@router.get("/service-quotes/analytics/summary")
async def get_quote_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    service: Any = Depends(get_service_quote_service),
):
    """
    Get analytics summary for user's quotes
    """
    analytics = service.get_quote_analytics(user_id=current_user.id, days=days)

    return analytics


# Additional utility endpoints
@router.get("/service-quotes/enums/service-types")
async def get_service_types():
    """Get available service types"""
    return [
        {"value": item.value, "label": item.value.replace("_", " ").title()}
        for item in ServiceType
    ]


@router.get("/service-quotes/enums/property-types")
async def get_property_types():
    """Get available property types"""
    return [
        {"value": item.value, "label": item.value.replace("_", " ").title()}
        for item in PropertyType
    ]


@router.get("/service-quotes/enums/suburbs")
async def get_suburbs():
    """Get available Perth suburbs"""
    return [
        {"value": item.value, "label": item.value.replace("_", " ").title()}
        for item in PerthSuburb
    ]


@router.get("/service-quotes/enums/quote-statuses")
async def get_quote_statuses():
    """Get available quote statuses"""
    return [
        {"value": item.value, "label": item.value.replace("_", " ").title()}
        for item in QuoteStatus
    ]


# Simple public endpoint for testing
@router.post("/service-quotes/simple-calculate")
async def simple_calculate_quote(
    suburb: str, address: str, services: List[str], base_price: float, multiplier: float
):
    """Simple quote calculation without authentication (for testing)"""
    try:
        adjusted_price = base_price * multiplier
        quote_id = f"SQ-{datetime.now().strftime('%Y%m%d')}-{hash(f'{suburb}-{address}') % 10000:04d}"

        service_names = {
            "residential": "Residential Glass Repair",
            "commercial": "Commercial Glazing Services",
            "emergency": "Emergency Glass Repair",
            "shower": "Shower Screen Installation/Repair",
            "mirrors": "Mirror Installation/Repair",
            "windows": "Window Cleaning/Repair",
        }

        selected_service_names = [service_names.get(svc, svc) for svc in services]

        return {
            "quote_id": quote_id,
            "suburb": suburb,
            "address": address,
            "services": services,
            "service_names": selected_service_names,
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "multiplier": multiplier,
            "ai_quote": f"Professional {', '.join(selected_service_names)} service for your property in {suburb}. Our experienced team will provide quality service with attention to detail.",
            "recommendation": f"Based on your location in {suburb}, we recommend our comprehensive service package for optimal results.",
            "estimated_duration": "2-4 hours depending on scope of work",
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate service quote: {str(e)}"
        )
