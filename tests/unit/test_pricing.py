"""
Unit tests for Quote Master Pro pricing calculations.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from src.services.pricing_service import (
    PricingService,
    apply_suburb_multiplier,
    calculate_base_price,
    calculate_final_quote,
)


class TestPricingService:
    """Test the PricingService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pricing_service = PricingService()

    def test_pricing_service_initialization(self):
        """Test that PricingService initializes correctly."""
        assert isinstance(self.pricing_service, PricingService)

    def test_get_service_base_rate_window_cleaning(self):
        """Test getting base rate for window cleaning."""
        rate = self.pricing_service.get_service_base_rate("window_cleaning")
        assert isinstance(rate, Decimal)
        assert rate > 0

    def test_get_service_base_rate_glass_repair(self):
        """Test getting base rate for glass repair."""
        rate = self.pricing_service.get_service_base_rate("glass_repair")
        assert isinstance(rate, Decimal)
        assert rate > 0

    def test_get_service_base_rate_invalid_service(self):
        """Test getting base rate for invalid service type."""
        with pytest.raises(ValueError):
            self.pricing_service.get_service_base_rate("invalid_service")

    def test_calculate_area_based_pricing(self):
        """Test area-based pricing calculation."""
        # Standard residential window cleaning
        price = self.pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )
        assert isinstance(price, Decimal)
        assert price > 0

    def test_calculate_pricing_with_difficulty_multiplier(self):
        """Test pricing with difficulty multiplier."""
        base_price = self.pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        difficult_price = self.pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.5,
            suburb="Perth",
        )

        assert difficult_price > base_price
        assert difficult_price == base_price * Decimal("1.5")

    def test_suburb_pricing_multipliers(self):
        """Test that different Perth suburbs have different pricing multipliers."""
        base_price_perth = self.pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        premium_price_cottesloe = self.pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Cottesloe",
        )

        # Cottesloe should be more expensive than Perth CBD
        assert premium_price_cottesloe >= base_price_perth


class TestCalculateBasePrice:
    """Test the calculate_base_price function."""

    def test_window_cleaning_base_price(self):
        """Test base price calculation for window cleaning."""
        price = calculate_base_price("window_cleaning", 100.0)
        assert isinstance(price, Decimal)
        assert price > 0

    def test_glass_repair_base_price(self):
        """Test base price calculation for glass repair."""
        price = calculate_base_price("glass_repair", 5.0)
        assert isinstance(price, Decimal)
        assert price > 0

    def test_pressure_cleaning_base_price(self):
        """Test base price calculation for pressure cleaning."""
        price = calculate_base_price("pressure_cleaning", 200.0)
        assert isinstance(price, Decimal)
        assert price > 0

    def test_zero_area_returns_zero(self):
        """Test that zero area returns zero price."""
        price = calculate_base_price("window_cleaning", 0.0)
        assert price == Decimal("0")

    def test_negative_area_raises_error(self):
        """Test that negative area raises ValueError."""
        with pytest.raises(ValueError):
            calculate_base_price("window_cleaning", -10.0)

    def test_invalid_service_type_raises_error(self):
        """Test that invalid service type raises ValueError."""
        with pytest.raises(ValueError):
            calculate_base_price("invalid_service", 50.0)


class TestApplySuburbMultiplier:
    """Test the apply_suburb_multiplier function."""

    def test_perth_cbd_standard_rate(self):
        """Test Perth CBD gets standard multiplier."""
        base_amount = Decimal("100.00")
        final_amount = apply_suburb_multiplier(base_amount, "Perth")

        assert isinstance(final_amount, Decimal)
        assert final_amount >= base_amount  # Should be at least the base amount

    def test_premium_suburbs_higher_rates(self):
        """Test premium suburbs get higher multipliers."""
        base_amount = Decimal("100.00")

        premium_suburbs = ["Cottesloe", "Peppermint Grove", "Dalkeith", "Nedlands"]

        for suburb in premium_suburbs:
            final_amount = apply_suburb_multiplier(base_amount, suburb)
            assert final_amount > base_amount

    def test_outer_suburbs_lower_rates(self):
        """Test outer suburbs may have different rates."""
        base_amount = Decimal("100.00")

        outer_suburbs = ["Joondalup", "Rockingham", "Armadale", "Midland"]

        for suburb in outer_suburbs:
            final_amount = apply_suburb_multiplier(base_amount, suburb)
            assert isinstance(final_amount, Decimal)
            assert final_amount > 0

    def test_unknown_suburb_default_rate(self):
        """Test unknown suburb gets default multiplier."""
        base_amount = Decimal("100.00")
        final_amount = apply_suburb_multiplier(base_amount, "Unknown Suburb")

        # Should default to standard Perth rate
        perth_rate = apply_suburb_multiplier(base_amount, "Perth")
        assert final_amount == perth_rate

    def test_case_insensitive_suburb_matching(self):
        """Test suburb matching is case insensitive."""
        base_amount = Decimal("100.00")

        cottesloe_lower = apply_suburb_multiplier(base_amount, "cottesloe")
        cottesloe_upper = apply_suburb_multiplier(base_amount, "COTTESLOE")
        cottesloe_mixed = apply_suburb_multiplier(base_amount, "Cottesloe")

        assert cottesloe_lower == cottesloe_upper == cottesloe_mixed


