"""
Service Quote model for Window & Pressure Cleaning Services
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re

from src.config.database import Base

class ServiceType(PyEnum):
    """Types of cleaning services"""
    WINDOW_CLEANING = "window_cleaning"
    PRESSURE_WASHING = "pressure_washing"
    GUTTER_CLEANING = "gutter_cleaning"
    SOLAR_PANEL_CLEANING = "solar_panel_cleaning"
    ROOF_CLEANING = "roof_cleaning"
    DRIVEWAY_CLEANING = "driveway_cleaning"
    COMBINED_SERVICE = "combined_service"

class PropertyType(PyEnum):
    """Types of properties"""
    RESIDENTIAL_HOUSE = "residential_house"
    RESIDENTIAL_UNIT = "residential_unit"
    COMMERCIAL_OFFICE = "commercial_office"
    COMMERCIAL_RETAIL = "commercial_retail"
    INDUSTRIAL = "industrial"
    STRATA_COMPLEX = "strata_complex"

class PerthSuburb(PyEnum):
    """Perth suburbs with pricing zones"""
    # Premium suburbs (Zone A - 20% markup)
    COTTESLOE = "cottesloe"
    PEPPERMINT_GROVE = "peppermint_grove"
    MOSMAN_PARK = "mosman_park"
    NEDLANDS = "nedlands"
    DALKEITH = "dalkeith"
    
    # Mid-tier suburbs (Zone B - standard pricing)
    FREMANTLE = "fremantle"
    SUBIACO = "subiaco"
    LEEDERVILLE = "leederville"
    MOUNT_LAWLEY = "mount_lawley"
    VICTORIA_PARK = "victoria_park"
    
    # Standard suburbs (Zone C - standard pricing)
    PERTH_CBD = "perth_cbd"
    EAST_PERTH = "east_perth"
    WEST_PERTH = "west_perth"
    NORTHBRIDGE = "northbridge"
    
    # Outer suburbs (Zone D - distance surcharge)
    JOONDALUP = "joondalup"
    ROCKINGHAM = "rockingham"
    MANDURAH = "mandurah"

class QuoteStatus(PyEnum):
    """Status of service quote"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class QuoteSource(PyEnum):
    """Source of the quote request"""
    AI_GENERATED = "ai_generated"
    MANUAL_INPUT = "manual_input"
    VOICE_TO_TEXT = "voice_to_text"
    PHONE_INQUIRY = "phone_inquiry"
    WEBSITE_FORM = "website_form"
    EMAIL_REQUEST = "email_request"

class AIModel(PyEnum):
    """AI models used for quote generation"""
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT3_5 = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GEMINI_PRO = "gemini-pro"

