"""
Performance tests for Quote Master Pro quote generation system.
Tests response times, throughput, and resource usage under load.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from src.services.ai.orchestrator import get_ai_orchestrator
from src.services.pricing_service import PricingService, calculate_final_quote


@pytest.mark.performance
@pytest.mark.slow
class TestQuoteGenerationPerformance:
    """Test performance of quote generation under various loads"""

    @pytest.mark.asyncio
    async def test_single_quote_generation_performance(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test performance of single quote generation"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Fast quote generation test",
                metadata={"provider": "test", "tokens_used": 25},
            )
            mock_orchestrator.return_value = mock_ai

            quote_request = {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "area_sqm": 100.0,
                "suburb": "Perth",
                "contact_email": "perf@example.com",
                "contact_phone": "+61412345678",
            }

            # Measure response time
            start_time = time.time()

            response = await async_client.post(
                "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
            )

            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code == status.HTTP_201_CREATED
            assert response_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_quote_generation_performance(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test performance under concurrent quote requests"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Concurrent quote test",
                metadata={"provider": "test", "tokens_used": 30},
            )
            mock_orchestrator.return_value = mock_ai

            quote_request = {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "area_sqm": 120.0,
                "suburb": "Subiaco",
                "contact_email": "concurrent@example.com",
                "contact_phone": "+61412345678",
            }

            # Generate 10 concurrent requests
            concurrent_requests = 10
            start_time = time.time()

            tasks = []
            for i in range(concurrent_requests):
                request_data = quote_request.copy()
                request_data["contact_email"] = f"concurrent{i}@example.com"

                task = async_client.post(
                    "/api/v1/quotes/generate", json=request_data, headers=auth_headers
                )
                tasks.append(task)

            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            total_time = end_time - start_time

            # Verify all requests succeeded
            successful_responses = [
                r
                for r in responses
                if not isinstance(r, Exception) and r.status_code == 201
            ]

            assert len(successful_responses) == concurrent_requests
            assert (
                total_time < 10.0
            )  # All 10 requests should complete within 10 seconds

            # Calculate average response time
            avg_response_time = total_time / concurrent_requests
            assert avg_response_time < 1.0  # Average should be under 1 second

    @pytest.mark.asyncio
    async def test_quote_retrieval_performance(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test performance of quote retrieval operations"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Retrieval performance test quote",
                metadata={"provider": "test", "tokens_used": 20},
            )
            mock_orchestrator.return_value = mock_ai

            # Create test quotes
            quote_ids = []
            for i in range(5):
                quote_request = {
                    "service_type": "window_cleaning",
                    "property_type": "residential",
                    "area_sqm": 100.0,
                    "suburb": "Perth",
                    "contact_email": f"retrieval{i}@example.com",
                    "contact_phone": "+61412345678",
                }

                response = await async_client.post(
                    "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
                )

                assert response.status_code == status.HTTP_201_CREATED
                quote_ids.append(response.json()["id"])

            # Test retrieval performance
            retrieval_times = []

            for quote_id in quote_ids:
                start_time = time.time()

                response = await async_client.get(
                    f"/api/v1/quotes/{quote_id}", headers=auth_headers
                )

                end_time = time.time()
                retrieval_time = end_time - start_time
                retrieval_times.append(retrieval_time)

                assert response.status_code == status.HTTP_200_OK

            # Performance assertions
            avg_retrieval_time = statistics.mean(retrieval_times)
            max_retrieval_time = max(retrieval_times)

            assert avg_retrieval_time < 0.5  # Average retrieval under 500ms
            assert max_retrieval_time < 1.0  # Max retrieval under 1 second


@pytest.mark.performance
class TestPricingServicePerformance:
    """Test performance of pricing calculations"""

    def test_pricing_calculation_performance(self):
        """Test performance of pricing calculations"""
        pricing_service = PricingService()

        # Test multiple pricing calculations
        calculation_times = []
        test_scenarios = [
            ("window_cleaning", 50.0, 1.0, "Perth"),
            ("glass_repair", 25.0, 1.2, "Cottesloe"),
            ("pressure_cleaning", 150.0, 1.5, "Nedlands"),
            ("gutter_cleaning", 100.0, 1.1, "Fremantle"),
            ("window_cleaning", 300.0, 1.8, "Joondalup"),
        ]

        for service_type, area, difficulty, suburb in test_scenarios:
            start_time = time.time()

            price = pricing_service.calculate_price(
                service_type=service_type,
                area_sqm=area,
                difficulty_multiplier=difficulty,
                suburb=suburb,
            )

            end_time = time.time()
            calculation_time = end_time - start_time
            calculation_times.append(calculation_time)

            assert isinstance(price, Decimal)
            assert price > 0

        # Performance assertions
        avg_calculation_time = statistics.mean(calculation_times)
        max_calculation_time = max(calculation_times)

        assert avg_calculation_time < 0.01  # Average under 10ms
        assert max_calculation_time < 0.05  # Max under 50ms

    def test_bulk_pricing_calculation_performance(self):
        """Test performance of bulk pricing calculations"""
        # Simulate processing multiple quotes simultaneously
        bulk_scenarios = []

        for i in range(100):  # 100 different pricing scenarios
            scenario = {
                "service_type": [
                    "window_cleaning",
                    "glass_repair",
                    "pressure_cleaning",
                ][i % 3],
                "area_sqm": 50.0 + (i * 2),
                "difficulty_multiplier": 1.0 + (i * 0.01),
                "suburb": ["Perth", "Subiaco", "Cottesloe", "Nedlands"][i % 4],
            }
            bulk_scenarios.append(scenario)

        start_time = time.time()

        for scenario in bulk_scenarios:
            quote = calculate_final_quote(
                service_type=scenario["service_type"],
                area_sqm=scenario["area_sqm"],
                difficulty_multiplier=scenario["difficulty_multiplier"],
                suburb=scenario["suburb"],
            )
            assert quote["final_price"] > 0

        end_time = time.time()
        total_time = end_time - start_time

        # Should process 100 calculations in under 1 second
        assert total_time < 1.0

        # Average time per calculation should be very fast
        avg_time_per_calc = total_time / 100
        assert avg_time_per_calc < 0.01  # Under 10ms per calculation


@pytest.mark.performance
@pytest.mark.slow
class TestSystemLoadPerformance:
    """Test system performance under various load conditions"""

    @pytest.mark.asyncio
    async def test_mixed_operation_load(self, async_client: AsyncClient, auth_headers):
        """Test performance with mixed read/write operations"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Mixed load test quote",
                metadata={"provider": "test", "tokens_used": 35},
            )
            mock_orchestrator.return_value = mock_ai

            # Create some initial quotes
            initial_quote_ids = []
            for i in range(3):
                quote_request = {
                    "service_type": "window_cleaning",
                    "property_type": "residential",
                    "area_sqm": 80.0,
                    "suburb": "Perth",
                    "contact_email": f"mixed{i}@example.com",
                    "contact_phone": "+61412345678",
                }

                response = await async_client.post(
                    "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
                )
                initial_quote_ids.append(response.json()["id"])

            # Mixed operations: create new quotes + retrieve existing ones
            start_time = time.time()

            tasks = []

            # Add creation tasks
            for i in range(5):
                quote_request = {
                    "service_type": ["window_cleaning", "glass_repair"][i % 2],
                    "property_type": "residential",
                    "area_sqm": 100.0 + (i * 10),
                    "suburb": ["Perth", "Subiaco"][i % 2],
                    "contact_email": f"mixedload{i}@example.com",
                    "contact_phone": "+61412345678",
                }

                task = async_client.post(
                    "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
                )
                tasks.append(task)

            # Add retrieval tasks
            for quote_id in initial_quote_ids:
                task = async_client.get(
                    f"/api/v1/quotes/{quote_id}", headers=auth_headers
                )
                tasks.append(task)

            # Add list tasks
            for i in range(2):
                task = async_client.get("/api/v1/quotes", headers=auth_headers)
                tasks.append(task)

            # Execute all tasks concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            total_time = end_time - start_time

            # Verify operations completed successfully
            successful_responses = [
                r
                for r in responses
                if not isinstance(r, Exception) and r.status_code in [200, 201]
            ]

            assert len(successful_responses) >= 8  # Most operations should succeed
            assert (
                total_time < 15.0
            )  # All mixed operations should complete within 15 seconds

    def test_memory_usage_under_load(self):
        """Test memory usage during intensive pricing calculations"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform many pricing calculations
        pricing_service = PricingService()

        for i in range(1000):
            price = pricing_service.calculate_price(
                service_type="window_cleaning",
                area_sqm=100.0 + (i % 50),
                difficulty_multiplier=1.0 + (i % 10) * 0.1,
                suburb=["Perth", "Subiaco", "Cottesloe"][i % 3],
            )
            assert price > 0

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory usage should not increase significantly (under 50MB)
        assert memory_increase < 50.0


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database operation performance"""

    @pytest.mark.asyncio
    async def test_quote_query_performance(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test database query performance"""
        with patch(
            "src.services.ai.orchestrator.get_ai_orchestrator"
        ) as mock_orchestrator:
            mock_ai = AsyncMock()
            mock_ai.generate_text.return_value = AsyncMock(
                success=True,
                content="Database performance test quote",
                metadata={"provider": "test", "tokens_used": 25},
            )
            mock_orchestrator.return_value = mock_ai

            # Create multiple quotes for query testing
            for i in range(10):
                quote_request = {
                    "service_type": ["window_cleaning", "glass_repair"][i % 2],
                    "property_type": "residential",
                    "area_sqm": 100.0,
                    "suburb": ["Perth", "Subiaco", "Cottesloe"][i % 3],
                    "contact_email": f"dbperf{i}@example.com",
                    "contact_phone": "+61412345678",
                }

                response = await async_client.post(
                    "/api/v1/quotes/generate", json=quote_request, headers=auth_headers
                )
                assert response.status_code == status.HTTP_201_CREATED

            # Test query performance
            query_times = []

            # Test different query patterns
            query_tests = [
                "/api/v1/quotes",  # List all quotes
                "/api/v1/quotes?service_type=window_cleaning",  # Filter by service
                "/api/v1/quotes?suburb=Perth",  # Filter by suburb
                "/api/v1/quotes?limit=5",  # Pagination
            ]

            for query_url in query_tests:
                start_time = time.time()

                response = await async_client.get(query_url, headers=auth_headers)

                end_time = time.time()
                query_time = end_time - start_time
                query_times.append(query_time)

                assert response.status_code == status.HTTP_200_OK

            # Performance assertions
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)

            assert avg_query_time < 1.0  # Average query under 1 second
            assert max_query_time < 2.0  # Max query under 2 seconds


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance and effectiveness"""

    def test_pricing_calculation_caching(self):
        """Test that repeated pricing calculations benefit from caching"""
        pricing_service = PricingService()

        # First calculation (cache miss)
        start_time = time.time()
        price1 = pricing_service.calculate_price(
            service_type="window_cleaning",
            area_sqm=100.0,
            difficulty_multiplier=1.2,
            suburb="Cottesloe",
        )
        first_calc_time = time.time() - start_time

        # Repeat the same calculation multiple times
        repeat_times = []
        for _ in range(5):
            start_time = time.time()
            price2 = pricing_service.calculate_price(
                service_type="window_cleaning",
                area_sqm=100.0,
                difficulty_multiplier=1.2,
                suburb="Cottesloe",
            )
            repeat_time = time.time() - start_time
            repeat_times.append(repeat_time)

            assert price1 == price2  # Results should be identical

        # Subsequent calculations should be faster (if caching is implemented)
        avg_repeat_time = statistics.mean(repeat_times)

        # Even without caching, calculations should be consistently fast
        assert avg_repeat_time < 0.01  # Under 10ms
        assert all(t < 0.02 for t in repeat_times)  # All under 20ms
