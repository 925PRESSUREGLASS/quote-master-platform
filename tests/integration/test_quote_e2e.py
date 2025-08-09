"""
Integration tests for complete quote generation workflow.
Tests the integration between pricing, AI services, and database persistence.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.ai.orchestrator import get_ai_orchestrator
from src.services.pricing_service import PricingService


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuoteGenerationIntegration:
    """Test complete quote generation workflow integration"""

    async def test_end_to_end_quote_generation(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test complete quote generation from request to response"""
        # Mock AI service to avoid external dependencies
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Professional window cleaning service for your Perth property. We provide reliable, insured service with attention to detail.",
                metadata={"provider": "test", "tokens_used": 50},
            )
            mock_orchestrator.return_value = mock_ai

            quote_request = {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "area_sqm": 120.0,
                "suburb": "Subiaco",
                "difficulty_multiplier": 1.2,
                "customer_notes": "Two-story house with some hard-to-reach windows",
                "contact_email": "customer@example.com",
                "contact_phone": "+61412345678",
            }

            response = await async_client.post(
                "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED

            quote_data = response.json()
            assert "id" in quote_data
            assert "pricing" in quote_data
            assert "quote_details" in quote_data

            # Verify pricing calculation
            pricing = quote_data["pricing"]
            assert "final_price" in pricing
            assert "gst_amount" in pricing
            assert Decimal(str(pricing["final_price"])) > 0

    async def test_pricing_service_integration(self):
        """Test pricing service calculations with realistic data"""
        pricing_service = PricingService()

        # Test residential window cleaning in premium suburb
        price = pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=100.0,
            difficulty_multiplier=1.3,
            suburb="Cottesloe",
            property_type="residential",
        )

        assert isinstance(price, Decimal)
        assert price > Decimal("100.00")  # Should be substantial for premium suburb

        # Test commercial service
        commercial_price = pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=100.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
            property_type="commercial",
        )

        # Commercial should cost more than residential
        residential_price = pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=100.0,
            difficulty_multiplier=1.0,
            suburb="Perth",
            property_type="residential",
        )

        assert commercial_price > residential_price

    async def test_suburb_multiplier_integration(self):
        """Test suburb pricing multipliers work correctly across the system"""
        from src.services.pricing_service import apply_suburb_multiplier

        base_amount = Decimal("100.00")

        # Test premium suburbs
        cottesloe_price = apply_suburb_multiplier(base_amount, "Cottesloe")
        assert cottesloe_price == Decimal("120.00")  # 20% markup

        # Test standard suburbs
        perth_price = apply_suburb_multiplier(base_amount, "Perth")
        assert perth_price == Decimal("100.00")  # No markup

        # Test outer suburbs
        joondalup_price = apply_suburb_multiplier(base_amount, "Joondalup")
        assert joondalup_price == Decimal("115.00")  # 15% markup

    async def test_multiple_services_integration(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test requesting multiple services in one quote"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Comprehensive cleaning package including windows and pressure washing.",
                metadata={"provider": "test", "tokens_used": 75},
            )
            mock_orchestrator.return_value = mock_ai

            quote_request = {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "area_sqm": 150.0,
                "suburb": "Nedlands",
                "additional_services": ["pressure_cleaning", "gutter_cleaning"],
                "contact_email": "customer@example.com",
                "contact_phone": "+61412345678",
            }

            response = await async_client.post(
                "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
            )

            assert response.status_code == status.HTTP_201_CREATED

            quote_data = response.json()
            pricing = quote_data["pricing"]

            # Should have additional services cost
            assert "additional_services_cost" in pricing
            assert Decimal(str(pricing["additional_services_cost"])) > 0

            # Total should be higher than single service
            assert Decimal(str(pricing["final_price"])) > Decimal("200.00")


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuoteStorageIntegration:
    """Test quote storage and retrieval integration"""

    async def test_quote_persistence_integration(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test that quotes are properly stored and can be retrieved"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Professional service quote for your property.",
                metadata={"provider": "test", "tokens_used": 40},
            )
            mock_orchestrator.return_value = mock_ai

            # Create quote
            quote_request = {
                "service_type": "glass_repair",
                "property_type": "residential",
                "area_sqm": 25.0,
                "suburb": "Fremantle",
                "customer_notes": "Cracked bathroom window",
                "contact_email": "test@example.com",
                "contact_phone": "+61412345678",
            }

            create_response = await async_client.post(
                "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
            )

            assert create_response.status_code == status.HTTP_201_CREATED

            created_quote = create_response.json()
            quote_id = created_quote["id"]

            # Retrieve quote
            get_response = await async_client.get(
                f"/api/v1/quotes/{quote_id}", headers=auth_headers
            )

            assert get_response.status_code == status.HTTP_200_OK

            retrieved_quote = get_response.json()
            assert retrieved_quote["id"] == quote_id
            assert retrieved_quote["service_type"] == "glass_repair"
            assert retrieved_quote["suburb"] == "Fremantle"

    async def test_quote_listing_integration(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test listing user's quotes"""
        # Create multiple quotes
        service_types = ["window_cleaning", "pressure_cleaning"]

        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Professional service quote.",
                metadata={"provider": "test", "tokens_used": 30},
            )
            mock_orchestrator.return_value = mock_ai

            created_quotes = []
            for i, service_type in enumerate(service_types):
                quote_request = {
                    "service_type": service_type,
                    "property_type": "residential",
                    "area_sqm": 100.0,
                    "suburb": "Perth",
                    "contact_email": f"test{i}@example.com",
                    "contact_phone": "+61412345678",
                }

                response = await async_client.post(
                    "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
                )

                assert response.status_code == status.HTTP_201_CREATED
                created_quotes.append(response.json()["id"])

            # List quotes
            list_response = await async_client.get(
                "/api/v1/quotes", headers=auth_headers
            )

            assert list_response.status_code == status.HTTP_200_OK

            quotes_list = list_response.json()
            quote_ids = [q["id"] for q in quotes_list]

            # Verify created quotes are in the list
            for created_id in created_quotes:
                assert created_id in quote_ids


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuoteBusinessLogicIntegration:
    """Test business logic integration across services"""

    async def test_minimum_charge_enforcement_integration(self):
        """Test that minimum charges are enforced across the system"""
        from src.services.pricing_service import calculate_final_quote

        # Very small job should still meet minimum
        quote = calculate_final_quote(
            service_type="window_cleaning", area_sqm=1.0, suburb="Perth"  # Tiny area
        )

        assert quote["final_price"] >= Decimal("50.00")  # Minimum charge

        # Glass repair minimum
        glass_quote = calculate_final_quote(
            service_type="glass_repair", area_sqm=1.0, suburb="Perth"
        )

        assert glass_quote["final_price"] >= Decimal("80.00")  # Higher minimum

    async def test_discount_calculation_integration(self):
        """Test discount calculations work correctly"""
        from src.services.pricing_service import calculate_final_quote

        # Quote without discount
        base_quote = calculate_final_quote(
            service_type="window_cleaning", area_sqm=100.0, suburb="Perth"
        )

        # Quote with 10% discount
        discounted_quote = calculate_final_quote(
            service_type="window_cleaning",
            area_sqm=100.0,
            suburb="Perth",
            discount_percent=10.0,
        )

        # Verify discount was applied
        expected_discount = base_quote["final_price"] * Decimal("0.10")
        actual_discount = discounted_quote["discount_amount"]

        assert abs(actual_discount - expected_discount) < Decimal("0.01")
        assert discounted_quote["final_price"] < base_quote["final_price"]

    async def test_gst_calculation_integration(self):
        """Test GST calculations are correct throughout the system"""
        from src.services.pricing_service import calculate_final_quote

        quote = calculate_final_quote(
            service_type="pressure_cleaning",
            area_sqm=200.0,
            suburb="Subiaco",
            difficulty_multiplier=1.1,
        )

        # Verify GST is exactly 10% of final price
        expected_gst = quote["final_price"] * Decimal("0.10")
        actual_gst = quote["gst_amount"]

        assert abs(actual_gst - expected_gst) < Decimal("0.01")

        # Verify total includes GST
        expected_total = quote["final_price"] + quote["gst_amount"]
        assert abs(quote["total_with_gst"] - expected_total) < Decimal("0.01")

    async def test_error_handling_integration(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test error handling across integrated services"""
        # Test invalid service type
        invalid_request = {
            "service_type": "invalid_service",
            "property_type": "residential",
            "area_sqm": 100.0,
            "suburb": "Perth",
            "contact_email": "test@example.com",
            "contact_phone": "+61412345678",
        }

        response = await async_client.post(
            "/api/v1/quotes/generate", json=invalid_request, headers=auth_headers
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

        # Test missing required fields
        incomplete_request = {
            "service_type": "window_cleaning"
            # Missing other required fields
        }

        response = await async_client.post(
            "/api/v1/quotes/generate", json=incomplete_request, headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
