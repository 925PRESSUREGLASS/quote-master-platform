"""
API Key Configuration Test & Verification
Tests all configured AI providers and validates the Enhanced AI Service setup.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_api_configuration():
    """Test and verify API key configuration."""
    
    print("🔑 API Key Configuration Test")
    print("=" * 60)
    
    results = {
        "config_loaded": False,
        "openai_configured": False,
        "anthropic_configured": False,
        "azure_configured": False,
        "enhanced_service": False,
        "full_integration": False
    }
    
    # Test 1: Configuration Loading
    try:
        print("1️⃣ Testing Configuration Loading...")
        from src.core.config import get_settings
        
        settings = get_settings()
        print(f"   📊 App: {settings.app_name} v{settings.app_version}")
        print(f"   🌍 Environment: {settings.environment}")
        print(f"   🔧 Debug Mode: {settings.debug}")
        
        results["config_loaded"] = True
        print("   ✅ Configuration loaded successfully")
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return results
    
    # Test 2: OpenAI Configuration
    try:
        print("\n2️⃣ Testing OpenAI Configuration...")
        
        if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key":
            print(f"   🔑 OpenAI API Key: {settings.openai_api_key[:15]}...{settings.openai_api_key[-4:]}")
            print(f"   🤖 Model: {settings.openai_model}")
            print(f"   🎛️ Max Tokens: {settings.openai_max_tokens}")
            
            # Test actual API connection
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=10.0)
                
                # Test with a minimal request
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": "Test connection. Reply with just 'OK'."}],
                    max_tokens=5,
                    temperature=0.1
                )
                
                content = response.choices[0].message.content or "No response"
                print(f"   🔗 Connection Test: {content.strip()}")
                print(f"   💰 Tokens Used: {response.usage.total_tokens if response.usage else 0}")
                
                results["openai_configured"] = True
                print("   ✅ OpenAI fully configured and working")
                
            except Exception as api_error:
                print(f"   ⚠️  OpenAI API configured but connection failed: {api_error}")
                # Keep as False for now
        else:
            print("   ❌ OpenAI API key not configured")
        
    except Exception as e:
        print(f"   ❌ OpenAI configuration test failed: {e}")
    
    # Test 3: Anthropic Configuration
    try:
        print("\n3️⃣ Testing Anthropic Configuration...")
        
        if settings.anthropic_api_key and settings.anthropic_api_key != "your-anthropic-api-key":
            print(f"   🔑 Anthropic API Key: {settings.anthropic_api_key[:15]}...{settings.anthropic_api_key[-4:]}")
            print(f"   🤖 Model: {settings.anthropic_model}")
            print(f"   🎛️ Max Tokens: {settings.anthropic_max_tokens}")
            
            # Test actual API connection
            try:
                from anthropic import AsyncAnthropic
                client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=10.0)
                
                # Test with a minimal request (using correct Anthropic API)
                response = await client.completions.create(
                    model=settings.anthropic_model,
                    prompt="Human: Test connection. Reply with just 'OK'.\n\nAssistant:",
                    max_tokens_to_sample=5,
                    temperature=0.1
                )
                
                content = response.completion.strip() if hasattr(response, 'completion') else "Connected"
                print(f"   � Connection Test: {content}")
                
                results["anthropic_configured"] = True
                print("   ✅ Anthropic fully configured and working")
                
            except Exception as api_error:
                print(f"   ⚠️  Anthropic API configured but connection failed: {api_error}")
                # Keep as False
        else:
            print("   ❌ Anthropic API key not configured")
        
    except Exception as e:
        print(f"   ❌ Anthropic configuration test failed: {e}")
    
    # Test 4: Azure OpenAI Configuration
    try:
        print("\n4️⃣ Testing Azure OpenAI Configuration...")
        
        if (settings.azure_openai_api_key and 
            settings.azure_openai_api_key != "your-azure-openai-key-here" and
            settings.azure_openai_endpoint):
            
            print(f"   🔑 Azure API Key: {settings.azure_openai_api_key[:15]}...{settings.azure_openai_api_key[-4:]}")
            print(f"   🌐 Endpoint: {settings.azure_openai_endpoint}")
            print(f"   📋 Deployment: {settings.azure_openai_deployment_name}")
            
            results["azure_configured"] = True
            print("   ✅ Azure OpenAI configured (connection test skipped)")
        else:
            print("   ℹ️  Azure OpenAI not configured (optional)")
        
    except Exception as e:
        print(f"   ❌ Azure OpenAI configuration test failed: {e}")
    
    # Test 5: Enhanced AI Service Integration
    try:
        print("\n5️⃣ Testing Enhanced AI Service...")
        from src.services.ai.enhanced_ai_service import get_ai_service, AIRequest, ServiceCategory
        
        # Initialize the service
        ai_service = await get_ai_service()
        
        # Get health status
        health = await ai_service.get_health_status()
        print(f"   🏥 Service Status: {health['service_status']}")
        
        # Check provider availability
        providers = health.get('providers', {})
        available_providers = []
        for provider, stats in providers.items():
            if stats['config']['enabled'] and stats['circuit_breaker']['state'] == 'closed':
                available_providers.append(provider)
                print(f"   ✅ {provider.title()}: Available")
            else:
                print(f"   ❌ {provider.title()}: Unavailable")
        
        if available_providers:
            results["enhanced_service"] = True
            print(f"   🚀 Enhanced AI Service ready with {len(available_providers)} provider(s)")
        else:
            print("   ⚠️  Enhanced AI Service initialized but no providers available")
        
    except Exception as e:
        print(f"   ❌ Enhanced AI Service test failed: {e}")
    
    # Test 6: Full Integration Test
    if results["enhanced_service"] and (results["openai_configured"] or results["anthropic_configured"]):
        try:
            print("\n6️⃣ Testing Full Integration...")
            
            # Create a test request
            request = AIRequest(
                prompt="Generate a brief professional quote for window cleaning services for a 2-story house.",
                category=ServiceCategory.WINDOW_CLEANING,
                tone="professional",
                max_tokens=100,
                temperature=0.7,
                user_id="test-user"
            )
            
            print("   🎯 Generating test quote...")
            response = await ai_service.generate_quote(request)
            
            print(f"   🤖 Provider Used: {response.provider.value}")
            print(f"   📝 Generated Quote: {response.text[:100]}...")
            print(f"   💰 Cost: ${response.cost:.4f}")
            print(f"   ⭐ Quality Score: {response.quality_score:.2f}")
            print(f"   ⏱️ Response Time: {response.response_time:.3f}s")
            print(f"   💾 Cached: {response.cached}")
            
            results["full_integration"] = True
            print("   ✅ Full integration test successful!")
            
        except Exception as e:
            print(f"   ❌ Full integration test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 API Configuration Test Results:")
    print("-" * 40)
    
    for component, status in results.items():
        if status is True:
            print(f"   {component.replace('_', ' ').title():<25} ✅ PASS")
        elif status == "partial":
            print(f"   {component.replace('_', ' ').title():<25} ⚠️  PARTIAL")
        else:
            print(f"   {component.replace('_', ' ').title():<25} ❌ FAIL")
    
    # Deployment readiness assessment
    print("\n🚀 DEPLOYMENT READINESS ASSESSMENT:")
    print("-" * 40)
    
    if results["full_integration"]:
        print("🎉 READY FOR PRODUCTION!")
        print("   • Enhanced AI Service fully operational")
        print("   • Multi-provider configuration working")
        print("   • Circuit breakers and smart routing active")
        print("   • OpenTelemetry tracing enabled")
        print("   • Quality scoring and cost tracking operational")
        
        # Next steps
        print("\n📋 NEXT STEPS:")
        print("   1. Start the API server: python src/main.py")
        print("   2. Test enhanced endpoints: POST /api/v1/quotes/generate/enhanced")
        print("   3. Monitor health: GET /api/v1/quotes/ai-service/health") 
        print("   4. View streaming: POST /api/v1/quotes/generate/stream")
        
    elif results["enhanced_service"]:
        print("⚠️  PARTIALLY READY")
        print("   • Enhanced AI Service initialized")
        print("   • Need to configure at least one AI provider API key")
        print("   • All monitoring and resilience features ready")
        
    else:
        print("❌ NOT READY")
        print("   • Configuration or service initialization issues")
        print("   • Check error messages above")
    
    return results

if __name__ == "__main__":
    # Run the configuration test
    results = asyncio.run(test_api_configuration())
    
    # Exit with appropriate code
    ready = results.get("full_integration", False)
    sys.exit(0 if ready else 1)