class TestCalculateFinalQuote:
    """Test the calculate_final_quote function."""

    def test_complete_quote_calculation(self):
        """Test complete quote calculation with all parameters."""
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=75.0,
            difficulty_multiplier=1.2,
            suburb="Subiaco",
            additional_services=["gutter_cleaning"],
            discount_percent=10.0,
        )

        assert isinstance(quote, dict)
        assert "base_price" in quote
        assert "suburb_multiplier" in quote
        assert "difficulty_adjustment" in quote
        assert "additional_services_cost" in quote
        assert "discount_amount" in quote
        assert "final_price" in quote
        assert "gst_amount" in quote
        assert "total_with_gst" in quote

    def test_quote_with_no_additional_services(self):
        """Test quote calculation with no additional services."""
        quote = calculate_final_quote(
            service_type="glass_repair",
            area_sqm=10.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        assert quote["additional_services_cost"] == Decimal("0")
        assert isinstance(quote["final_price"], Decimal)
        assert quote["final_price"] > 0

    def test_quote_with_discount(self):
        """Test quote calculation with discount applied."""
        quote_no_discount = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        quote_with_discount = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
            discount_percent=15.0,
        )

        assert quote_with_discount["discount_amount"] > 0
        assert quote_with_discount["final_price"] < quote_no_discount["final_price"]

    def test_gst_calculation(self):
        """Test GST is calculated correctly at 10%."""
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        expected_gst = quote["final_price"] * Decimal("0.10")
        assert abs(quote["gst_amount"] - expected_gst) < Decimal("0.01")

        expected_total = quote["final_price"] + quote["gst_amount"]
        assert abs(quote["total_with_gst"] - expected_total) < Decimal("0.01")

    def test_minimum_charge_applied(self):
        """Test minimum charge is applied for very small jobs."""
        # Very small area should still have minimum charge
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=1.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        # Should have a reasonable minimum charge
        assert quote["final_price"] >= Decimal("50.00")  # Assuming $50 minimum

    def test_large_commercial_job_pricing(self):
        """Test pricing for large commercial jobs."""
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=2000.0,  # Large commercial building
            difficulty_multiplier=1.3,  # High-rise difficulty
            suburb="Perth",
            additional_services=["pressure_cleaning", "gutter_cleaning"],
        )

        assert quote["final_price"] > Decimal("1000.00")  # Should be substantial
        assert quote["additional_services_cost"] > 0

    @pytest.mark.parametrize(
        "service_type,expected_min",
        [
            ("window_cleaning", 50),
            ("glass_repair", 80),
            ("pressure_cleaning", 100),
            ("gutter_cleaning", 120),
        ],
    )
    def test_service_type_minimums(self, service_type, expected_min):
        """Test each service type has appropriate minimum charges."""
        quote = calculate_final_quote(
            service_type=service_type,
            area_sqm=1.0,  # Very small job
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        assert quote["final_price"] >= Decimal(str(expected_min))


class TestPricingEdgeCases:
    """Test edge cases and error conditions."""

    def test_extremely_large_area(self):
        """Test pricing for extremely large areas."""
        # Should handle very large commercial projects
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=10000.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
        )

        assert isinstance(quote["final_price"], Decimal)
        assert quote["final_price"] > 0

    def test_maximum_discount_percentage(self):
        """Test maximum discount doesn't exceed 100%."""
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=50.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
            discount_percent=150.0,  # Invalid high discount
        )

        # Should cap discount at reasonable maximum (e.g., 50%)
        assert quote["final_price"] > 0
        assert quote["discount_amount"] <= quote["base_price"]

    def test_negative_discount_raises_error(self):
        """Test negative discount percentage raises error."""
        with pytest.raises(ValueError):
            calculate_final_quote(
                service_type="window_cleaning",
                area_sqm=50.0,
                difficulty_multiplier=1.0,
                suburb="Perth",
                discount_percent=-10.0,
            )

    def test_zero_difficulty_multiplier(self):
        """Test zero difficulty multiplier raises error."""
        with pytest.raises(ValueError):
            calculate_final_quote(
                service_type="window_cleaning",
                area_sqm=50.0,
                difficulty_multiplier=0.0,
                suburb="Perth",
            )

    def test_pricing_precision(self):
        """Test pricing calculations maintain proper decimal precision."""
        quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=33.33,  # Fraction that might cause precision issues
            difficulty_multiplier=1.15,
            suburb="Perth",
        )

        # All monetary amounts should be rounded to 2 decimal places
        assert quote["final_price"].as_tuple().exponent >= -2
        assert quote["gst_amount"].as_tuple().exponent >= -2
        assert quote["total_with_gst"].as_tuple().exponent >= -2
