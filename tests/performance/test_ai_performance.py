"""
Performance Tests for AI Service
Phase 2 Enhancement: Benchmarking and Load Testing

This module provides comprehensive performance testing for the AI service,
including response times, throughput, memory usage, and scalability tests.
"""

import pytest
import asyncio
import time
import gc
from unittest.mock import AsyncMock, patch
import psutil
import os

from src.services.ai.ai_service import AIService, AIRequest


class TestAIServicePerformance:
    """Performance tests for AI Service functionality."""
    
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing."""
        return AIService()
    
    @pytest.mark.benchmark
    def test_single_quote_generation_benchmark(self, benchmark, ai_service):
        """Benchmark single quote generation performance."""
        
        @patch('src.services.ai.ai_service.openai.ChatCompletion.acreate')
        async def mock_generate_quote():
            # Mock the OpenAI response
            with patch('src.services.ai.ai_service.openai.ChatCompletion.acreate') as mock_openai:
                mock_openai.return_value = AsyncMock()
                mock_openai.return_value.choices = [
                    AsyncMock(message=AsyncMock(content="Success is not final, failure is not fatal."))
                ]
                
                result = await ai_service.generate_quote(
                    AIRequest(
                        prompt="Generate a motivational quote",
                        context="motivation",
                        tone="positive"
                    )
                )
                return result
        
        # Benchmark the function
        result = benchmark(asyncio.run, mock_generate_quote())
        
        # Verify result structure
        assert result is not None
        assert "quote" in result or isinstance(result, str)
    
    @pytest.mark.benchmark
    def test_cache_performance_benchmark(self, benchmark, ai_service):
        """Benchmark cache hit performance vs fresh generation."""
        
        cache_key = "test_performance_cache_key"
        test_response = {
            "quote": "Cached performance quote",
            "metadata": {"provider": "test", "response_time": 0.001}
        }
        
        def cache_hit_operation():
            # Simulate cache hit
            ai_service.cache.set(cache_key, test_response, ttl=300)
            return ai_service.cache.get(cache_key)
        
        # Benchmark cache retrieval
        result = benchmark(cache_hit_operation)
        
        assert result == test_response
        # Cache operations should be under 5ms
        assert benchmark.stats.mean < 0.005
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, ai_service):
        """Test performance under concurrent load."""
        
        # Mock AI provider responses
        with patch('src.services.ai.ai_service.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = AsyncMock()
            mock_openai.return_value.choices = [
                AsyncMock(message=AsyncMock(content="Concurrent test quote"))
            ]
            
            # Test different concurrency levels
            concurrency_levels = [5, 10, 20]
            
            for concurrency in concurrency_levels:
                start_time = time.time()
                
                # Create concurrent tasks
                tasks = [
                    ai_service.generate_quote(
                        context=f"test_context_{i}",
                        style="motivational",
                        tone="positive"
                    )
                    for i in range(concurrency)
                ]
                
                # Execute all tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Verify all requests completed successfully
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) == concurrency
                
                # Calculate performance metrics
                avg_response_time = duration / concurrency
                requests_per_second = concurrency / duration
                
                print(f"\nConcurrency: {concurrency}")
                print(f"Total Duration: {duration:.3f}s")
                print(f"Average Response Time: {avg_response_time:.3f}s")
                print(f"Requests/Second: {requests_per_second:.2f}")
                
                # Performance assertions
                assert avg_response_time < 2.0  # Each request should complete within 2s
                assert requests_per_second > 1.0  # Should handle at least 1 req/s
    
    def test_memory_usage_under_load(self, ai_service):
        """Test memory usage during sustained operations."""
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate sustained load
        with patch('src.services.ai.ai_service.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = AsyncMock()
            mock_openai.return_value.choices = [
                AsyncMock(message=AsyncMock(content="Memory test quote"))
            ]
            
            # Generate many quotes to test memory usage
            for i in range(100):
                result = asyncio.run(ai_service.generate_quote(
                    context=f"memory_test_{i}",
                    style="inspirational",
                    tone="positive"
                ))
                
                # Occasionally check memory
                if i % 25 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory
                    print(f"Iteration {i}: Memory usage: {current_memory:.2f}MB (+{memory_increase:.2f}MB)")
                    
                    # Memory shouldn't grow excessively
                    assert memory_increase < 100  # Less than 100MB increase
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"Final memory increase: {total_increase:.2f}MB")
        # Memory should return to reasonable levels after GC
        assert total_increase < 50  # Less than 50MB permanent increase
    
    @pytest.mark.benchmark
    def test_rate_limiter_performance(self, benchmark, ai_service):
        """Benchmark rate limiter overhead."""
        
        from src.services.ai.ai_service import RateLimiter
        rate_limiter = RateLimiter(max_requests=60, time_window=60)
        
        def rate_limit_check():
            return asyncio.run(rate_limiter.can_proceed())
        
        # Benchmark rate limiting check
        result = benchmark(rate_limit_check)
        
        assert result is True
        # Rate limiting should be very fast
        assert benchmark.stats.mean < 0.01  # Under 10ms (accounting for async overhead)
    
    @pytest.mark.asyncio
    async def test_provider_fallback_performance(self, ai_service):
        """Test performance impact of provider fallback."""
        
        start_time = time.time()
        
        with patch('src.services.ai.ai_service.openai.ChatCompletion.acreate') as mock_openai, \
             patch('src.services.ai.ai_service.anthropic.messages.create') as mock_anthropic:
            
            # First provider fails, second succeeds
            mock_openai.side_effect = Exception("Provider 1 failed")
            mock_anthropic.return_value = AsyncMock()
            mock_anthropic.return_value.content = [
                AsyncMock(text="Fallback test quote")
            ]
            
            result = await ai_service.generate_quote(
                context="fallback_test",
                style="motivational",
                tone="positive"
            )
            
            end_time = time.time()
            fallback_duration = end_time - start_time
            
            print(f"Fallback duration: {fallback_duration:.3f}s")
            
            # Fallback should complete within reasonable time
            assert fallback_duration < 5.0  # Less than 5 seconds total
            assert result is not None
    
    @pytest.mark.benchmark
    def test_cache_key_generation_performance(self, benchmark, ai_service):
        """Benchmark cache key generation performance."""
        
        def generate_cache_key():
            return ai_service._generate_cache_key(
                context="performance_test",
                style="motivational", 
                tone="positive",
                additional_context="benchmark testing"
            )
        
        # Benchmark cache key generation
        result = benchmark(generate_cache_key)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Cache key generation should be very fast
        assert benchmark.stats.mean < 0.0001  # Under 0.1ms


@pytest.mark.performance
class TestPerformanceTargets:
    """Test specific performance targets for Phase 2."""
    
    @pytest.fixture
    def ai_service(self):
        return AIService()
    
    @pytest.mark.asyncio
    async def test_response_time_sla(self, ai_service):
        """Test that 95% of requests complete within SLA."""
        
        response_times = []
        
        with patch('src.services.ai.ai_service.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = AsyncMock()
            mock_openai.return_value.choices = [
                AsyncMock(message=AsyncMock(content="SLA test quote"))
            ]
            
            # Test multiple requests
            for i in range(20):
                start_time = time.time()
                
                await ai_service.generate_quote(
                    context=f"sla_test_{i}",
                    style="motivational",
                    tone="positive"
                )
                
                end_time = time.time()
                response_times.append(end_time - start_time)
        
        # Calculate 95th percentile
        response_times.sort()
        p95_index = int(0.95 * len(response_times))
        p95_time = response_times[p95_index]
        
        print(f"95th percentile response time: {p95_time:.3f}s")
        
        # 95% of requests should complete within 3 seconds
        assert p95_time < 3.0
    
    def test_cache_performance_target(self, ai_service):
        """Test cache performance meets Phase 2 targets."""
        
        # Set up cache with test data
        test_key = "performance_target_test"
        test_value = {"quote": "Fast cache response", "timestamp": time.time()}
        
        # Measure cache operations
        start_time = time.time()
        ai_service.cache.set(test_key, test_value, ttl=300)
        set_time = time.time() - start_time
        
        start_time = time.time()
        result = ai_service.cache.get(test_key)
        get_time = time.time() - start_time
        
        print(f"Cache SET time: {set_time*1000:.2f}ms")
        print(f"Cache GET time: {get_time*1000:.2f}ms")
        
        # Cache operations should be under 1ms
        assert set_time < 0.001
        assert get_time < 0.001
        assert result == test_value