class ServiceQuote(Base):
    __tablename__ = "service_quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String(20), unique=True, nullable=False, index=True)  # Q2025-001
    
    # Customer Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    customer_name = Column(String(100))
    customer_email = Column(String(255))
    customer_phone = Column(String(20))
    
    # Service Details
    service_type = Column(Enum(ServiceType), nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False)
    property_address = Column(Text)
    suburb = Column(Enum(PerthSuburb), nullable=False, index=True)
    
    # Service Specifications
    window_count = Column(Integer)  # For window cleaning
    square_meters = Column(Float)   # For pressure washing/area-based services
    storeys = Column(Integer, default=1)  # Building height
    access_difficulty = Column(String(20))  # easy, medium, hard, extreme
    
    # Pricing
    base_price = Column(Float, nullable=False)  # Base service price
    zone_adjustment = Column(Float, default=0)  # Suburb pricing adjustment
    difficulty_adjustment = Column(Float, default=0)  # Access/complexity adjustment
    total_price = Column(Float, nullable=False)  # Final quoted price
    
    # Additional Details
    adjustments = Column(JSON)  # Detailed pricing breakdown JSON
    service_notes = Column(Text)  # Special requirements, conditions
    inclusions = Column(Text)  # What's included in the service
    exclusions = Column(Text)  # What's not included
    
    # Quote Management
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT, index=True)
    source = Column(Enum(QuoteSource), default=QuoteSource.AI_GENERATED)
    ai_model = Column(Enum(AIModel))
    voice_recording_id = Column(Integer, ForeignKey("voice_recordings.id"), nullable=True)
    
    # AI Analysis
    customer_sentiment = Column(Float)  # -1 to 1 (price sensitive to eager)
    urgency_score = Column(Float)  # 0 to 1 (how urgent the job is)
    conversion_probability = Column(Float)  # 0 to 1 (likelihood to accept)
    psychology_profile = Column(Text)  # JSON stored customer psychology insights
    
    # Validity and Terms
    valid_until = Column(DateTime(timezone=True))  # Quote expiration
    terms_conditions = Column(Text)  # Quote terms and conditions
    payment_terms = Column(String(50))  # Payment terms
    
    # Metadata
    prompt_used = Column(Text)  # Original prompt for AI generation
    generation_context = Column(Text)  # JSON stored context
    
    # Tracking
    is_favorite = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)  # Can be used as template
    view_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)  # How many times sent
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    last_viewed = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="service_quotes")
    voice_recording = relationship("VoiceRecording", back_populates="service_quotes")

    def __repr__(self):
        return f"<ServiceQuote(id={self.id}, quote_number='{getattr(self, 'quote_number', 'Unknown')}', service='{getattr(self, 'service_type', 'Unknown')}')>"

    def _safe_isoformat(self, attr_name):
        """Safely get isoformat from datetime attribute"""
        try:
            dt = getattr(self, attr_name, None)
            return dt.isoformat() if dt is not None else None
        except:
            return None

    def _safe_enum_value(self, attr_name, default=None):
        """Safely get value from enum attribute"""
        try:
            enum_val = getattr(self, attr_name, None)
            return enum_val.value if enum_val is not None else default
        except:
            return default

    def generate_quote_number(self):
        """Generate unique quote number"""
        try:
            year = datetime.now().year
            # This would need to be implemented with a database query to get next sequence
            # For now, using timestamp-based approach
            timestamp = int(datetime.now().timestamp())
            return f"Q{year}-{str(timestamp)[-6:]}"
        except:
            return f"Q{datetime.now().year}-000001"

    def is_expired(self):
        """Check if quote has expired"""
        try:
            valid_until = getattr(self, 'valid_until', None)
            if not valid_until:
                return False
            return datetime.now(valid_until.tzinfo) > valid_until
        except:
            return False

    def days_until_expiry(self):
        """Get days until quote expires"""
        try:
            valid_until = getattr(self, 'valid_until', None)
            if not valid_until:
                return None
            delta = valid_until - datetime.now(valid_until.tzinfo)
            return max(0, delta.days)
        except:
            return None

    def get_zone_pricing_factor(self):
        """Get pricing adjustment factor based on suburb zone"""
        try:
            suburb = getattr(self, 'suburb', None)
            if not suburb:
                return 1.0
            
            # Premium suburbs (Zone A)
            premium_suburbs = [PerthSuburb.COTTESLOE, PerthSuburb.PEPPERMINT_GROVE, 
                             PerthSuburb.MOSMAN_PARK, PerthSuburb.NEDLANDS, PerthSuburb.DALKEITH]
            if suburb in premium_suburbs:
                return 1.2  # 20% markup
            
            # Outer suburbs (Zone D)
            outer_suburbs = [PerthSuburb.JOONDALUP, PerthSuburb.ROCKINGHAM, PerthSuburb.MANDURAH]
            if suburb in outer_suburbs:
                return 1.15  # 15% surcharge for distance
            
            # Standard pricing for all other zones
            return 1.0
        except:
            return 1.0

    def get_difficulty_multiplier(self):
        """Get pricing multiplier based on access difficulty"""
        try:
            difficulty = getattr(self, 'access_difficulty', 'easy')
            multipliers = {
                'easy': 1.0,
                'medium': 1.15,
                'hard': 1.3,
                'extreme': 1.5
            }
            return multipliers.get(difficulty, 1.0)
        except:
            return 1.0

    def calculate_total_price(self):
        """Calculate total price with all adjustments"""
        try:
            base = getattr(self, 'base_price', 0)
            zone_factor = self.get_zone_pricing_factor()
            difficulty_factor = self.get_difficulty_multiplier()
            
            total = base * zone_factor * difficulty_factor
            return round(total, 2)
        except:
            return 0.0

    def get_service_display_name(self):
        """Get human-readable service name"""
        try:
            service = getattr(self, 'service_type', None)
            if not service:
                return "Unknown Service"
            
            display_names = {
                ServiceType.WINDOW_CLEANING: "Window Cleaning",
                ServiceType.PRESSURE_WASHING: "Pressure Washing",
                ServiceType.GUTTER_CLEANING: "Gutter Cleaning",
                ServiceType.SOLAR_PANEL_CLEANING: "Solar Panel Cleaning",
                ServiceType.ROOF_CLEANING: "Roof Cleaning",
                ServiceType.DRIVEWAY_CLEANING: "Driveway Cleaning",
                ServiceType.COMBINED_SERVICE: "Combined Service Package"
            }
            return display_names.get(service, service.value.replace('_', ' ').title())
        except:
            return "Unknown Service"

    def get_formatted_address(self):
        """Get formatted address string"""
        try:
            address = getattr(self, 'property_address', '')
            suburb = getattr(self, 'suburb', None)
            
            if address and suburb:
                suburb_name = suburb.value.replace('_', ' ').title()
                return f"{address}, {suburb_name}, WA"
            elif suburb:
                return suburb.value.replace('_', ' ').title() + ", WA"
            return address or "Address not specified"
        except:
            return "Address not available"

    def to_dict(self, include_sensitive=False):
        """Convert service quote to dictionary"""
        try:
            data = {
                "id": getattr(self, 'id', None),
                "quote_number": getattr(self, 'quote_number', None),
                "user_id": getattr(self, 'user_id', None),
                "customer_name": getattr(self, 'customer_name', None),
                "service_type": self._safe_enum_value('service_type'),
                "service_display_name": self.get_service_display_name(),
                "property_type": self._safe_enum_value('property_type'),
                "property_address": getattr(self, 'property_address', None),
                "formatted_address": self.get_formatted_address(),
                "suburb": self._safe_enum_value('suburb'),
                "window_count": getattr(self, 'window_count', None),
                "square_meters": getattr(self, 'square_meters', None),
                "storeys": getattr(self, 'storeys', None),
                "access_difficulty": getattr(self, 'access_difficulty', None),
                "base_price": getattr(self, 'base_price', None),
                "zone_adjustment": getattr(self, 'zone_adjustment', None),
                "difficulty_adjustment": getattr(self, 'difficulty_adjustment', None),
                "total_price": getattr(self, 'total_price', None),
                "adjustments": getattr(self, 'adjustments', None),
                "service_notes": getattr(self, 'service_notes', None),
                "inclusions": getattr(self, 'inclusions', None),
                "exclusions": getattr(self, 'exclusions', None),
                "status": self._safe_enum_value('status'),
                "source": self._safe_enum_value('source'),
                "ai_model": self._safe_enum_value('ai_model'),
                "valid_until": self._safe_isoformat('valid_until'),
                "is_expired": self.is_expired(),
                "days_until_expiry": self.days_until_expiry(),
                "terms_conditions": getattr(self, 'terms_conditions', None),
                "payment_terms": getattr(self, 'payment_terms', None),
                "view_count": getattr(self, 'view_count', 0),
                "sent_count": getattr(self, 'sent_count', 0),
                "created_at": self._safe_isoformat('created_at'),
                "updated_at": self._safe_isoformat('updated_at'),
                "sent_at": self._safe_isoformat('sent_at'),
                "accepted_at": self._safe_isoformat('accepted_at')
            }
            
            if include_sensitive:
                data.update({
                    "customer_email": getattr(self, 'customer_email', None),
                    "customer_phone": getattr(self, 'customer_phone', None),
                    "customer_sentiment": getattr(self, 'customer_sentiment', None),
                    "urgency_score": getattr(self, 'urgency_score', None),
                    "conversion_probability": getattr(self, 'conversion_probability', None),
                    "psychology_profile": getattr(self, 'psychology_profile', None),
                    "prompt_used": getattr(self, 'prompt_used', None),
                    "generation_context": getattr(self, 'generation_context', None)
                })
            
            return data
        except Exception as e:
            return {
                "id": getattr(self, 'id', None),
                "quote_number": getattr(self, 'quote_number', 'Error'),
                "service_type": "unknown",
                "error": str(e)
            }

    def to_customer_quote(self):
        """Convert to customer-facing quote format"""
        try:
            return {
                "quote_number": getattr(self, 'quote_number', None),
                "service": self.get_service_display_name(),
                "property_address": self.get_formatted_address(),
                "total_price": f"${getattr(self, 'total_price', 0):,.2f}",
                "inclusions": getattr(self, 'inclusions', None),
                "exclusions": getattr(self, 'exclusions', None),
                "terms": getattr(self, 'terms_conditions', None),
                "payment_terms": getattr(self, 'payment_terms', None),
                "valid_until": self._safe_isoformat('valid_until'),
                "status": self._safe_enum_value('status'),
                "created_date": self._safe_isoformat('created_at')
            }
        except:
            return {
                "quote_number": getattr(self, 'quote_number', 'Error'),
                "service": "Service information unavailable",
                "total_price": "$0.00"
            }

    def to_summary_dict(self):
        """Convert to summary format for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "quote_number": getattr(self, 'quote_number', None),
                "service": self.get_service_display_name(),
                "customer_name": getattr(self, 'customer_name', None),
                "suburb": self._safe_enum_value('suburb'),
                "total_price": f"${getattr(self, 'total_price', 0):,.2f}",
                "status": self._safe_enum_value('status'),
                "created_at": self._safe_isoformat('created_at'),
                "valid_until": self._safe_isoformat('valid_until'),
                "is_expired": self.is_expired()
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "quote_number": getattr(self, 'quote_number', 'Error'),
                "service": "Unknown",
                "status": "error"
            }
