"""
Integration tests for AI Service.

These tests verify the AI service works correctly with actual dependencies
and external services (where appropriate) to ensure proper integration.
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from src.services.ai.ai_service import (
    AIService,
    AIProvider,
    AIRequest,
    ServiceCategory,
    get_ai_service
)
from src.core.exceptions import AIServiceError


@pytest.fixture
def mock_settings():
    """Mock settings for integration tests."""
    settings = MagicMock()
    settings.OPENAI_API_KEY = "test-openai-key-integration"
    settings.ANTHROPIC_API_KEY = "test-anthropic-key-integration"
    settings.AZURE_OPENAI_API_KEY = "test-azure-key-integration"
    settings.AZURE_OPENAI_ENDPOINT = "https://test-integration.openai.azure.com/"
    settings.REDIS_URL = "redis://localhost:6379/1"  # Use different DB for tests
    return settings


class TestAIServiceIntegration:
    """Integration tests for AI service functionality."""
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_ai_service_singleton_pattern(self, mock_redis, mock_get_settings, mock_settings):
        """Test that AI service follows singleton pattern."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        # Get two instances
        service1 = get_ai_service()
        service2 = get_ai_service()
        
        # Should be the same instance
        assert service1 is service2
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_end_to_end_quote_generation(self, mock_redis, mock_get_settings, mock_settings):
        """Test end-to-end quote generation workflow."""
        mock_get_settings.return_value = mock_settings
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        # Mock no cached response initially
        mock_redis_client.get.return_value = None
        
        service = AIService()
        
        # Mock successful OpenAI response
        mock_openai_response = MagicMock()
        mock_openai_response.choices[0].message.content = "Success comes to those who never give up on their dreams."
        mock_openai_response.usage.total_tokens = 150
        mock_openai_response.id = "integration_test_123"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_openai_response
        
        # Create test request
        request = AIRequest(
            prompt="Generate a window cleaning service quote",
            context="Residential property cleaning services",
            category=ServiceCategory.WINDOW_CLEANING,
            tone="professional",
            user_id="integration_test_user"
        )
        
        # Generate quote
        response = await service.generate_quote(request)
        
        # Verify response
        assert response is not None
        assert response.text == "Success comes to those who never give up on their dreams."
        assert response.provider == AIProvider.OPENAI
        assert response.tokens_used == 150
        assert response.cost > 0
        assert 0 <= response.quality_score <= 1
        assert response.cached is False
        
        # Verify caching was attempted
        mock_redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_provider_fallback_integration(self, mock_redis, mock_get_settings, mock_settings):
        """Test provider fallback mechanism in integration scenario."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock OpenAI to fail
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.side_effect = Exception("OpenAI timeout")
        
        # Mock Anthropic to succeed
        mock_anthropic_response = MagicMock()
        mock_anthropic_response.content[0].text = "Resilience is the key to overcoming challenges."
        mock_anthropic_response.usage.input_tokens = 75
        mock_anthropic_response.usage.output_tokens = 25
        mock_anthropic_response.id = "anthropic_fallback_123"
        
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.return_value = mock_anthropic_response
        
        request = AIRequest(
            prompt="Generate a pressure washing service quote",
            category=ServiceCategory.PRESSURE_WASHING,
            user_id="fallback_test_user"
        )
        
        response = await service.generate_quote(request)
        
        # Verify fallback worked
        assert response.provider == AIProvider.ANTHROPIC
        assert response.text == "Resilience is the key to overcoming challenges."
        
        # Verify OpenAI was tried first
        service.clients[AIProvider.OPENAI].chat.completions.create.assert_called_once()
        service.clients[AIProvider.ANTHROPIC].messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_rate_limiting_integration(self, mock_redis, mock_get_settings, mock_settings):
        """Test rate limiting works correctly in integration scenario."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Set very low rate limit for testing
        service.rate_limiters[AIProvider.OPENAI].max_requests = 1
        service.rate_limiters[AIProvider.OPENAI].time_window = 10  # 10 seconds
        
        # Mock successful OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test quote"
        mock_response.usage.total_tokens = 50
        mock_response.id = "rate_limit_test"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_response
        
        request = AIRequest(
            prompt="Test quote",
            user_id="rate_limit_user"
        )
        
        # First request should succeed
        response1 = await service.generate_quote(request)
        assert response1.provider == AIProvider.OPENAI
        
        # Second request should hit rate limit and fallback to another provider
        # Mock Anthropic as fallback
        mock_anthropic_response = MagicMock()
        mock_anthropic_response.content[0].text = "Fallback quote"
        mock_anthropic_response.usage.input_tokens = 30
        mock_anthropic_response.usage.output_tokens = 20
        mock_anthropic_response.id = "anthropic_rate_limit_fallback"
        
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.return_value = mock_anthropic_response
        
        response2 = await service.generate_quote(request)
        
        # Should fallback to Anthropic due to rate limiting
        assert response2.provider == AIProvider.ANTHROPIC
        assert response2.text == "Fallback quote"
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_cache_integration_workflow(self, mock_redis, mock_get_settings, mock_settings):
        """Test caching workflow in integration scenario."""
        mock_get_settings.return_value = mock_settings
        mock_redis_client = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        service = AIService()
        
        request = AIRequest(
            prompt="Cached quote test",
            context="Testing cache functionality",
            user_id="cache_test_user"
        )
        
        # First request - no cache, should make API call
        mock_redis_client.get.return_value = None
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Cached test quote"
        mock_response.usage.total_tokens = 100
        mock_response.id = "cache_test_123"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_response
        
        response1 = await service.generate_quote(request)
        
        # Verify API was called and response cached
        service.clients[AIProvider.OPENAI].chat.completions.create.assert_called_once()
        mock_redis_client.setex.assert_called_once()
        assert response1.cached is False
        
        # Second request - should return cached response
        cached_data = {
            "text": "Cached test quote",
            "provider": "openai",
            "model": "gpt-4",
            "tokens_used": 100,
            "cost": 0.002,
            "quality_score": 0.8,
            "response_time": 1.0,
            "timestamp": datetime.now().isoformat(),
            "request_id": "cache_test_123",
            "cached": True
        }
        
        import json
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        response2 = await service.generate_quote(request)
        
        # Verify cached response
        assert response2.cached is True
        assert response2.text == "Cached test quote"
        assert response2.tokens_used == 100
        
        # API should not be called again
        assert service.clients[AIProvider.OPENAI].chat.completions.create.call_count == 1
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_multiple_quotes_integration(self, mock_redis, mock_get_settings, mock_settings):
        """Test generating multiple quote variations in integration scenario."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock different responses for each variation
        responses = [
            "The journey of success begins with a single step.",
            "Excellence is achieved through persistent effort.",
            "Dreams become reality when backed by determination."
        ]
        
        call_count = 0
        
        async def mock_generate_quote(request, preferred_provider=None, use_cache=True):
            nonlocal call_count
            response_text = responses[call_count % len(responses)]
            call_count += 1
            
            from src.services.ai.ai_service import AIResponse
            return AIResponse(
                text=response_text,
                provider=AIProvider.OPENAI,
                model="gpt-4",
                tokens_used=100,
                cost=0.002,
                quality_score=0.9 - (call_count * 0.1),  # Decreasing quality
                response_time=1.0,
                timestamp=datetime.now(),
                request_id=f"multi_test_{call_count}"
            )
        
        # Patch the generate_quote method
        service.generate_quote = mock_generate_quote
        
        request = AIRequest(
            prompt="Generate gutter cleaning service quotes",
            category=ServiceCategory.GUTTER_CLEANING,
            user_id="multi_quote_user"
        )
        
        results = await service.generate_multiple_quotes(request, count=3)
        
        # Verify we got 3 different quotes
        assert len(results) == 3
        assert all(result.text in responses for result in results)
        
        # Verify quotes are sorted by quality score (highest first)
        for i in range(len(results) - 1):
            assert results[i].quality_score >= results[i + 1].quality_score
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_health_check_integration(self, mock_redis, mock_get_settings, mock_settings):
        """Test health check functionality in integration scenario."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock successful health check responses
        health_response_template = MagicMock()
        health_response_template.choices[0].message.content = "Health check OK"
        health_response_template.usage.total_tokens = 10
        health_response_template.id = "health_check"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = health_response_template
        
        # Mock Anthropic health check
        anthropic_health = MagicMock()
        anthropic_health.content[0].text = "Health check OK"
        anthropic_health.usage.input_tokens = 5
        anthropic_health.usage.output_tokens = 5
        anthropic_health.id = "health_anthropic"
        
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.return_value = anthropic_health
        
        # Mock Azure health check
        service.clients[AIProvider.AZURE_OPENAI] = AsyncMock()
        service.clients[AIProvider.AZURE_OPENAI].chat.completions.create.return_value = health_response_template
        
        health_status = await service.health_check()
        
        # Verify all providers are healthy
        assert "openai" in health_status
        assert "anthropic" in health_status
        assert "azure_openai" in health_status
        
        for provider, status in health_status.items():
            assert status["status"] == "healthy"
            assert "response_time" in status
            assert status["response_time"] > 0
            assert "last_check" in status
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_metrics_tracking_integration(self, mock_redis, mock_get_settings, mock_settings):
        """Test metrics tracking across multiple operations."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Initial metrics should be zero
        initial_metrics = await service.get_metrics()
        for provider_metrics in initial_metrics.values():
            assert provider_metrics.requests_count == 0
            assert provider_metrics.successful_requests == 0
            assert provider_metrics.total_cost == 0.0
        
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Metrics test quote"
        mock_response.usage.total_tokens = 75
        mock_response.id = "metrics_test"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_response
        
        # Generate multiple quotes to accumulate metrics
        request = AIRequest(
            prompt="Test quote for metrics",
            user_id="metrics_user"
        )
        
        for _ in range(3):
            await service.generate_quote(request)
        
        # Check updated metrics
        final_metrics = await service.get_metrics()
        openai_metrics = final_metrics["openai"]
        
        assert openai_metrics.requests_count == 3
        assert openai_metrics.successful_requests == 3
        assert openai_metrics.total_cost > 0
        assert openai_metrics.total_tokens == 225  # 75 * 3
        assert openai_metrics.average_response_time > 0


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery scenarios."""
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_complete_provider_failure_recovery(self, mock_redis, mock_get_settings, mock_settings):
        """Test recovery when all providers initially fail."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock all providers to fail initially
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.side_effect = Exception("Network error")
        
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.side_effect = Exception("Service unavailable")
        
        service.clients[AIProvider.AZURE_OPENAI] = AsyncMock()
        service.clients[AIProvider.AZURE_OPENAI].chat.completions.create.side_effect = Exception("Timeout")
        
        request = AIRequest(
            prompt="Test error recovery",
            user_id="error_recovery_user"
        )
        
        # Should raise AIServiceError when all providers fail
        with pytest.raises(AIServiceError, match="All AI providers failed"):
            await service.generate_quote(request)
        
        # Verify all providers were attempted
        service.clients[AIProvider.OPENAI].chat.completions.create.assert_called()
        service.clients[AIProvider.ANTHROPIC].messages.create.assert_called()
        service.clients[AIProvider.AZURE_OPENAI].chat.completions.create.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_cache_failure_graceful_handling(self, mock_redis, mock_get_settings, mock_settings):
        """Test graceful handling of cache failures."""
        mock_get_settings.return_value = mock_settings
        
        # Mock Redis to fail
        mock_redis_client = AsyncMock()
        mock_redis_client.get.side_effect = Exception("Redis connection failed")
        mock_redis_client.setex.side_effect = Exception("Redis write failed")
        mock_redis.return_value = mock_redis_client
        
        service = AIService()
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Quote despite cache failure"
        mock_response.usage.total_tokens = 100
        mock_response.id = "cache_failure_test"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_response
        
        request = AIRequest(
            prompt="Test cache failure handling",
            user_id="cache_failure_user"
        )
        
        # Should still work despite cache failures
        response = await service.generate_quote(request)
        
        assert response is not None
        assert response.text == "Quote despite cache failure"
        assert response.cached is False
        
        # Verify API was called despite cache failure
        service.clients[AIProvider.OPENAI].chat.completions.create.assert_called_once()


# Test fixtures for integration testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
