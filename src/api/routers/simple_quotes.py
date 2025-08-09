"""Simple quote calculator API for testing frontend integration."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/simple-quotes", tags=["simple-quotes"])


class SimpleQuoteRequest(BaseModel):
    suburb: str
    address: str
    services: List[str]
    base_price: float
    multiplier: float


@router.post("/calculate")
async def calculate_simple_quote(request: SimpleQuoteRequest):
    """Calculate a simple quote without authentication"""
    try:
        adjusted_price = request.base_price * request.multiplier
        quote_id = f"SQ-{datetime.now().strftime('%Y%m%d')}-{hash(f'{request.suburb}-{request.address}') % 10000:04d}"

        service_names = {
            "residential": "Residential Glass Repair",
            "commercial": "Commercial Glazing Services",
            "emergency": "Emergency Glass Repair",
            "shower": "Shower Screen Installation/Repair",
            "mirrors": "Mirror Installation/Repair",
            "windows": "Window Cleaning/Repair",
        }

        selected_service_names = [
            service_names.get(svc, svc) for svc in request.services
        ]

        return {
            "quote_id": quote_id,
            "suburb": request.suburb,
            "address": request.address,
            "services": request.services,
            "service_names": selected_service_names,
            "base_price": request.base_price,
            "adjusted_price": adjusted_price,
            "multiplier": request.multiplier,
            "ai_quote": f"Professional {', '.join(selected_service_names)} service for your property in {request.suburb}. Our experienced team will provide quality service with attention to detail.",
            "recommendation": f"Based on your location in {request.suburb}, we recommend our comprehensive service package for optimal results.",
            "estimated_duration": "2-4 hours depending on scope of work",
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate service quote: {str(e)}"
        )
