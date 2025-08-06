"""
Pricing Engine for Window & Pressure Cleaning Services
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio

from src.models.service_quote import ServiceType, PropertyType, PerthSuburb, ServiceQuote
from src.models.pricing_rule import PricingRule, PricingRuleType
from src.services.ai.orchestrator import get_ai_orchestrator
from src.services.ai.base import AIRequest, AITaskType
from src.core.config import get_settings
from src.core.exceptions import QuoteGenerationException
from src.core.database import get_db_session

logger = logging.getLogger(__name__)
settings = get_settings()


class ServiceComplexity(str, Enum):
    """Service complexity levels for pricing"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPLEX = "complex"
    PREMIUM = "premium"


class PricingEngine:
    """Main pricing engine for service quotes"""
    
    def __init__(self):
        self.ai_orchestrator = get_ai_orchestrator()
    
    def calculate_service_quote(
        self,
        service_type: ServiceType,
        property_type: PropertyType,
        suburb: PerthSuburb,
        window_count: Optional[int] = None,
        square_meters: Optional[float] = None,
        storeys: int = 1,
        access_difficulty: str = "easy",
        customer_notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive service quote with pricing breakdown
        """
        try:
            # Step 1: Get base pricing from rules
            base_price = self._get_base_price(service_type, property_type)
            
            # Step 2: Calculate quantity-based pricing
            quantity_price = self._calculate_quantity_pricing(
                service_type, window_count, square_meters
            )
            
            # Step 3: Apply location adjustments
            location_adjustment = self._get_location_adjustment(suburb)
            
            # Step 4: Apply complexity adjustments
            complexity_adjustment = self._get_complexity_adjustment(
                access_difficulty, storeys, property_type
            )
            
            # Step 5: Calculate final price
            subtotal = base_price + quantity_price
            location_adjusted = subtotal * location_adjustment
            final_price = location_adjusted * complexity_adjustment
            
            # Step 6: Generate quote details
            quote_details = self._generate_quote_details(
                service_type, property_type, suburb, final_price,
                window_count, square_meters, customer_notes
            )
            
            # Step 7: Create pricing breakdown
            breakdown = {
                "base_price": base_price,
                "quantity_price": quantity_price,
                "subtotal": subtotal,
                "location_adjustment": {
                    "factor": location_adjustment,
                    "amount": location_adjusted - subtotal
                },
                "complexity_adjustment": {
                    "factor": complexity_adjustment,
                    "amount": final_price - location_adjusted
                },
                "final_price": round(final_price, 2)
            }
            
            return {
                "pricing": breakdown,
                "quote_details": quote_details,
                "service_specifications": {
                    "service_type": service_type.value,
                    "property_type": property_type.value,
                    "suburb": suburb.value,
                    "window_count": window_count,
                    "square_meters": square_meters,
                    "storeys": storeys,
                    "access_difficulty": access_difficulty
                },
                "validity": {
                    "valid_until": (datetime.now() + timedelta(days=30)).isoformat(),
                    "quote_number": self._generate_quote_number()
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating service quote: {str(e)}")
            raise QuoteGenerationException(f"Failed to calculate service quote: {str(e)}")
    
    def _get_base_price(self, service_type: ServiceType, property_type: PropertyType) -> float:
        """Get base price for service type and property type"""
        try:
            # Default pricing structure
            base_prices = {
                ServiceType.WINDOW_CLEANING: {
                    PropertyType.RESIDENTIAL_HOUSE: 120.0,
                    PropertyType.RESIDENTIAL_UNIT: 80.0,
                    PropertyType.COMMERCIAL_OFFICE: 200.0,
                    PropertyType.COMMERCIAL_RETAIL: 150.0,
                    PropertyType.INDUSTRIAL: 300.0,
                    PropertyType.STRATA_COMPLEX: 180.0
                },
                ServiceType.PRESSURE_WASHING: {
                    PropertyType.RESIDENTIAL_HOUSE: 150.0,
                    PropertyType.RESIDENTIAL_UNIT: 100.0,
                    PropertyType.COMMERCIAL_OFFICE: 250.0,
                    PropertyType.COMMERCIAL_RETAIL: 200.0,
                    PropertyType.INDUSTRIAL: 400.0,
                    PropertyType.STRATA_COMPLEX: 220.0
                },
                ServiceType.GUTTER_CLEANING: {
                    PropertyType.RESIDENTIAL_HOUSE: 180.0,
                    PropertyType.RESIDENTIAL_UNIT: 120.0,
                    PropertyType.COMMERCIAL_OFFICE: 300.0,
                    PropertyType.COMMERCIAL_RETAIL: 250.0,
                    PropertyType.INDUSTRIAL: 500.0,
                    PropertyType.STRATA_COMPLEX: 280.0
                },
                ServiceType.COMBINED_SERVICE: {
                    PropertyType.RESIDENTIAL_HOUSE: 280.0,
                    PropertyType.RESIDENTIAL_UNIT: 200.0,
                    PropertyType.COMMERCIAL_OFFICE: 450.0,
                    PropertyType.COMMERCIAL_RETAIL: 380.0,
                    PropertyType.INDUSTRIAL: 750.0,
                    PropertyType.STRATA_COMPLEX: 420.0
                }
            }
            
            return base_prices.get(service_type, {}).get(property_type, 100.0)
            
        except Exception:
            return 100.0  # Fallback base price
    
    def _calculate_quantity_pricing(
        self, 
        service_type: ServiceType, 
        window_count: Optional[int], 
        square_meters: Optional[float]
    ) -> float:
        """Calculate additional pricing based on quantity"""
        try:
            if service_type == ServiceType.WINDOW_CLEANING and window_count:
                # Additional windows beyond base (first 10 included)
                base_windows = 10
                if window_count > base_windows:
                    additional_windows = window_count - base_windows
                    return additional_windows * 8.0  # $8 per additional window
            
            elif service_type in [ServiceType.PRESSURE_WASHING, ServiceType.DRIVEWAY_CLEANING] and square_meters:
                # Additional square meters beyond base (first 50sqm included)
                base_sqm = 50.0
                if square_meters > base_sqm:
                    additional_sqm = square_meters - base_sqm
                    return additional_sqm * 3.5  # $3.50 per additional sqm
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _get_location_adjustment(self, suburb: PerthSuburb) -> float:
        """Get pricing adjustment factor based on suburb"""
        try:
            # Premium suburbs (Zone A - 20% markup)
            premium_suburbs = [
                PerthSuburb.COTTESLOE, PerthSuburb.PEPPERMINT_GROVE,
                PerthSuburb.MOSMAN_PARK, PerthSuburb.NEDLANDS, PerthSuburb.DALKEITH
            ]
            
            # Outer suburbs (Zone D - 15% surcharge for distance)
            outer_suburbs = [
                PerthSuburb.JOONDALUP, PerthSuburb.ROCKINGHAM, PerthSuburb.MANDURAH
            ]
            
            if suburb in premium_suburbs:
                return 1.2  # 20% markup
            elif suburb in outer_suburbs:
                return 1.15  # 15% distance surcharge
            else:
                return 1.0  # Standard pricing
                
        except Exception:
            return 1.0
    
    def _get_complexity_adjustment(
        self, 
        access_difficulty: str, 
        storeys: int, 
        property_type: PropertyType
    ) -> float:
        """Get pricing adjustment based on job complexity"""
        try:
            base_multiplier = 1.0
            
            # Access difficulty adjustment
            difficulty_multipliers = {
                "easy": 1.0,
                "medium": 1.15,
                "hard": 1.3,
                "extreme": 1.5
            }
            base_multiplier *= difficulty_multipliers.get(access_difficulty, 1.0)
            
            # Height adjustment
            if storeys > 1:
                base_multiplier *= (1.0 + (storeys - 1) * 0.1)  # 10% per additional storey
            
            # Property type complexity
            if property_type in [PropertyType.INDUSTRIAL, PropertyType.COMMERCIAL_OFFICE]:
                base_multiplier *= 1.1  # 10% commercial complexity
            
            return base_multiplier
            
        except Exception:
            return 1.0
    
    def _generate_quote_details(
        self,
        service_type: ServiceType,
        property_type: PropertyType,
        suburb: PerthSuburb,
        final_price: float,
        window_count: Optional[int] = None,
        square_meters: Optional[float] = None,
        customer_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive quote details using AI"""
        try:
            # Create context for AI quote generation
            context = {
                "service_type": service_type.value.replace('_', ' ').title(),
                "property_type": property_type.value.replace('_', ' ').title(),
                "suburb": suburb.value.replace('_', ' ').title(),
                "price": f"${final_price:.2f}",
                "window_count": window_count,
                "square_meters": square_meters,
                "customer_notes": customer_notes
            }
            
            # Generate AI-powered quote content
            prompt = self._build_quote_prompt(context)
            
            if self.ai_orchestrator:
                try:
                    # Create AI request
                    ai_request = AIRequest(
                        task_type=AITaskType.QUOTE_GENERATION,
                        prompt=prompt,
                        max_tokens=500,
                        temperature=0.7
                    )
                    
                    # Note: In production, this should be handled asynchronously
                    # For now, we'll use the fallback approach
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    ai_response = loop.run_until_complete(
                        self.ai_orchestrator.generate_text(ai_request)
                    )
                    loop.close()
                    
                    quote_content = ai_response.content if ai_response and ai_response.success else self._generate_fallback_quote(context)
                except Exception as e:
                    logger.warning(f"AI generation failed, using fallback: {e}")
                    quote_content = self._generate_fallback_quote(context)
            else:
                quote_content = self._generate_fallback_quote(context)
            
            return {
                "quote_text": quote_content,
                "inclusions": self._get_service_inclusions(service_type),
                "exclusions": self._get_service_exclusions(service_type),
                "terms_conditions": self._get_terms_conditions(),
                "payment_terms": "Payment due within 7 days of service completion",
                "warranty": self._get_warranty_terms(service_type)
            }
            
        except Exception as e:
            logger.warning(f"Failed to generate AI quote details: {e}")
            return self._generate_fallback_quote_details(service_type, final_price)
    
    def _build_quote_prompt(self, context: Dict[str, Any]) -> str:
        """Build AI prompt for quote generation"""
        return f"""
        Generate a professional and friendly service quote for a window and pressure cleaning business in Perth, Western Australia.

        Service Details:
        - Service: {context['service_type']}
        - Property Type: {context['property_type']}
        - Location: {context['suburb']}, WA
        - Quote Price: {context['price']}
        {f"- Number of Windows: {context['window_count']}" if context.get('window_count') else ""}
        {f"- Area: {context['square_meters']} square meters" if context.get('square_meters') else ""}
        {f"- Special Requirements: {context['customer_notes']}" if context.get('customer_notes') else ""}

        Generate a quote that includes:
        1. A warm, professional greeting
        2. Service description highlighting quality and reliability
        3. Emphasis on being fully insured and professional
        4. Local Perth knowledge and community focus
        5. Trustworthy and customer-focused tone
        6. Clear value proposition
        
        Keep the tone friendly but professional, and make it feel personal and trustworthy.
        Maximum 300 words.
        """
    
    def _generate_fallback_quote(self, context: Dict[str, Any]) -> str:
        """Generate fallback quote when AI is unavailable"""
        return f"""
        Thank you for your interest in our {context['service_type'].lower()} services!

        We're pleased to provide you with a competitive quote for your {context['property_type'].lower()} in {context['suburb']}.

        Our team of experienced professionals will ensure your property receives the highest quality service. We use professional-grade equipment and eco-friendly cleaning solutions to deliver exceptional results.

        As a fully insured Perth-based business, we take pride in our attention to detail and commitment to customer satisfaction. We've been serving the Perth community for years and understand the unique challenges of maintaining properties in our beautiful city.

        Your quoted price of {context['price']} includes all labour, equipment, and materials required for the job.
        
        We look forward to the opportunity to exceed your expectations!
        """
    
    def _get_service_inclusions(self, service_type: ServiceType) -> List[str]:
        """Get list of what's included in the service"""
        inclusions = {
            ServiceType.WINDOW_CLEANING: [
                "Internal and external window cleaning",
                "Window sill and frame cleaning", 
                "Screen cleaning (if applicable)",
                "Professional squeegee finish",
                "Eco-friendly cleaning products",
                "Fully insured service"
            ],
            ServiceType.PRESSURE_WASHING: [
                "High-pressure cleaning of specified areas",
                "Pre-treatment of stained areas",
                "Professional-grade equipment",
                "Water-efficient cleaning methods",
                "Post-cleaning inspection",
                "Fully insured service"
            ],
            ServiceType.GUTTER_CLEANING: [
                "Complete gutter and downpipe cleaning",
                "Removal of all debris",
                "Basic gutter inspection",
                "Disposal of waste materials",
                "Safety equipment and procedures",
                "Fully insured service"
            ]
        }
        
        return inclusions.get(service_type, ["Professional service", "Fully insured"])
    
    def _get_service_exclusions(self, service_type: ServiceType) -> List[str]:
        """Get list of what's excluded from the service"""
        exclusions = {
            ServiceType.WINDOW_CLEANING: [
                "Repair of broken windows or screens",
                "Cleaning of windows above 3 stories without proper access",
                "Removal of paint or permanent stains",
                "Interior furniture moving"
            ],
            ServiceType.PRESSURE_WASHING: [
                "Repair of damaged surfaces",
                "Treatment of oil stains (additional charge)",
                "Sealing or painting services",
                "Garden maintenance or landscaping"
            ],
            ServiceType.GUTTER_CLEANING: [
                "Gutter repairs or replacement",
                "Roof cleaning or maintenance",
                "Installation of gutter guards",
                "Structural modifications"
            ]
        }
        
        return exclusions.get(service_type, ["Repairs or modifications not included"])
    
    def _get_terms_conditions(self) -> str:
        """Get standard terms and conditions"""
        return """
        1. Quote valid for 30 days from issue date.
        2. Weather dependent - service may be rescheduled for safety.
        3. Clear access to work areas required.
        4. Payment due within 7 days of service completion.
        5. Additional charges may apply for work beyond scope.
        6. Customer satisfaction guarantee - we'll make it right.
        """
    
    def _get_warranty_terms(self, service_type: ServiceType) -> str:
        """Get warranty terms for service"""
        warranties = {
            ServiceType.WINDOW_CLEANING: "7-day satisfaction guarantee on all window cleaning services",
            ServiceType.PRESSURE_WASHING: "14-day satisfaction guarantee on pressure washing services", 
            ServiceType.GUTTER_CLEANING: "30-day guarantee against blockage recurrence"
        }
        
        return warranties.get(service_type, "Customer satisfaction guarantee")
    
    def _generate_quote_number(self) -> str:
        """Generate unique quote number"""
        timestamp = int(datetime.now().timestamp())
        year = datetime.now().year
        return f"Q{year}-{str(timestamp)[-6:]}"
    
    def _generate_fallback_quote_details(self, service_type: ServiceType, price: float) -> Dict[str, Any]:
        """Generate fallback quote details when AI fails"""
        return {
            "quote_text": f"Professional {service_type.value.replace('_', ' ')} service quote for ${price:.2f}",
            "inclusions": self._get_service_inclusions(service_type),
            "exclusions": self._get_service_exclusions(service_type),
            "terms_conditions": self._get_terms_conditions(),
            "payment_terms": "Payment due within 7 days of service completion",
            "warranty": self._get_warranty_terms(service_type)
        }


def get_pricing_engine() -> PricingEngine:
    """Get singleton instance of pricing engine"""
    return PricingEngine()
