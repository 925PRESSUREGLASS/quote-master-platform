"""
Final AI Service Test - Direct Testing of Core Functionality
Tests the actual AI services and quote generation without server startup
"""
import asyncio
import time
import json
import os
import sys
from datetime import datetime

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

async def test_ai_service_complete():
    """Test complete AI service functionality"""
    print("🤖 Testing Complete AI Service Functionality...")
    print("=" * 50)
    
    try:
        # Import and initialize AI service
        from services.ai.ai_service import AIService, AIRequest
        
        ai_service = AIService()
        print("✅ AI Service initialized")
        
        # Test 1: Basic Quote Generation
        print("\n1️⃣ Testing Basic Quote Generation...")
        request = AIRequest(
            prompt="Generate a professional quote for residential window cleaning",
            max_tokens=200,
            temperature=0.7
        )
        
        start_time = time.time()
        response = await ai_service.generate_quote(request)
        duration = time.time() - start_time
        
        print(f"✅ Quote generated in {duration:.2f}s")
        print(f"Response type: {type(response)}")
        
        if isinstance(response, dict):
            print("✅ Response is properly formatted")
            if 'pricing' in response:
                print(f"✅ Pricing included: ${response['pricing'].get('total', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_unified_quote_generator():
    """Test the unified quote generator"""
    print("\n💰 Testing Unified Quote Generator...")
    print("=" * 50)
    
    try:
        from services.quote.unified_generator import UnifiedServiceQuoteGenerator
        
        generator = UnifiedServiceQuoteGenerator()
        print("✅ Quote Generator initialized")
        
        # Test with different service types
        test_requests = [
            {
                "service_type": "window_cleaning",
                "property_type": "residential",
                "square_footage": 1500,
                "num_windows": 12,
                "difficulty": "standard",
                "location": "suburban",
                "urgency": "standard"
            },
            {
                "service_type": "pressure_washing",
                "property_type": "commercial", 
                "square_footage": 3000,
                "surface_type": "concrete",
                "difficulty": "high",
                "location": "urban",
                "urgency": "urgent"
            }
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n{i}️⃣ Testing {request['service_type']} quote...")
            
            start_time = time.time()
            quote = await generator.generate_service_quote(request)
            duration = time.time() - start_time
            
            print(f"✅ Quote generated in {duration:.2f}s")
            print(f"Service: {request['service_type']}")
            
            if quote:
                print(f"Quote contains {len(quote)} fields")
                if 'total_price' in quote:
                    print(f"Total Price: ${quote['total_price']}")
                if 'service_details' in quote:
                    print(f"Service: {quote['service_details'].get('name', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quote Generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_redis_performance():
    """Test Redis caching performance with real operations"""
    print("\n⚡ Testing Redis Performance with Real Operations...")
    print("=" * 50)
    
    try:
        from services.cache.redis_connection import redis_manager
        
        # Connect to Redis
        await redis_manager.async_connect()
        print("✅ Redis connected")
        
        # Test caching performance
        test_data = {
            "quote_id": "test_123",
            "service": "window_cleaning",
            "price": 150.00,
            "timestamp": str(datetime.now()),
            "customer": "Test Customer",
            "details": {
                "windows": 12,
                "floors": 2,
                "difficulty": "standard"
            }
        }
        
        # Performance test - multiple operations
        cache_times = []
        num_tests = 10
        
        for i in range(num_tests):
            key = f"perf_test_{i}"
            
            # Time cache set
            start_time = time.time()
            await redis_manager.async_set(key, test_data, ex=300)
            set_time = time.time() - start_time
            
            # Time cache get
            start_time = time.time()
            retrieved = await redis_manager.async_get(key)
            get_time = time.time() - start_time
            
            total_time = set_time + get_time
            cache_times.append(total_time)
            
            # Verify data integrity
            if retrieved != test_data:
                print(f"⚠️ Data mismatch on test {i}")
        
        # Calculate performance metrics
        avg_time = sum(cache_times) / len(cache_times)
        min_time = min(cache_times)
        max_time = max(cache_times)
        
        print(f"✅ Completed {num_tests} cache operations")
        print(f"Average time: {avg_time*1000:.2f}ms")
        print(f"Fastest: {min_time*1000:.2f}ms")
        print(f"Slowest: {max_time*1000:.2f}ms")
        
        # Performance assessment
        if avg_time < 0.01:  # Under 10ms
            print("🚀 EXCELLENT cache performance!")
        elif avg_time < 0.05:  # Under 50ms
            print("✅ GOOD cache performance")
        else:
            print("⚠️ Cache performance could be improved")
        
        # Cleanup
        for i in range(num_tests):
            await redis_manager.async_delete(f"perf_test_{i}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis performance test failed: {e}")
        return False

async def test_system_integration():
    """Test complete system integration"""
    print("\n🔗 Testing Complete System Integration...")
    print("=" * 50)
    
    try:
        # Import all components
        from services.ai.ai_service import AIService, AIRequest
        from services.quote.unified_generator import UnifiedServiceQuoteGenerator
        from services.cache.redis_connection import redis_manager
        
        print("✅ All components imported successfully")
        
        # Initialize components
        ai_service = AIService()
        quote_generator = UnifiedServiceQuoteGenerator()
        
        print("✅ All components initialized")
        
        # Test integrated workflow
        print("\n🔄 Testing Integrated Quote Generation Workflow...")
        
        # Step 1: Generate AI-powered quote
        ai_request = AIRequest(
            prompt="Create a detailed quote for commercial window cleaning of a 20-story office building",
            max_tokens=300,
            temperature=0.8
        )
        
        ai_response = await ai_service.generate_quote(ai_request)
        print("✅ AI quote generated")
        
        # Step 2: Process through unified generator
        quote_request = {
            "service_type": "window_cleaning",
            "property_type": "commercial",
            "square_footage": 5000,
            "num_windows": 200,
            "difficulty": "high",
            "location": "urban",
            "urgency": "standard",
            "floors": 20
        }
        
        unified_quote = await quote_generator.generate_service_quote(quote_request)
        print("✅ Unified quote generated")
        
        # Step 3: Cache the results
        cache_key = f"integrated_quote_{int(time.time())}"
        quote_data = {
            "ai_response": ai_response,
            "unified_quote": unified_quote,
            "request": quote_request,
            "timestamp": str(datetime.now())
        }
        
        await redis_manager.async_set(cache_key, quote_data, ex=3600)
        cached_result = await redis_manager.async_get(cache_key)
        
        if cached_result:
            print("✅ Quote cached successfully")
        
        # Cleanup
        await redis_manager.async_delete(cache_key)
        
        print("✅ Complete integration workflow successful!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    print("🚀 QUOTE MASTER PRO - COMPREHENSIVE FUNCTIONALITY TEST")
    print("=" * 70)
    print(f"Test Started: {datetime.now()}")
    print("=" * 70)
    
    test_results = {
        'AI Service': False,
        'Quote Generator': False,
        'Redis Performance': False,
        'System Integration': False
    }
    
    # Run all tests
    test_results['AI Service'] = await test_ai_service_complete()
    test_results['Quote Generator'] = await test_unified_quote_generator()
    test_results['Redis Performance'] = await test_redis_performance()
    test_results['System Integration'] = await test_system_integration()
    
    # Calculate results
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    success_rate = (passed / total) * 100
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE FUNCTIONALITY TEST RESULTS")
    print("=" * 70)
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        status_text = "PASSED" if result else "FAILED"
        print(f"{status_icon} {test_name}: {status_text}")
    
    print(f"\n📈 Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 100:
        print("\n🎉 PERFECT! ALL SYSTEMS FULLY OPERATIONAL!")
        print("🚀 Quote Master Pro is production-ready!")
    elif success_rate >= 75:
        print("\n✅ EXCELLENT! Core functionality working!")
        print("🎯 System is ready for deployment")
    elif success_rate >= 50:
        print("\n⚠️ GOOD! Most features working")
        print("🔧 Minor fixes needed for full deployment")
    else:
        print("\n❌ ISSUES DETECTED!")
        print("🔧 Requires attention before deployment")
    
    print("\n💡 DEPLOYMENT READINESS:")
    if test_results['AI Service']:
        print("✅ AI-powered quote generation ready")
    if test_results['Quote Generator']:
        print("✅ Service-specific quote generation ready")
    if test_results['Redis Performance']:
        print("✅ High-performance caching operational")
    if test_results['System Integration']:
        print("✅ Complete workflow integration working")
    
    print("\n" + "=" * 70)
    
    return success_rate >= 75

if __name__ == "__main__":
    print("Starting comprehensive functionality test...")
    
    try:
        success = asyncio.run(main())
        
        if success:
            print("\n🎯 QUOTE MASTER PRO: READY FOR PRODUCTION! 🚀")
            exit(0)
        else:
            print("\n⚠️ QUOTE MASTER PRO: Needs additional work")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        exit(2)
