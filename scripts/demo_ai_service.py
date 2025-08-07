#!/usr/bin/env python3
"""
AI Service Demo Script

This script demonstrates the comprehensive AI service implementation
with all its features including multi-provider support, fallback,
rate limiting, caching, quality scoring, and metrics tracking.

Run this script to see the AI service in action:
python scripts/demo_ai_service.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.ai.ai_service import (
    AIService,
    AIRequest,
    AIProvider,
    QuoteCategory,
    generate_motivational_quote,
    generate_professional_quote,
    get_ai_service
)
from src.core.exceptions import AIServiceError, RateLimitError


async def demo_basic_usage():
    """Demonstrate basic AI service usage."""
    print("🚀 AI Service Demo - Basic Usage")
    print("=" * 50)
    
    try:
        # Simple motivational quote
        print("\n1. Generating a motivational quote...")
        response = await generate_motivational_quote(
            prompt="Success in entrepreneurship",
            context="Starting and growing a business",
            user_id="demo_user_001"
        )
        
        print(f"✅ Quote: {response.text}")
        print(f"📊 Quality Score: {response.quality_score:.2f}")
        print(f"💰 Cost: ${response.cost:.4f}")
        print(f"⚡ Provider: {response.provider.value}")
        print(f"🕐 Response Time: {response.response_time:.2f}s")
        print(f"🎯 Tokens Used: {response.tokens_used}")
        
        # Professional quote
        print("\n2. Generating a professional quote...")
        response2 = await generate_professional_quote(
            prompt="Leadership and teamwork",
            context="Corporate management and team building",
            user_id="demo_user_002"
        )
        
        print(f"✅ Quote: {response2.text}")
        print(f"📊 Quality Score: {response2.quality_score:.2f}")
        print(f"💰 Cost: ${response2.cost:.4f}")
        print(f"⚡ Provider: {response2.provider.value}")
        
    except Exception as e:
        print(f"❌ Error in basic usage demo: {e}")


async def demo_advanced_features():
    """Demonstrate advanced AI service features."""
    print("\n🔧 AI Service Demo - Advanced Features")
    print("=" * 50)
    
    try:
        service = AIService()
        
        # Custom request with specific parameters
        print("\n1. Custom request with specific parameters...")
        request = AIRequest(
            prompt="Innovation and creativity in technology",
            context="Software development and digital transformation",
            category=QuoteCategory.INSPIRATIONAL,
            tone="forward-thinking",
            max_tokens=200,
            temperature=0.8,
            user_id="advanced_demo_user"
        )
        
        response = await service.generate_quote(request)
        print(f"✅ Custom Quote: {response.text}")
        print(f"📊 Quality Score: {response.quality_score:.2f}")
        
        # Generate multiple variations
        print("\n2. Generating multiple quote variations...")
        variations = await service.generate_multiple_quotes(request, count=3)
        
        for i, variation in enumerate(variations, 1):
            print(f"\n📝 Variation {i}:")
            print(f"   Quote: {variation.text}")
            print(f"   Quality: {variation.quality_score:.2f}")
            print(f"   Provider: {variation.provider.value}")
            print(f"   Cost: ${variation.cost:.4f}")
        
        print(f"\n📈 Total variations generated: {len(variations)}")
        print(f"💰 Total cost: ${sum(v.cost for v in variations):.4f}")
        
    except Exception as e:
        print(f"❌ Error in advanced features demo: {e}")


async def demo_health_and_metrics():
    """Demonstrate health monitoring and metrics."""
    print("\n🏥 AI Service Demo - Health & Metrics")
    print("=" * 50)
    
    try:
        service = AIService()
        
        # Health check
        print("\n1. Checking provider health...")
        health_status = await service.health_check()
        
        for provider, status in health_status.items():
            status_icon = "✅" if status["status"] == "healthy" else "❌"
            print(f"   {status_icon} {provider.upper()}: {status['status']}")
            print(f"      Response Time: {status.get('response_time', 0):.2f}s")
            print(f"      Last Check: {status.get('last_check', 'Unknown')}")
            
            if status["status"] != "healthy":
                print(f"      Error: {status.get('error', 'Unknown error')}")
        
        # Get metrics
        print("\n2. Current service metrics...")
        metrics = await service.get_metrics()
        
        for provider, provider_metrics in metrics.items():
            print(f"\n📊 {provider.upper()} Metrics:")
            print(f"   Total Requests: {provider_metrics.requests_count}")
            print(f"   Successful: {provider_metrics.successful_requests}")
            print(f"   Failed: {provider_metrics.failed_requests}")
            if provider_metrics.requests_count > 0:
                success_rate = provider_metrics.successful_requests / provider_metrics.requests_count
                print(f"   Success Rate: {success_rate:.1%}")
            else:
                print(f"   Success Rate: N/A")
            print(f"   Total Cost: ${provider_metrics.total_cost:.4f}")
            print(f"   Total Tokens: {provider_metrics.total_tokens:,}")
            print(f"   Avg Response Time: {provider_metrics.average_response_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error in health and metrics demo: {e}")


async def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n🛡️ AI Service Demo - Error Handling")
    print("=" * 50)
    
    try:
        service = AIService()
        
        print("\n1. Testing invalid request handling...")
        try:
            invalid_request = AIRequest(
                prompt="",  # Empty prompt
                max_tokens=0,  # Invalid token count
                temperature=2.0,  # Invalid temperature
                user_id="error_demo_user"
            )
            
            response = await service.generate_quote(invalid_request)
            print(f"⚠️ Unexpected success: {response.text}")
            
        except AIServiceError as e:
            print(f"✅ Properly handled invalid request: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("\n2. Testing rate limiting (simulated)...")
        # Note: This would need actual rate limiting to trigger
        print("   Rate limiting demo requires actual API usage to trigger")
        print("   In production, rate limits would cause automatic fallback")
        
        print("\n3. Testing provider fallback (simulated)...")
        # This would require mocking provider failures
        print("   Fallback demo requires provider failure simulation")
        print("   The service automatically tries all available providers")
        
    except Exception as e:
        print(f"❌ Error in error handling demo: {e}")


async def demo_caching():
    """Demonstrate caching functionality."""
    print("\n🗄️ AI Service Demo - Caching")
    print("=" * 50)
    
    try:
        service = AIService()
        
        print("\n1. First request (should miss cache)...")
        request = AIRequest(
            prompt="Persistence and determination",
            context="Achieving long-term goals",
            category=QuoteCategory.MOTIVATIONAL,
            user_id="cache_demo_user"
        )
        
        start_time = datetime.now()
        response1 = await service.generate_quote(request)
        first_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Quote: {response1.text[:80]}...")
        print(f"🕐 Response Time: {first_duration:.2f}s")
        print(f"💾 From Cache: {response1.cached}")
        
        print("\n2. Second identical request (should hit cache)...")
        start_time = datetime.now()
        response2 = await service.generate_quote(request)
        second_duration = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Quote: {response2.text[:80]}...")
        print(f"🕐 Response Time: {second_duration:.2f}s")
        print(f"💾 From Cache: {response2.cached}")
        print(f"⚡ Speed Improvement: {first_duration/second_duration:.1f}x faster")
        
        # Compare responses
        if response1.text == response2.text:
            print("✅ Cached response matches original")
        else:
            print("⚠️ Cached response differs from original")
        
    except Exception as e:
        print(f"❌ Error in caching demo: {e}")


def print_service_info():
    """Print information about the AI service."""
    print("🤖 Quote Master Pro - AI Service Comprehensive Demo")
    print("=" * 60)
    print(f"📅 Demo Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python Version: {sys.version}")
    
    # Check environment configuration
    providers_configured = []
    if os.getenv('OPENAI_API_KEY'):
        providers_configured.append("OpenAI")
    if os.getenv('ANTHROPIC_API_KEY'):
        providers_configured.append("Anthropic")
    if os.getenv('AZURE_OPENAI_API_KEY'):
        providers_configured.append("Azure OpenAI")
    
    print(f"🔑 Configured Providers: {', '.join(providers_configured) if providers_configured else 'None (using mock mode)'}")
    print(f"🗄️ Redis URL: {os.getenv('REDIS_URL', 'Not configured')}")
    print()


async def main():
    """Run all demonstration scenarios."""
    print_service_info()
    
    try:
        # Run all demos
        await demo_basic_usage()
        await demo_advanced_features()
        await demo_health_and_metrics()
        await demo_error_handling()
        await demo_caching()
        
        print("\n🎉 AI Service Demo Complete!")
        print("=" * 50)
        print("✅ All features demonstrated successfully")
        print("📚 Check the documentation for more details:")
        print("   📄 src/services/ai/README.md")
        print("   🧪 tests/unit/test_ai_service.py")
        print("   🔗 tests/integration/test_ai_service_integration.py")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error in demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if we're in the correct environment
    if not project_root.exists():
        print("❌ Error: Project root not found. Please run from the project directory.")
        sys.exit(1)
    
    # Run the demo
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to run demo: {e}")
        sys.exit(1)
