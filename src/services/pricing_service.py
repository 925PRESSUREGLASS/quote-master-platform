"""
Pricing service for Perth glass and cleaning services.
Handles pricing calculations, suburb multipliers, and service rates.
"""

import logging
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Service types offered"""

    WINDOW_CLEANING = "window_cleaning"
    GLASS_REPAIR = "glass_repair"
    PRESSURE_CLEANING = "pressure_cleaning"
    GUTTER_CLEANING = "gutter_cleaning"
    COMBINED_SERVICE = "combined_service"


class PropertyType(str, Enum):
    """Property types"""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"


class PerthSuburbZone(str, Enum):
    """Perth suburb pricing zones"""

    ZONE_A_PREMIUM = "zone_a_premium"  # Cottesloe, Peppermint Grove, etc.
    ZONE_B_INNER = "zone_b_inner"  # Perth CBD, Subiaco, etc.
    ZONE_C_MIDDLE = "zone_c_middle"  # Nedlands, Mount Lawley, etc.
    ZONE_D_OUTER = "zone_d_outer"  # Joondalup, Rockingham, etc.


class PricingService:
    """Main pricing service for glass and cleaning services in Perth"""

    def __init__(self):
        self.base_rates = self._initialize_base_rates()
        self.suburb_multipliers = self._initialize_suburb_multipliers()

    def _initialize_base_rates(self) -> Dict[ServiceType, Dict[PropertyType, Decimal]]:
        """Initialize base rates for services by property type"""
        return {
            ServiceType.WINDOW_CLEANING: {
                PropertyType.RESIDENTIAL: Decimal("80.00"),
                PropertyType.COMMERCIAL: Decimal("150.00"),
                PropertyType.INDUSTRIAL: Decimal("200.00"),
            },
            ServiceType.GLASS_REPAIR: {
                PropertyType.RESIDENTIAL: Decimal("120.00"),
                PropertyType.COMMERCIAL: Decimal("180.00"),
                PropertyType.INDUSTRIAL: Decimal("250.00"),
            },
            ServiceType.PRESSURE_CLEANING: {
                PropertyType.RESIDENTIAL: Decimal("100.00"),
                PropertyType.COMMERCIAL: Decimal("180.00"),
                PropertyType.INDUSTRIAL: Decimal("300.00"),
            },
            ServiceType.GUTTER_CLEANING: {
                PropertyType.RESIDENTIAL: Decimal("140.00"),
                PropertyType.COMMERCIAL: Decimal("220.00"),
                PropertyType.INDUSTRIAL: Decimal("350.00"),
            },
            ServiceType.COMBINED_SERVICE: {
                PropertyType.RESIDENTIAL: Decimal("250.00"),
                PropertyType.COMMERCIAL: Decimal("400.00"),
                PropertyType.INDUSTRIAL: Decimal("600.00"),
            },
        }

    def _initialize_suburb_multipliers(self) -> Dict[str, Decimal]:
        """Initialize Perth suburb pricing multipliers (case-insensitive)"""
        return {
            # Zone A - Premium suburbs (20% markup)
            "cottesloe": Decimal("1.20"),
            "peppermint grove": Decimal("1.20"),
            "dalkeith": Decimal("1.20"),
            "mosman park": Decimal("1.15"),
            # Zone B - Inner suburbs (5-10% markup)
            "subiaco": Decimal("1.10"),
            "leederville": Decimal("1.08"),
            "west perth": Decimal("1.05"),
            "northbridge": Decimal("1.05"),
            # Zone C - Middle suburbs (standard rate)
            "perth": Decimal("1.00"),
            "mount lawley": Decimal("1.05"),
            "nedlands": Decimal("1.10"),
            "claremont": Decimal("1.08"),
            "fremantle": Decimal("1.05"),
            # Zone D - Outer suburbs (distance surcharge)
            "joondalup": Decimal("1.15"),
            "rockingham": Decimal("1.15"),
            "mandurah": Decimal("1.20"),
            "armadale": Decimal("1.12"),
            "midland": Decimal("1.12"),
        }

    def get_service_base_rate(
        self, service_type: str, property_type: str = "residential"
    ) -> Decimal:
        """Get base rate for a service type"""
        try:
            service_enum = ServiceType(service_type)
            property_enum = PropertyType(property_type)

            return self.base_rates[service_enum][property_enum]
        except (ValueError, KeyError):
            raise ValueError(
                f"Invalid service type '{service_type}' or property type '{property_type}'"
            )

    def calculate_price(
        self,
        service_type: str,
        area_sqm: float,
        difficulty_multiplier: float = 1.0,
        suburb: str = "Perth",
        property_type: str = "residential",
        additional_services: Optional[List[str]] = None,
    ) -> Decimal:
        """Calculate final price for service"""
        if area_sqm < 0:
            raise ValueError("Area cannot be negative")

        if area_sqm == 0:
            return Decimal("0")

        # Get base rate
        base_rate = self.get_service_base_rate(service_type, property_type)

        # Calculate area-based pricing
        base_price = base_rate * Decimal(str(area_sqm / 50.0))  # $base per 50 sqm

        # Apply difficulty multiplier
        adjusted_price = base_price * Decimal(str(difficulty_multiplier))

        # Apply suburb multiplier
        final_price = apply_suburb_multiplier(adjusted_price, suburb)

        # Add additional services
        if additional_services:
            for additional_service in additional_services:
                try:
                    additional_rate = self.get_service_base_rate(
                        additional_service, property_type
                    )
                    final_price += additional_rate * Decimal(
                        "0.5"
                    )  # 50% rate for additional services
                except ValueError:
                    # Skip unknown additional services
                    continue

        return final_price


def calculate_base_price(service_type: str, area_sqm: float) -> Decimal:
    """Calculate base price for service without adjustments"""
    if area_sqm < 0:
        raise ValueError("Area cannot be negative")

    if area_sqm == 0:
        return Decimal("0")

    pricing_service = PricingService()

    if service_type not in [s.value for s in ServiceType]:
        raise ValueError(f"Invalid service type: {service_type}")

    base_rate = pricing_service.get_service_base_rate(service_type)
    return base_rate * Decimal(str(area_sqm / 50.0))


def apply_suburb_multiplier(base_amount: Decimal, suburb: str) -> Decimal:
    """Apply Perth suburb pricing multiplier"""
    pricing_service = PricingService()

    # Normalize suburb name (lowercase, strip whitespace)
    suburb_normalized = suburb.lower().strip()

    # Get multiplier (default to Perth rate if not found)
    multiplier = pricing_service.suburb_multipliers.get(
        suburb_normalized, Decimal("1.00")
    )

    return base_amount * multiplier


def calculate_final_quote(
    service_type: str,
    area_sqm: float,
    difficulty_multiplier: float = 1.0,
    suburb: str = "Perth",
    additional_services: Optional[List[str]] = None,
    discount_percent: float = 0.0,
) -> Dict[str, Any]:
    """Calculate complete quote with breakdown"""

    if discount_percent < 0:
        raise ValueError("Discount percentage cannot be negative")

    if difficulty_multiplier <= 0:
        raise ValueError("Difficulty multiplier must be greater than zero")

    # Cap discount at 50%
    if discount_percent > 50:
        discount_percent = 50.0

    pricing_service = PricingService()

    # Calculate base price
    base_price = calculate_base_price(service_type, area_sqm)

    # Apply minimum charge
    minimum_charges = {
        "window_cleaning": Decimal("50.00"),
        "glass_repair": Decimal("80.00"),
        "pressure_cleaning": Decimal("100.00"),
        "gutter_cleaning": Decimal("120.00"),
    }

    min_charge = minimum_charges.get(service_type, Decimal("50.00"))
    base_price = max(base_price, min_charge)

    # Apply suburb multiplier
    suburb_multiplier = pricing_service.suburb_multipliers.get(
        suburb.lower().strip(), Decimal("1.00")
    )
    suburb_adjusted_price = base_price * suburb_multiplier

    # Apply difficulty multiplier
    difficulty_adjusted_price = suburb_adjusted_price * Decimal(
        str(difficulty_multiplier)
    )

    # Calculate additional services cost
    additional_services_cost = Decimal("0")
    if additional_services:
        for service in additional_services:
            try:
                service_rate = pricing_service.get_service_base_rate(service)
                additional_services_cost += service_rate * Decimal(
                    "0.3"
                )  # 30% rate for add-ons
            except ValueError:
                continue

    # Calculate subtotal
    subtotal = difficulty_adjusted_price + additional_services_cost

    # Apply discount
    discount_amount = subtotal * Decimal(str(discount_percent / 100))
    final_price = subtotal - discount_amount

    # Calculate GST (10%)
    gst_amount = final_price * Decimal("0.10")
    total_with_gst = final_price + gst_amount

    # Round all amounts to 2 decimal places
    return {
        "base_price": base_price.quantize(Decimal("0.01")),
        "suburb_multiplier": float(suburb_multiplier),
        "difficulty_adjustment": float(difficulty_multiplier),
        "additional_services_cost": additional_services_cost.quantize(Decimal("0.01")),
        "discount_amount": discount_amount.quantize(Decimal("0.01")),
        "final_price": final_price.quantize(Decimal("0.01")),
        "gst_amount": gst_amount.quantize(Decimal("0.01")),
        "total_with_gst": total_with_gst.quantize(Decimal("0.01")),
    }
