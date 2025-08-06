"""
Pricing Rules model for configurable service pricing
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, JSON
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Optional, Dict, Any

from src.config.database import Base
from src.models.service_quote import ServiceType, PropertyType, PerthSuburb

class PricingRuleType(PyEnum):
    """Types of pricing rules"""
    BASE_SERVICE = "base_service"          # Base price for service type
    PROPERTY_MODIFIER = "property_modifier"  # Adjustment by property type
    LOCATION_MODIFIER = "location_modifier"  # Adjustment by suburb/zone
    DIFFICULTY_MODIFIER = "difficulty_modifier"  # Adjustment by access difficulty
    QUANTITY_TIER = "quantity_tier"        # Volume-based pricing tiers
    SEASONAL_MODIFIER = "seasonal_modifier"  # Seasonal price adjustments
    PROMOTION = "promotion"                # Promotional discounts

class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False, index=True)
    rule_type = Column(Enum(PricingRuleType), nullable=False, index=True)
    
    # Applicability conditions
    service_type = Column(Enum(ServiceType), nullable=True, index=True)
    property_type = Column(Enum(PropertyType), nullable=True)
    suburb = Column(Enum(PerthSuburb), nullable=True)
    
    # Pricing parameters
    base_price = Column(Float)  # Base price for service
    modifier_type = Column(String(20))  # 'multiplier', 'addition', 'percentage'
    modifier_value = Column(Float)  # The adjustment value
    min_price = Column(Float)  # Minimum price after adjustment
    max_price = Column(Float)  # Maximum price after adjustment
    
    # Quantity-based rules
    quantity_min = Column(Integer)  # Minimum quantity for rule
    quantity_max = Column(Integer)  # Maximum quantity for rule
    per_unit_price = Column(Float)  # Price per unit (window, sqm, etc.)
    
    # Conditions and metadata
    conditions = Column(JSON)  # Additional JSON conditions
    description = Column(String(255))  # Human-readable description
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # Validity period
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PricingRule(id={self.id}, name='{self.rule_name}', type='{self.rule_type}')>"

    def _safe_enum_value(self, attr_name, default=None):
        """Safely get value from enum attribute"""
        try:
            enum_val = getattr(self, attr_name, None)
            return enum_val.value if enum_val is not None else default
        except:
            return default

    def _safe_isoformat(self, attr_name):
        """Safely get isoformat from datetime attribute"""
        try:
            dt = getattr(self, attr_name, None)
            return dt.isoformat() if dt is not None else None
        except:
            return None

    def is_applicable(self, service_type=None, property_type=None, suburb=None, quantity=None):
        """Check if this rule applies to given parameters"""
        try:
            # Check if rule is active
            if not getattr(self, 'is_active', True):
                return False
            
            # Check service type match
            rule_service = getattr(self, 'service_type', None)
            if rule_service and service_type and rule_service != service_type:
                return False
            
            # Check property type match
            rule_property = getattr(self, 'property_type', None)
            if rule_property and property_type and rule_property != property_type:
                return False
            
            # Check suburb match
            rule_suburb = getattr(self, 'suburb', None)
            if rule_suburb and suburb and rule_suburb != suburb:
                return False
            
            # Check quantity range
            if quantity is not None:
                min_qty = getattr(self, 'quantity_min', None)
                max_qty = getattr(self, 'quantity_max', None)
                
                if min_qty is not None and quantity < min_qty:
                    return False
                if max_qty is not None and quantity > max_qty:
                    return False
            
            return True
        except:
            return False

    def calculate_price(self, base_amount, quantity=1):
        """Calculate price adjustment based on rule"""
        try:
            rule_type = getattr(self, 'rule_type', None)
            modifier_type = getattr(self, 'modifier_type', 'multiplier')
            modifier_value = getattr(self, 'modifier_value', 0)
            
            if rule_type == PricingRuleType.BASE_SERVICE:
                # Base service pricing
                base_price = getattr(self, 'base_price', 0)
                per_unit = getattr(self, 'per_unit_price', None)
                
                if per_unit:
                    result = base_price + (per_unit * quantity)
                else:
                    result = base_price
            else:
                # Modifier-based pricing
                if modifier_type == 'multiplier':
                    result = base_amount * modifier_value
                elif modifier_type == 'addition':
                    result = base_amount + modifier_value
                elif modifier_type == 'percentage':
                    result = base_amount * (1 + modifier_value / 100)
                else:
                    result = base_amount
            
            # Apply min/max constraints
            min_price = getattr(self, 'min_price', None)
            max_price = getattr(self, 'max_price', None)
            
            if min_price is not None:
                result = max(result, min_price)
            if max_price is not None:
                result = min(result, max_price)
            
            return round(result, 2)
        except:
            return base_amount

    def to_dict(self):
        """Convert pricing rule to dictionary"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "rule_name": getattr(self, 'rule_name', None),
                "rule_type": self._safe_enum_value('rule_type'),
                "service_type": self._safe_enum_value('service_type'),
                "property_type": self._safe_enum_value('property_type'),
                "suburb": self._safe_enum_value('suburb'),
                "base_price": getattr(self, 'base_price', None),
                "modifier_type": getattr(self, 'modifier_type', None),
                "modifier_value": getattr(self, 'modifier_value', None),
                "min_price": getattr(self, 'min_price', None),
                "max_price": getattr(self, 'max_price', None),
                "quantity_min": getattr(self, 'quantity_min', None),
                "quantity_max": getattr(self, 'quantity_max', None),
                "per_unit_price": getattr(self, 'per_unit_price', None),
                "conditions": getattr(self, 'conditions', None),
                "description": getattr(self, 'description', None),
                "is_active": getattr(self, 'is_active', True),
                "priority": getattr(self, 'priority', 0),
                "valid_from": self._safe_isoformat('valid_from'),
                "valid_to": self._safe_isoformat('valid_to'),
                "created_at": self._safe_isoformat('created_at'),
                "updated_at": self._safe_isoformat('updated_at')
            }
        except Exception as e:
            return {
                "id": getattr(self, 'id', None),
                "rule_name": getattr(self, 'rule_name', 'Error'),
                "error": str(e)
            }

    def to_summary_dict(self):
        """Convert to summary format for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "rule_name": getattr(self, 'rule_name', None),
                "rule_type": self._safe_enum_value('rule_type'),
                "service_type": self._safe_enum_value('service_type'),
                "modifier_value": getattr(self, 'modifier_value', None),
                "is_active": getattr(self, 'is_active', True),
                "description": getattr(self, 'description', None)
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "rule_name": getattr(self, 'rule_name', 'Error')
            }
