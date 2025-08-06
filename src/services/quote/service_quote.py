"""
Service Quote Service - Main service for handling service quote operations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.service_quote import ServiceQuote, ServiceType, PropertyType, PerthSuburb, QuoteStatus
from src.models.user import User
from src.models.voice_recording import VoiceRecording
from src.services.quote.pricing_engine import get_pricing_engine
from src.services.voice.processor import VoiceProcessor
from src.core.database import get_db_session
from src.core.exceptions import QuoteGenerationException

logger = logging.getLogger(__name__)


class ServiceQuoteService:
    """Main service for handling service quote operations"""
    
    def __init__(self):
        self.pricing_engine = get_pricing_engine()
        self.voice_processor = VoiceProcessor()
    
    def create_service_quote(
        self,
        user_id: int,
        service_type: ServiceType,
        property_type: PropertyType,
        suburb: PerthSuburb,
        customer_name: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        property_address: Optional[str] = None,
        window_count: Optional[int] = None,
        square_meters: Optional[float] = None,
        storeys: int = 1,
        access_difficulty: str = "easy",
        customer_notes: Optional[str] = None,
        voice_recording_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new service quote with pricing calculation
        """
        try:
            with get_db_session() as db:
                # Step 1: Calculate pricing using pricing engine
                pricing_data = self.pricing_engine.calculate_service_quote(
                    service_type=service_type,
                    property_type=property_type,
                    suburb=suburb,
                    window_count=window_count,
                    square_meters=square_meters,
                    storeys=storeys,
                    access_difficulty=access_difficulty,
                    customer_notes=customer_notes,
                    user_id=user_id
                )
                
                # Step 2: Create service quote record
                service_quote = ServiceQuote(
                    user_id=user_id,
                    service_type=service_type,
                    property_type=property_type,
                    suburb=suburb,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    property_address=property_address,
                    window_count=window_count,
                    square_meters=square_meters,
                    storeys=storeys,
                    access_difficulty=access_difficulty,
                    customer_notes=customer_notes,
                    base_price=pricing_data['pricing']['base_price'],
                    quantity_price=pricing_data['pricing']['quantity_price'],
                    location_adjustment=pricing_data['pricing']['location_adjustment']['factor'],
                    complexity_adjustment=pricing_data['pricing']['complexity_adjustment']['factor'],
                    final_price=pricing_data['pricing']['final_price'],
                    quote_text=pricing_data['quote_details']['quote_text'],
                    inclusions=pricing_data['quote_details']['inclusions'],
                    exclusions=pricing_data['quote_details']['exclusions'],
                    terms_conditions=pricing_data['quote_details']['terms_conditions'],
                    quote_number=pricing_data['validity']['quote_number'],
                    voice_recording_id=voice_recording_id,
                    status=QuoteStatus.DRAFT
                )
                
                db.add(service_quote)
                db.commit()
                db.refresh(service_quote)
                
                # Step 3: Prepare response
                response = {
                    "quote_id": service_quote.id,
                    "quote_number": service_quote.quote_number,
                    "pricing": pricing_data['pricing'],
                    "quote_details": pricing_data['quote_details'],
                    "service_specifications": pricing_data['service_specifications'],
                    "validity": pricing_data['validity'],
                    "customer_info": {
                        "name": customer_name,
                        "email": customer_email,
                        "phone": customer_phone,
                        "address": property_address
                    },
                    "status": service_quote.status.value,
                    "created_at": service_quote.created_at.isoformat()
                }
                
                logger.info(f"Created service quote {service_quote.quote_number} for user {user_id}")
                return response
                
        except Exception as e:
            logger.error(f"Error creating service quote: {str(e)}")
            raise QuoteGenerationException(f"Failed to create service quote: {str(e)}")
    
    def get_service_quote(self, quote_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get service quote by ID"""
        try:
            with get_db_session() as db:
                quote = db.query(ServiceQuote).filter(
                    ServiceQuote.id == quote_id,
                    ServiceQuote.user_id == user_id
                ).first()
                
                if not quote:
                    return None
                
                return self._format_quote_response(quote)
                
        except Exception as e:
            logger.error(f"Error retrieving service quote {quote_id}: {str(e)}")
            return None
    
    def get_user_quotes(
        self, 
        user_id: int, 
        status: Optional[QuoteStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all service quotes for a user"""
        try:
            with get_db_session() as db:
                query = db.query(ServiceQuote).filter(ServiceQuote.user_id == user_id)
                
                if status:
                    query = query.filter(ServiceQuote.status == status)
                
                quotes = query.order_by(ServiceQuote.created_at.desc()).offset(offset).limit(limit).all()
                
                return [self._format_quote_response(quote) for quote in quotes]
                
        except Exception as e:
            logger.error(f"Error retrieving user quotes for user {user_id}: {str(e)}")
            return []
    
    def update_quote_status(self, quote_id: int, user_id: int, status: QuoteStatus) -> bool:
        """Update quote status"""
        try:
            with get_db_session() as db:
                quote = db.query(ServiceQuote).filter(
                    ServiceQuote.id == quote_id,
                    ServiceQuote.user_id == user_id
                ).first()
                
                if not quote:
                    return False
                
                old_status = quote.status
                setattr(quote, 'status', status.value)
                setattr(quote, 'updated_at', datetime.now())
                
                # Handle status-specific logic
                if status == QuoteStatus.ACCEPTED:
                    setattr(quote, 'accepted_at', datetime.now())
                elif status == QuoteStatus.SENT:
                    setattr(quote, 'sent_at', datetime.now())
                
                db.commit()
                logger.info(f"Updated quote {quote.quote_number} status from {old_status} to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating quote status: {str(e)}")
            return False
    
    def create_quote_from_voice(
        self,
        user_id: int,
        voice_recording_id: int
    ) -> Dict[str, Any]:
        """Create service quote from voice recording"""
        try:
            with get_db_session() as db:
                # Get voice recording
                voice_recording = db.query(VoiceRecording).filter(
                    VoiceRecording.id == voice_recording_id,
                    VoiceRecording.user_id == user_id
                ).first()
                
                if not voice_recording:
                    raise QuoteGenerationException("Voice recording not found")
                
                # Extract service details from transcription
                service_details = self._extract_service_details_from_voice(voice_recording)
                
                # Create quote with extracted details
                return self.create_service_quote(
                    user_id=user_id,
                    voice_recording_id=voice_recording_id,
                    **service_details
                )
                
        except Exception as e:
            logger.error(f"Error creating quote from voice: {str(e)}")
            raise QuoteGenerationException(f"Failed to create quote from voice: {str(e)}")
    
    def recalculate_quote_pricing(self, quote_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Recalculate pricing for existing quote"""
        try:
            with get_db_session() as db:
                quote = db.query(ServiceQuote).filter(
                    ServiceQuote.id == quote_id,
                    ServiceQuote.user_id == user_id
                ).first()
                
                if not quote:
                    return None
                
                # Recalculate pricing
                pricing_data = self.pricing_engine.calculate_service_quote(
                    service_type=ServiceType(getattr(quote, 'service_type')),
                    property_type=PropertyType(getattr(quote, 'property_type')),
                    suburb=PerthSuburb(getattr(quote, 'suburb')),
                    window_count=getattr(quote, 'window_count'),
                    square_meters=getattr(quote, 'square_meters'),
                    storeys=getattr(quote, 'storeys'),
                    access_difficulty=getattr(quote, 'access_difficulty'),
                    customer_notes=getattr(quote, 'customer_notes'),
                    user_id=user_id
                )
                
                # Update quote with new pricing
                setattr(quote, 'base_price', pricing_data['pricing']['base_price'])
                setattr(quote, 'quantity_price', pricing_data['pricing']['quantity_price'])
                setattr(quote, 'location_adjustment', pricing_data['pricing']['location_adjustment']['factor'])
                setattr(quote, 'complexity_adjustment', pricing_data['pricing']['complexity_adjustment']['factor'])
                setattr(quote, 'final_price', pricing_data['pricing']['final_price'])
                setattr(quote, 'quote_text', pricing_data['quote_details']['quote_text'])
                setattr(quote, 'updated_at', datetime.now())
                
                db.commit()
                db.refresh(quote)
                
                return self._format_quote_response(quote)
                
        except Exception as e:
            logger.error(f"Error recalculating quote pricing: {str(e)}")
            return None
    
    def get_quote_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get analytics for user's quotes"""
        try:
            with get_db_session() as db:
                cutoff_date = datetime.now() - timedelta(days=days)
                
                quotes = db.query(ServiceQuote).filter(
                    ServiceQuote.user_id == user_id,
                    ServiceQuote.created_at >= cutoff_date
                ).all()
                
                if not quotes:
                    return {
                        "total_quotes": 0,
                        "average_quote_value": 0,
                        "total_quote_value": 0,
                        "quote_status_breakdown": {},
                        "service_type_breakdown": {},
                        "suburb_breakdown": {}
                    }
                
                # Calculate analytics
                total_quotes = len(quotes)
                total_value = sum(quote.final_price for quote in quotes)
                average_value = total_value / total_quotes if total_quotes > 0 else 0
                
                # Status breakdown
                status_breakdown = {}
                for quote in quotes:
                    status = quote.status.value
                    status_breakdown[status] = status_breakdown.get(status, 0) + 1
                
                # Service type breakdown
                service_breakdown = {}
                for quote in quotes:
                    service = quote.service_type.value
                    service_breakdown[service] = service_breakdown.get(service, 0) + 1
                
                # Suburb breakdown
                suburb_breakdown = {}
                for quote in quotes:
                    suburb = quote.suburb.value
                    suburb_breakdown[suburb] = suburb_breakdown.get(suburb, 0) + 1
                
                return {
                    "total_quotes": total_quotes,
                    "average_quote_value": round(average_value, 2),
                    "total_quote_value": round(total_value, 2),
                    "quote_status_breakdown": status_breakdown,
                    "service_type_breakdown": service_breakdown,
                    "suburb_breakdown": suburb_breakdown
                }
                
        except Exception as e:
            logger.error(f"Error getting quote analytics: {str(e)}")
            return {}
    
    def _format_quote_response(self, quote: ServiceQuote) -> Dict[str, Any]:
        """Format service quote for API response"""
        return {
            "id": quote.id,
            "quote_number": getattr(quote, 'quote_number'),
            "service_type": getattr(quote, 'service_type'),
            "property_type": getattr(quote, 'property_type'),
            "suburb": getattr(quote, 'suburb'),
            "customer_name": getattr(quote, 'customer_name'),
            "customer_email": getattr(quote, 'customer_email'),
            "customer_phone": getattr(quote, 'customer_phone'),
            "property_address": getattr(quote, 'property_address'),
            "specifications": {
                "window_count": getattr(quote, 'window_count'),
                "square_meters": getattr(quote, 'square_meters'),
                "storeys": getattr(quote, 'storeys'),
                "access_difficulty": getattr(quote, 'access_difficulty')
            },
            "pricing": {
                "base_price": getattr(quote, 'base_price'),
                "quantity_price": getattr(quote, 'quantity_price'),
                "location_adjustment": getattr(quote, 'location_adjustment'),
                "complexity_adjustment": getattr(quote, 'complexity_adjustment'),
                "final_price": getattr(quote, 'final_price')
            },
            "quote_text": getattr(quote, 'quote_text'),
            "inclusions": getattr(quote, 'inclusions'),
            "exclusions": getattr(quote, 'exclusions'),
            "terms_conditions": getattr(quote, 'terms_conditions'),
            "status": getattr(quote, 'status'),
            "customer_notes": getattr(quote, 'customer_notes'),
            "voice_recording_id": getattr(quote, 'voice_recording_id'),
            "created_at": getattr(quote, 'created_at').isoformat(),
            "updated_at": getattr(quote, 'updated_at').isoformat() if getattr(quote, 'updated_at') else None,
            "sent_at": getattr(quote, 'sent_at').isoformat() if getattr(quote, 'sent_at') else None,
            "accepted_at": getattr(quote, 'accepted_at').isoformat() if getattr(quote, 'accepted_at') else None
        }
    
    def _extract_service_details_from_voice(self, voice_recording: VoiceRecording) -> Dict[str, Any]:
        """Extract service details from voice recording transcription"""
        # This would use AI to extract structured data from voice transcription
        # For now, return basic defaults that would be enhanced by AI
        
        transcription = voice_recording.transcription or ""
        
        # Basic keyword matching (would be enhanced with AI)
        service_type = ServiceType.WINDOW_CLEANING
        property_type = PropertyType.RESIDENTIAL_HOUSE
        suburb = PerthSuburb.COTTESLOE  # Default to a valid suburb
        
        if "pressure wash" in transcription.lower():
            service_type = ServiceType.PRESSURE_WASHING
        elif "gutter" in transcription.lower():
            service_type = ServiceType.GUTTER_CLEANING
        elif "combined" in transcription.lower() or "both" in transcription.lower():
            service_type = ServiceType.COMBINED_SERVICE
        
        if "unit" in transcription.lower() or "apartment" in transcription.lower():
            property_type = PropertyType.RESIDENTIAL_UNIT
        elif "office" in transcription.lower():
            property_type = PropertyType.COMMERCIAL_OFFICE
        elif "shop" in transcription.lower() or "retail" in transcription.lower():
            property_type = PropertyType.COMMERCIAL_RETAIL
        
        # Extract basic details (would be enhanced with AI)
        return {
            "service_type": service_type,
            "property_type": property_type,
            "suburb": suburb,
            "customer_name": "Customer",  # Would extract from voice
            "customer_notes": transcription
        }


def get_service_quote_service() -> ServiceQuoteService:
    """Get singleton instance of service quote service"""
    return ServiceQuoteService()
