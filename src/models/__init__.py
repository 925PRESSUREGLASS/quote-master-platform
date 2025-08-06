"""Database models for Quote Master Pro - Window & Pressure Cleaning Services"""

# Import models
from src.models.user import User, UserRole, UserStatus
from src.models.service_quote import (
    ServiceQuote, ServiceType, PropertyType, PerthSuburb, 
    QuoteStatus, QuoteSource, AIModel
)
from src.models.pricing_rule import PricingRule, PricingRuleType
from src.models.voice_recording import VoiceRecording, AudioFormat, VoiceRecordingStatus
from src.models.analytics import AnalyticsEvent, EventType, EventCategory

# Keep old quote model for backward compatibility during migration
from src.models.quote import Quote, QuoteCategory

# Export all models and enums
__all__ = [
    # Models
    "User",
    "ServiceQuote",     # New primary quote model
    "Quote",           # Legacy model for migration
    "PricingRule",     # New pricing configuration
    "VoiceRecording",
    "AnalyticsEvent",
    
    # User enums
    "UserRole",
    "UserStatus",
    
    # Service Quote enums
    "ServiceType",
    "PropertyType", 
    "PerthSuburb",
    "QuoteStatus",
    "QuoteSource",
    "AIModel",
    
    # Pricing enums
    "PricingRuleType",
    
    # Legacy Quote enums (for migration)
    "QuoteCategory",
    
    # Voice recording enums
    "AudioFormat",
    "VoiceRecordingStatus",
    
    # Analytics enums
    "EventType",
    "EventCategory"
]