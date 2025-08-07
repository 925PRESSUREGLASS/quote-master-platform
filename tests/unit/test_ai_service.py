"""
Unit tests for AI Service implementation.

This test suite covers all aspects of the AI service including:
- Provider initialization and configuration
- Quote generation with different providers
- Automatic fallback mechanisms
- Rate limiting functionality
- Caching with Redis
- Quality scoring system
- Cost calculation and metrics tracking
- Error handling and retry logic
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any

import openai
import anthropic
import redis.asyncio as redis

from src.services.ai.ai_service import (
    AIService,
    AIProvider,
    AIRequest,
    AIResponse,
    QuoteCategory,
    RateLimiter,
    QualityScorer,
    ProviderMetrics,
    get_ai_service,
    generate_motivational_quote,
    generate_professional_quote
)
from src.core.exceptions import AIServiceError, RateLimitError


class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        assert limiter.max_requests == 10
        assert limiter.time_window == 60
        assert limiter.requests == []
    
    @pytest.mark.asyncio
    async def test_rate_limiter_can_proceed_empty(self):
        """Test rate limiter with no previous requests."""
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        can_proceed = await limiter.can_proceed()
        assert can_proceed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_can_proceed_within_limit(self):
        """Test rate limiter within allowed limits."""
        limiter = RateLimiter(max_requests=10, time_window=60)
        
        # Record 5 requests
        for _ in range(5):
            await limiter.record_request()
        
        can_proceed = await limiter.can_proceed()
        assert can_proceed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_exceeds_limit(self):
        """Test rate limiter when exceeding limits."""
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # Record maximum requests
        for _ in range(3):
            await limiter.record_request()
        
        can_proceed = await limiter.can_proceed()
        assert can_proceed is False
    
    @pytest.mark.asyncio
    async def test_rate_limiter_time_window_cleanup(self):
        """Test rate limiter cleans up old requests."""
        limiter = RateLimiter(max_requests=3, time_window=1)  # 1 second window
        
        # Record requests
        for _ in range(3):
            await limiter.record_request()
        
        # Should be at limit
        assert await limiter.can_proceed() is False
        
        # Wait for time window to expire
        await asyncio.sleep(1.1)
        
        # Should be able to proceed again
        assert await limiter.can_proceed() is True


class TestQualityScorer:
    """Test cases for QualityScorer class."""
    
    def test_quality_scorer_empty_text(self):
        """Test quality scorer with empty text."""
        request = AIRequest(prompt="test")
        score = QualityScorer.score_quote("", request)
        assert score == 0.0
    
    def test_quality_scorer_good_quote(self):
        """Test quality scorer with good quote."""
        request = AIRequest(
            prompt="motivational quote",
            context="business success motivation",
            category=QuoteCategory.MOTIVATIONAL
        )
        
        good_quote = "Success is not final, failure is not fatal: it is the courage to continue that counts."
        score = QualityScorer.score_quote(good_quote, request)
        
        assert 0.6 <= score <= 1.0  # Should get a good score
    
    def test_quality_scorer_poor_quote(self):
        """Test quality scorer with poor quality quote."""
        request = AIRequest(prompt="test")
        
        poor_quote = "a"  # Too short
        score = QualityScorer.score_quote(poor_quote, request)
        
        assert score < 0.5  # Should get a low score
    
    def test_quality_scorer_with_context_relevance(self):
        """Test quality scorer with context relevance."""
        request = AIRequest(
            prompt="quote about success",
            context="business achievement goals motivation"
        )
        
        relevant_quote = "Business success comes from setting clear goals and staying motivated."
        score = QualityScorer.score_quote(relevant_quote, request)
        
        # Should get higher score due to context relevance
        assert score > 0.6


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = MagicMock()
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.ANTHROPIC_API_KEY = "test-anthropic-key"
    settings.AZURE_OPENAI_API_KEY = "test-azure-key"
    settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
    settings.REDIS_URL = "redis://localhost:6379"
    return settings


@pytest.fixture
def sample_ai_request():
    """Sample AI request for testing."""
    return AIRequest(
        prompt="Generate a motivational quote about success",
        context="Business success and achievement",
        category=QuoteCategory.MOTIVATIONAL,
        tone="inspiring",
        max_tokens=200,
        temperature=0.7,
        user_id="test_user_123"
    )


@pytest.fixture
def sample_ai_response():
    """Sample AI response for testing."""
    return AIResponse(
        text="Success is not the key to happiness. Happiness is the key to success.",
        provider=AIProvider.OPENAI,
        model="gpt-4",
        tokens_used=150,
        cost=0.003,
        quality_score=0.85,
        response_time=1.2,
        timestamp=datetime.now(),
        request_id="test_request_123"
    )


class TestAIService:
    """Test cases for AIService class."""
    
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    def test_ai_service_initialization(self, mock_redis, mock_get_settings, mock_settings):
        """Test AI service initialization."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        assert service.settings == mock_settings
        assert AIProvider.OPENAI in service.clients
        assert AIProvider.ANTHROPIC in service.clients
        assert AIProvider.AZURE_OPENAI in service.clients
        assert len(service.rate_limiters) == 3
        assert len(service.metrics) == 3
    
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    def test_ai_service_initialization_no_providers(self, mock_redis, mock_get_settings):
        """Test AI service initialization with no providers configured."""
        settings = MagicMock()
        settings.OPENAI_API_KEY = None
        settings.ANTHROPIC_API_KEY = None
        settings.AZURE_OPENAI_API_KEY = None
        mock_get_settings.return_value = settings
        
        with pytest.raises(AIServiceError, match="No AI providers configured"):
            AIService()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_generate_cache_key(self, mock_redis, mock_get_settings, mock_settings, sample_ai_request):
        """Test cache key generation."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        cache_key = service._generate_cache_key(sample_ai_request)
        
        assert isinstance(cache_key, str)
        assert cache_key.startswith("ai_service:")
        assert len(cache_key) == 43  # ai_service: + 32 char MD5 hash
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_cache_response_and_retrieval(self, mock_redis, mock_get_settings, 
                                               mock_settings, sample_ai_request, sample_ai_response):
        """Test caching and retrieving responses."""
        mock_get_settings.return_value = mock_settings
        mock_cache = AsyncMock()
        mock_redis.return_value = mock_cache
        
        service = AIService()
        cache_key = service._generate_cache_key(sample_ai_request)
        
        # Test caching
        await service._cache_response(cache_key, sample_ai_response)
        mock_cache.setex.assert_called_once()
        
        # Test retrieval
        cached_data = sample_ai_response.to_dict()
        cached_data['timestamp'] = sample_ai_response.timestamp.isoformat()
        mock_cache.get.return_value = json.dumps(cached_data)
        
        retrieved_response = await service._get_cached_response(cache_key)
        
        assert retrieved_response is not None
        assert retrieved_response.text == sample_ai_response.text
        assert retrieved_response.cached is True
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_rate_limit_check(self, mock_redis, mock_get_settings, mock_settings):
        """Test rate limit checking."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Should pass initially
        result = await service._check_rate_limit(AIProvider.OPENAI)
        assert result is True
        
        # Mock rate limiter to return False
        mock_limiter = AsyncMock()
        mock_limiter.can_proceed.return_value = False
        service.rate_limiters[AIProvider.OPENAI] = mock_limiter
        
        # Should raise RateLimitError
        with pytest.raises(RateLimitError):
            await service._check_rate_limit(AIProvider.OPENAI)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_openai_api_call_success(self, mock_redis, mock_get_settings, 
                                          mock_settings, sample_ai_request):
        """Test successful OpenAI API call."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test quote from OpenAI"
        mock_response.usage.total_tokens = 100
        mock_response.id = "test_id_123"
        
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.return_value = mock_response
        
        response = await service._call_openai(sample_ai_request)
        
        assert isinstance(response, AIResponse)
        assert response.text == "Test quote from OpenAI"
        assert response.provider == AIProvider.OPENAI
        assert response.tokens_used == 100
        assert response.cost > 0
        assert 0 <= response.quality_score <= 1
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_anthropic_api_call_success(self, mock_redis, mock_get_settings, 
                                             mock_settings, sample_ai_request):
        """Test successful Anthropic API call."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock Anthropic client response
        mock_response = MagicMock()
        mock_response.content[0].text = "Test quote from Anthropic"
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 25
        mock_response.id = "test_anthropic_123"
        
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.return_value = mock_response
        
        response = await service._call_anthropic(sample_ai_request)
        
        assert isinstance(response, AIResponse)
        assert response.text == "Test quote from Anthropic"
        assert response.provider == AIProvider.ANTHROPIC
        assert response.tokens_used == 75  # input + output tokens
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_generate_quote_with_fallback(self, mock_redis, mock_get_settings, 
                                               mock_settings, sample_ai_request):
        """Test quote generation with provider fallback."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        service._get_cached_response = AsyncMock(return_value=None)
        service._cache_response = AsyncMock()
        service._check_rate_limit = AsyncMock(return_value=True)
        
        # Mock first provider (OpenAI) to fail
        service._call_openai = AsyncMock(side_effect=AIServiceError("OpenAI failed"))
        
        # Mock second provider (Anthropic) to succeed
        success_response = AIResponse(
            text="Fallback quote from Anthropic",
            provider=AIProvider.ANTHROPIC,
            model="claude-3-sonnet",
            tokens_used=100,
            cost=0.002,
            quality_score=0.8,
            response_time=1.5,
            timestamp=datetime.now(),
            request_id="fallback_123"
        )
        service._call_anthropic = AsyncMock(return_value=success_response)
        
        response = await service.generate_quote(sample_ai_request)
        
        assert response.provider == AIProvider.ANTHROPIC
        assert response.text == "Fallback quote from Anthropic"
        
        # Verify OpenAI was tried first, then Anthropic
        service._call_openai.assert_called_once()
        service._call_anthropic.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_generate_quote_all_providers_fail(self, mock_redis, mock_get_settings, 
                                                    mock_settings, sample_ai_request):
        """Test quote generation when all providers fail."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        service._get_cached_response = AsyncMock(return_value=None)
        service._check_rate_limit = AsyncMock(return_value=True)
        
        # Mock all providers to fail
        service._call_openai = AsyncMock(side_effect=AIServiceError("OpenAI failed"))
        service._call_anthropic = AsyncMock(side_effect=AIServiceError("Anthropic failed"))
        service._call_azure_openai = AsyncMock(side_effect=AIServiceError("Azure failed"))
        
        with pytest.raises(AIServiceError, match="All AI providers failed"):
            await service.generate_quote(sample_ai_request)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_generate_quote_with_cache_hit(self, mock_redis, mock_get_settings, 
                                                mock_settings, sample_ai_request, sample_ai_response):
        """Test quote generation with cache hit."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock cached response
        cached_response = sample_ai_response
        cached_response.cached = True
        service._get_cached_response = AsyncMock(return_value=cached_response)
        
        response = await service.generate_quote(sample_ai_request)
        
        assert response.cached is True
        assert response.text == sample_ai_response.text
        
        # Verify no API calls were made
        service._get_cached_response.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_generate_multiple_quotes(self, mock_redis, mock_get_settings, 
                                           mock_settings, sample_ai_request):
        """Test generating multiple quote variations."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock generate_quote to return different responses
        responses = []
        for i in range(3):
            response = AIResponse(
                text=f"Quote variation {i+1}",
                provider=AIProvider.OPENAI,
                model="gpt-4",
                tokens_used=100,
                cost=0.002,
                quality_score=0.8 - (i * 0.1),  # Decreasing quality scores
                response_time=1.0,
                timestamp=datetime.now(),
                request_id=f"variation_{i}"
            )
            responses.append(response)
        
        service.generate_quote = AsyncMock(side_effect=responses)
        
        result = await service.generate_multiple_quotes(sample_ai_request, count=3)
        
        assert len(result) == 3
        # Verify responses are sorted by quality score (highest first)
        assert result[0].quality_score >= result[1].quality_score >= result[2].quality_score
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_health_check(self, mock_redis, mock_get_settings, mock_settings):
        """Test health check functionality."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock successful API calls
        mock_openai_response = AIResponse(
            text="Health check response",
            provider=AIProvider.OPENAI,
            model="gpt-4",
            tokens_used=10,
            cost=0.0001,
            quality_score=0.5,
            response_time=0.5,
            timestamp=datetime.now(),
            request_id="health_check"
        )
        
        service._call_openai = AsyncMock(return_value=mock_openai_response)
        service._call_anthropic = AsyncMock(return_value=mock_openai_response)
        service._call_azure_openai = AsyncMock(return_value=mock_openai_response)
        
        health_status = await service.health_check()
        
        assert "openai" in health_status
        assert "anthropic" in health_status
        assert "azure_openai" in health_status
        
        for provider_status in health_status.values():
            assert provider_status["status"] == "healthy"
            assert "response_time" in provider_status
            assert "last_check" in provider_status
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_metrics_tracking(self, mock_redis, mock_get_settings, mock_settings):
        """Test metrics tracking functionality."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Verify initial metrics
        metrics = await service.get_metrics()
        
        for provider_metrics in metrics.values():
            assert provider_metrics.requests_count == 0
            assert provider_metrics.successful_requests == 0
            assert provider_metrics.failed_requests == 0
            assert provider_metrics.total_cost == 0.0
        
        # Update metrics
        test_response = AIResponse(
            text="Test response",
            provider=AIProvider.OPENAI,
            model="gpt-4",
            tokens_used=100,
            cost=0.002,
            quality_score=0.8,
            response_time=1.0,
            timestamp=datetime.now(),
            request_id="test"
        )
        
        service._update_metrics(AIProvider.OPENAI, test_response)
        
        # Check updated metrics
        metrics = await service.get_metrics()
        openai_metrics = metrics["openai"]
        
        assert openai_metrics.requests_count == 1
        assert openai_metrics.successful_requests == 1
        assert openai_metrics.total_cost == 0.002
        assert openai_metrics.total_tokens == 100


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_ai_service')
    async def test_generate_motivational_quote(self, mock_get_service):
        """Test generate_motivational_quote convenience function."""
        mock_service = AsyncMock()
        mock_response = AIResponse(
            text="Motivational test quote",
            provider=AIProvider.OPENAI,
            model="gpt-4",
            tokens_used=50,
            cost=0.001,
            quality_score=0.9,
            response_time=0.8,
            timestamp=datetime.now(),
            request_id="motivational_test"
        )
        mock_service.generate_quote.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        result = await generate_motivational_quote("success", "business context", "user123")
        
        assert result.text == "Motivational test quote"
        
        # Verify the request was configured correctly
        call_args = mock_service.generate_quote.call_args[0][0]
        assert call_args.prompt == "success"
        assert call_args.context == "business context"
        assert call_args.category == QuoteCategory.MOTIVATIONAL
        assert call_args.tone == "inspiring"
        assert call_args.user_id == "user123"
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_ai_service')
    async def test_generate_professional_quote(self, mock_get_service):
        """Test generate_professional_quote convenience function."""
        mock_service = AsyncMock()
        mock_response = AIResponse(
            text="Professional test quote",
            provider=AIProvider.OPENAI,
            model="gpt-4",
            tokens_used=75,
            cost=0.0015,
            quality_score=0.85,
            response_time=1.1,
            timestamp=datetime.now(),
            request_id="professional_test"
        )
        mock_service.generate_quote.return_value = mock_response
        mock_get_service.return_value = mock_service
        
        result = await generate_professional_quote("teamwork", "corporate environment", "user456")
        
        assert result.text == "Professional test quote"
        
        # Verify the request was configured correctly
        call_args = mock_service.generate_quote.call_args[0][0]
        assert call_args.prompt == "teamwork"
        assert call_args.context == "corporate environment"
        assert call_args.category == QuoteCategory.PROFESSIONAL
        assert call_args.tone == "professional"
        assert call_args.max_tokens == 300
        assert call_args.user_id == "user456"


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_openai_api_error_handling(self, mock_redis, mock_get_settings, 
                                            mock_settings, sample_ai_request):
        """Test OpenAI API error handling."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock OpenAI client to raise an error
        service.clients[AIProvider.OPENAI] = AsyncMock()
        service.clients[AIProvider.OPENAI].chat.completions.create.side_effect = Exception("OpenAI API Error")
        
        with pytest.raises(AIServiceError, match="OpenAI request failed"):
            await service._call_openai(sample_ai_request)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_anthropic_api_error_handling(self, mock_redis, mock_get_settings, 
                                               mock_settings, sample_ai_request):
        """Test Anthropic API error handling."""
        mock_get_settings.return_value = mock_settings
        mock_redis.return_value = AsyncMock()
        
        service = AIService()
        
        # Mock Anthropic client to raise an error
        service.clients[AIProvider.ANTHROPIC] = AsyncMock()
        service.clients[AIProvider.ANTHROPIC].messages.create.side_effect = Exception("Anthropic API Error")
        
        with pytest.raises(AIServiceError, match="Anthropic request failed"):
            await service._call_anthropic(sample_ai_request)
    
    @pytest.mark.asyncio
    @patch('src.services.ai.ai_service.get_settings')
    @patch('src.services.ai.ai_service.redis.from_url')
    async def test_cache_error_handling(self, mock_redis, mock_get_settings, 
                                       mock_settings, sample_ai_request):
        """Test cache error handling."""
        mock_get_settings.return_value = mock_settings
        mock_cache = AsyncMock()
        mock_cache.get.side_effect = Exception("Redis connection error")
        mock_redis.return_value = mock_cache
        
        service = AIService()
        cache_key = service._generate_cache_key(sample_ai_request)
        
        # Should handle cache errors gracefully and return None
        result = await service._get_cached_response(cache_key)
        assert result is None
