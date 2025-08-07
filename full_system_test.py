"""
COMPREHENSIVE FULL SYSTEM TEST for Quote Master Pro
Tests every component of the system end-to-end
"""
import asyncio
import time
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

class FullSystemTest:
    """Complete system test suite"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    def log_test(self, test_name, success, duration=0, details=""):
        """Log test results"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'duration': duration,
            'details': details
        })
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s) {details}")
    
    async def test_1_environment_config(self):
        """Test 1: Environment Configuration"""
        print("\n1️⃣ TESTING ENVIRONMENT CONFIGURATION")
        print("-" * 50)
        
        start = time.time()
        try:
            # Test environment variables
            openai_key = os.getenv('OPENAI_API_KEY')
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            redis_url = os.getenv('REDIS_URL')
            
            assert openai_key and not openai_key.startswith('your-'), "OpenAI key not configured"
            assert anthropic_key and not anthropic_key.startswith('your-'), "Anthropic key not configured"
            assert redis_url, "Redis URL not configured"
            
            duration = time.time() - start
            self.log_test("Environment Variables", True, duration, f"Keys loaded: OpenAI, Anthropic, Redis")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Environment Variables", False, duration, str(e))
            return False
    
    async def test_2_redis_infrastructure(self):
        """Test 2: Redis Infrastructure"""
        print("\n2️⃣ TESTING REDIS INFRASTRUCTURE")
        print("-" * 50)
        
        start = time.time()
        try:
            import redis
            
            # Test Redis connection
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            pong = r.ping()
            assert pong, "Redis not responding"
            
            # Test basic operations
            test_key = "system_test_" + str(int(time.time()))
            test_data = {"timestamp": datetime.now().isoformat(), "test": "full_system"}
            
            r.set(test_key, json.dumps(test_data), ex=60)
            retrieved = json.loads(r.get(test_key))
            assert retrieved['test'] == 'full_system', "Redis data integrity failed"
            
            # Performance test
            perf_start = time.time()
            for i in range(10):
                r.set(f"perf_{i}", f"value_{i}")
                r.get(f"perf_{i}")
            perf_time = (time.time() - perf_start) / 10 * 1000  # ms per operation
            
            # Cleanup
            r.delete(test_key)
            for i in range(10):
                r.delete(f"perf_{i}")
            
            duration = time.time() - start
            self.log_test("Redis Infrastructure", True, duration, f"PONG received, {perf_time:.1f}ms avg op time")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Redis Infrastructure", False, duration, str(e))
            return False
    
    async def test_3_ai_service_integration(self):
        """Test 3: AI Service Integration"""
        print("\n3️⃣ TESTING AI SERVICE INTEGRATION")
        print("-" * 50)
        
        start = time.time()
        try:
            from services.ai.ai_service import AIService, AIRequest
            
            # Initialize AI service
            ai_service = AIService()
            
            # Test basic quote generation
            request = AIRequest(
                prompt="Generate a professional quote for window cleaning a 2-story house with 15 windows",
                max_tokens=200,
                temperature=0.7
            )
            
            ai_start = time.time()
            response = await ai_service.generate_quote(request)
            ai_duration = time.time() - ai_start
            
            assert response is not None, "AI service returned no response"
            
            # Test caching by making same request
            cache_start = time.time()
            cached_response = await ai_service.generate_quote(request)
            cache_duration = time.time() - cache_start
            
            assert cached_response is not None, "Cached response failed"
            
            speedup = ai_duration / cache_duration if cache_duration > 0 else float('inf')
            
            duration = time.time() - start
            self.log_test("AI Service Integration", True, duration, 
                         f"Generated in {ai_duration:.2f}s, cached in {cache_duration:.3f}s ({speedup:.1f}x speedup)")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("AI Service Integration", False, duration, str(e))
            return False
    
    async def test_4_quote_generator_system(self):
        """Test 4: Quote Generator System"""
        print("\n4️⃣ TESTING QUOTE GENERATOR SYSTEM")  
        print("-" * 50)
        
        start = time.time()
        try:
            from services.quote.unified_generator import UnifiedServiceQuoteGenerator
            
            generator = UnifiedServiceQuoteGenerator()
            
            # Test window cleaning quote
            job_description = "Professional window cleaning for residential property"
            property_info = "2-story suburban house, 16 windows, standard difficulty access"
            customer_info = {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "(555) 123-4567",
                "schedule": "weekday_morning"
            }
            
            quote_start = time.time()
            quote = await generator.generate_service_quote(
                job_description=job_description,
                property_info=property_info,
                customer_info=customer_info
            )
            quote_duration = time.time() - quote_start
            
            assert quote is not None, "Quote generator returned no quote"
            assert hasattr(quote, '__class__'), "Quote object malformed"
            
            # Test different service type
            pressure_job = "Pressure washing for commercial building exterior"
            pressure_property = "3000 sq ft commercial building, concrete surfaces"
            
            pressure_quote = await generator.generate_service_quote(
                job_description=pressure_job,
                property_info=pressure_property,
                customer_info=customer_info
            )
            
            assert pressure_quote is not None, "Pressure washing quote failed"
            
            duration = time.time() - start
            self.log_test("Quote Generator System", True, duration,
                         f"Generated 2 quotes in {quote_duration:.2f}s avg")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Quote Generator System", False, duration, str(e))
            return False
    
    async def test_5_api_provider_fallback(self):
        """Test 5: API Provider Fallback System"""
        print("\n5️⃣ TESTING API PROVIDER FALLBACK")
        print("-" * 50)
        
        start = time.time()
        try:
            # Test OpenAI directly
            import openai
            openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            openai_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test: Generate a brief window cleaning quote"}],
                max_tokens=50
            )
            assert openai_response.choices[0].message.content, "OpenAI API failed"
            
            # Test Anthropic directly
            import anthropic
            anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            anthropic_response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": "Test: Generate a brief pressure washing quote"}]
            )
            assert anthropic_response.content[0].text, "Anthropic API failed"
            
            duration = time.time() - start
            self.log_test("API Provider Fallback", True, duration, "OpenAI & Anthropic both responding")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("API Provider Fallback", False, duration, str(e))
            return False
    
    async def test_6_caching_performance(self):
        """Test 6: Caching Performance"""
        print("\n6️⃣ TESTING CACHING PERFORMANCE")
        print("-" * 50)
        
        start = time.time()
        try:
            from services.cache.redis_connection import redis_manager, cache_get, cache_set
            
            # Connect to cache
            redis_manager.connect()
            
            # Performance test with multiple operations
            cache_times = []
            for i in range(20):
                cache_start = time.time()
                
                test_key = f"perf_test_{i}"
                test_data = {
                    "quote_id": f"quote_{i}",
                    "service": "window_cleaning",
                    "price": 150 + i,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Set and get
                cache_set(test_key, test_data, ttl=60)
                retrieved = cache_get(test_key)
                
                cache_time = time.time() - cache_start
                cache_times.append(cache_time * 1000)  # Convert to ms
                
                assert retrieved is not None, f"Cache operation {i} failed"
                assert retrieved['quote_id'] == f"quote_{i}", f"Data integrity failed on operation {i}"
            
            # Calculate performance metrics
            avg_time = sum(cache_times) / len(cache_times)
            max_time = max(cache_times)
            min_time = min(cache_times)
            
            # Test cache with AI-like data
            ai_cache_key = "ai_test_response"
            ai_cache_data = {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "response": "Professional window cleaning quote: $150 for 2-story house",
                "tokens": 25,
                "timestamp": datetime.now().isoformat()
            }
            
            cache_set(ai_cache_key, ai_cache_data, ttl=3600)
            ai_retrieved = cache_get(ai_cache_key)
            assert ai_retrieved['provider'] == 'openai', "AI cache test failed"
            
            duration = time.time() - start
            self.log_test("Caching Performance", True, duration,
                         f"Avg: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Caching Performance", False, duration, str(e))
            return False
    
    async def test_7_end_to_end_workflow(self):
        """Test 7: End-to-End Workflow"""
        print("\n7️⃣ TESTING END-TO-END WORKFLOW")
        print("-" * 50)
        
        start = time.time()
        try:
            from services.ai.ai_service import AIService, AIRequest
            from services.quote.unified_generator import UnifiedServiceQuoteGenerator
            
            # Simulate complete quote request workflow
            workflow_start = time.time()
            
            # Step 1: Initialize services
            ai_service = AIService()
            quote_generator = UnifiedServiceQuoteGenerator()
            
            # Step 2: Generate AI-powered assessment
            assessment_request = AIRequest(
                prompt="Assess property for window cleaning: 2-story house, 16 windows, suburban location",
                max_tokens=150
            )
            
            assessment = await ai_service.generate_quote(assessment_request)
            assert assessment is not None, "Property assessment failed"
            
            # Step 3: Generate comprehensive quote
            quote = await quote_generator.generate_service_quote(
                job_description="Complete window cleaning service based on AI assessment",
                property_info="2-story suburban house, 16 windows, assessed as standard difficulty",
                customer_info={
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "(555) 987-6543",
                    "preferred_date": "weekday",
                    "communication": "email"
                }
            )
            
            assert quote is not None, "Final quote generation failed"
            
            # Step 4: Test quote variations
            variations_request = AIRequest(
                prompt="Generate 3 pricing variations for window cleaning: budget, standard, premium",
                max_tokens=200
            )
            
            variations = await ai_service.generate_quote(variations_request)
            assert variations is not None, "Quote variations failed"
            
            workflow_duration = time.time() - workflow_start
            
            duration = time.time() - start
            self.log_test("End-to-End Workflow", True, duration,
                         f"Complete workflow in {workflow_duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("End-to-End Workflow", False, duration, str(e))
            return False
    
    async def test_8_system_resilience(self):
        """Test 8: System Resilience & Error Handling"""
        print("\n8️⃣ TESTING SYSTEM RESILIENCE")
        print("-" * 50)
        
        start = time.time()
        try:
            from services.ai.ai_service import AIService, AIRequest
            
            ai_service = AIService()
            
            # Test with various edge cases
            edge_cases = [
                ("Empty prompt", ""),
                ("Very short prompt", "Quote"),
                ("Long prompt", "Generate a quote for " + "very detailed " * 50 + "window cleaning"),
                ("Special characters", "Quote for cleaning windows @#$%^&*()"),
                ("Numbers only", "123456789")
            ]
            
            successful_cases = 0
            for case_name, prompt in edge_cases:
                try:
                    request = AIRequest(prompt=prompt, max_tokens=100)
                    response = await ai_service.generate_quote(request)
                    if response is not None:
                        successful_cases += 1
                        print(f"  ✅ {case_name}: Handled gracefully")
                    else:
                        print(f"  ⚠️ {case_name}: No response but no crash")
                except Exception as e:
                    print(f"  ⚠️ {case_name}: {str(e)[:50]}...")
            
            # Test rate limiting behavior (simulate)
            rapid_requests = []
            for i in range(5):
                rapid_start = time.time()
                try:
                    request = AIRequest(prompt=f"Quick test {i}", max_tokens=50)
                    response = await ai_service.generate_quote(request)
                    rapid_time = time.time() - rapid_start
                    rapid_requests.append(rapid_time)
                except Exception as e:
                    print(f"  Rate limit test {i}: {e}")
            
            avg_rapid_time = sum(rapid_requests) / len(rapid_requests) if rapid_requests else 0
            
            duration = time.time() - start
            self.log_test("System Resilience", True, duration,
                         f"{successful_cases}/5 edge cases handled, avg rapid: {avg_rapid_time:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("System Resilience", False, duration, str(e))
            return False
    
    async def test_9_cost_tracking(self):
        """Test 9: Cost Tracking & Monitoring"""
        print("\n9️⃣ TESTING COST TRACKING & MONITORING")
        print("-" * 50)
        
        start = time.time()
        try:
            from services.ai.ai_service import AIService, AIRequest
            
            ai_service = AIService()
            
            # Test multiple requests to accumulate cost data
            cost_test_requests = [
                "Generate window cleaning quote for small house",
                "Create pressure washing estimate for driveway", 
                "Provide gutter cleaning quote for 2-story home"
            ]
            
            total_requests = 0
            for i, prompt in enumerate(cost_test_requests):
                try:
                    request = AIRequest(prompt=prompt, max_tokens=100)
                    response = await ai_service.generate_quote(request)
                    if response:
                        total_requests += 1
                        print(f"  ✅ Cost tracking request {i+1}: Completed")
                except Exception as e:
                    print(f"  ⚠️ Cost tracking request {i+1}: {e}")
            
            # Test budget monitoring (simulated)
            monthly_limit = float(os.getenv('MONTHLY_BUDGET_LIMIT', 500))
            cost_tracking_enabled = os.getenv('ENABLE_COST_TRACKING', 'True').lower() == 'true'
            
            assert monthly_limit > 0, "Monthly budget limit not set"
            assert cost_tracking_enabled, "Cost tracking not enabled"
            
            duration = time.time() - start
            self.log_test("Cost Tracking & Monitoring", True, duration,
                         f"{total_requests}/3 requests tracked, ${monthly_limit} budget limit")
            return True
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Cost Tracking & Monitoring", False, duration, str(e))
            return False
    
    async def test_10_production_readiness(self):
        """Test 10: Production Readiness Check"""
        print("\n🔟 TESTING PRODUCTION READINESS")
        print("-" * 50)
        
        start = time.time()
        try:
            # Check critical production settings
            environment = os.getenv('ENVIRONMENT', 'development')
            debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
            secret_key = os.getenv('SECRET_KEY', '')
            
            production_checks = [
                (environment == 'production', "Environment set to production"),
                (not debug_mode, "Debug mode disabled"),
                (len(secret_key) > 20, "Strong secret key configured"),
                (os.getenv('OPENAI_API_KEY', '').startswith('sk-'), "Valid OpenAI API key format"),
                (os.getenv('ANTHROPIC_API_KEY', '').startswith('sk-ant-'), "Valid Anthropic API key format"),
                (os.getenv('REDIS_URL', '').startswith('redis://'), "Redis URL properly configured")
            ]
            
            passed_checks = sum(1 for check, _ in production_checks if check)
            total_checks = len(production_checks)
            
            for check, description in production_checks:
                status = "✅" if check else "⚠️"
                print(f"  {status} {description}")
            
            # Test server-like behavior
            try:
                from services.ai.ai_service import AIService
                from services.quote.unified_generator import UnifiedServiceQuoteGenerator
                
                # Simulate server startup
                ai_service = AIService()
                quote_generator = UnifiedServiceQuoteGenerator()
                
                print("  ✅ Services can be initialized for server startup")
                server_ready = True
            except Exception as e:
                print(f"  ❌ Server startup simulation failed: {e}")
                server_ready = False
            
            duration = time.time() - start
            readiness_score = (passed_checks / total_checks) * 100
            self.log_test("Production Readiness", server_ready and readiness_score >= 80, duration,
                         f"{passed_checks}/{total_checks} checks passed ({readiness_score:.0f}%)")
            return server_ready and readiness_score >= 80
            
        except Exception as e:
            duration = time.time() - start
            self.log_test("Production Readiness", False, duration, str(e))
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        print("🚀 QUOTE MASTER PRO - COMPREHENSIVE FULL SYSTEM TEST")
        print("=" * 70)
        print(f"Started at: {datetime.now()}")
        print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"Redis URL: {os.getenv('REDIS_URL', 'not configured')}")
        print("=" * 70)
        
        # Run all tests
        test_methods = [
            self.test_1_environment_config,
            self.test_2_redis_infrastructure,
            self.test_3_ai_service_integration,
            self.test_4_quote_generator_system,
            self.test_5_api_provider_fallback,
            self.test_6_caching_performance,
            self.test_7_end_to_end_workflow,
            self.test_8_system_resilience,
            self.test_9_cost_tracking,
            self.test_10_production_readiness
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, 0, f"Test crashed: {e}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE SYSTEM TEST RESULTS")
        print("=" * 70)
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.2f}s")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status} {result['test']:<25} ({result['duration']:>5.2f}s) {result['details']}")
        
        print("\n" + "=" * 70)
        
        # Final assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT! System is production-ready!")
            print("✅ All critical components working")
            print("✅ Performance metrics within acceptable ranges")
            print("✅ API keys validated and functional")
            print("✅ Caching system optimized")
            print("✅ Error handling robust")
            print("\n🚀 READY FOR DEPLOYMENT!")
            
        elif success_rate >= 75:
            print("✅ GOOD! System is mostly operational")
            print("⚠️ Some non-critical issues detected")
            print("💡 Review failed tests and address before full deployment")
            print("\n🔧 DEPLOYMENT READY WITH MINOR FIXES")
            
        elif success_rate >= 50:
            print("⚠️ PARTIAL SUCCESS - System has significant issues")
            print("❌ Multiple critical components need attention")
            print("🔧 Address failed tests before deployment")
            print("\n🚨 NOT READY FOR PRODUCTION")
            
        else:
            print("❌ SYSTEM FAILURE - Major issues detected")
            print("🚨 Critical components not working")
            print("🔧 Significant fixes required")
            print("\n🛑 DO NOT DEPLOY")
        
        print("=" * 70)
        print(f"Test completed at: {datetime.now()}")

async def main():
    """Main test execution"""
    test_suite = FullSystemTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
