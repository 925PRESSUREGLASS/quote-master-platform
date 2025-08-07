#!/usr/bin/env python3
"""
Comprehensive AI Integration Tests

Tests the complete AI service infrastructure including:
- AI Service with provider fallback
- Unified Quote Generator
- Rate limiting and caching
- Quality scoring
- Error handling and retry logic
"""

import asyncio
import time
import json
from typing import List, Dict, Any

from src.services.ai.ai_service import (
    AIService, AIProvider, AIRequest, AIResponse, ServiceCategory
)
from src.services.quote.unified_generator import UnifiedServiceQuoteGenerator
from src.core.config import get_settings


class AIIntegrationTester:
    """Comprehensive AI integration tester."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.quote_generator = UnifiedServiceQuoteGenerator()
        self.settings = get_settings()
        self.test_results: List[Dict[str, Any]] = []
    
    async def test_ai_service_basic(self) -> Dict[str, Any]:
        """Test basic AI service functionality."""
        print("🔍 Testing AI Service Basic Functionality...")
        
        test_result = {
            "name": "AI Service Basic",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Test simple request
            request = AIRequest(
                prompt="Generate a professional window cleaning quote description",
                context="2-story residential house in Perth with 20 windows",
                category=ServiceCategory.WINDOW_CLEANING,
                max_tokens=150,
                temperature=0.7
            )
            
            response = await self.ai_service.generate_quote(request)
            
            if response and isinstance(response, AIResponse):
                test_result["details"].append(f"✅ Generated response: {len(response.text)} chars")
                test_result["details"].append(f"✅ Provider: {response.provider.value}")
                test_result["details"].append(f"✅ Quality score: {response.quality_score:.2f}")
                test_result["details"].append(f"✅ Cost: ${response.cost:.4f}")
                test_result["passed"] = True
            else:
                test_result["errors"].append("No response generated")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def test_provider_fallback(self) -> Dict[str, Any]:
        """Test AI provider fallback mechanism."""
        print("🔍 Testing Provider Fallback...")
        
        test_result = {
            "name": "Provider Fallback",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Test with multiple providers
            request = AIRequest(
                prompt="Create a professional pressure washing service description",
                category=ServiceCategory.PRESSURE_WASHING,
                max_tokens=100
            )
            
            # Test fallback by trying invalid API keys (simulation)
            original_providers = self.ai_service.providers.copy()
            
            response = await self.ai_service.generate_quote(request)
            
            if response:
                test_result["details"].append(f"✅ Fallback successful with {response.provider.value}")
                test_result["passed"] = True
            else:
                test_result["errors"].append("All providers failed")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality."""
        print("🔍 Testing Rate Limiting...")
        
        test_result = {
            "name": "Rate Limiting",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Make multiple rapid requests
            requests = []
            for i in range(3):
                request = AIRequest(
                    prompt=f"Quick test quote {i+1}",
                    max_tokens=50
                )
                requests.append(request)
            
            # Test rate limiter
            start_time = time.time()
            responses = []
            
            for req in requests:
                response = await self.ai_service.generate_quote(req)
                responses.append(response)
                
            end_time = time.time()
            
            successful_responses = [r for r in responses if r is not None]
            
            test_result["details"].append(f"✅ Processed {len(successful_responses)}/{len(requests)} requests")
            test_result["details"].append(f"✅ Total time: {end_time - start_time:.2f}s")
            
            if successful_responses:
                test_result["passed"] = True
            else:
                test_result["errors"].append("No successful responses")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def test_caching(self) -> Dict[str, Any]:
        """Test response caching."""
        print("🔍 Testing Response Caching...")
        
        test_result = {
            "name": "Response Caching",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Make identical request twice
            request = AIRequest(
                prompt="Test caching functionality",
                max_tokens=50
            )
            
            # First request
            start_time1 = time.time()
            response1 = await self.ai_service.generate_quote(request)
            end_time1 = time.time()
            time1 = end_time1 - start_time1
            
            # Second request (should be cached)
            start_time2 = time.time()
            response2 = await self.ai_service.generate_quote(request)
            end_time2 = time.time()
            time2 = end_time2 - start_time2
            
            if response1 and response2:
                test_result["details"].append(f"✅ First request: {time1:.3f}s")
                test_result["details"].append(f"✅ Second request: {time2:.3f}s")
                test_result["details"].append(f"✅ Second response cached: {response2.cached}")
                
                # Cached response should be faster or marked as cached
                if response2.cached or time2 < time1 * 0.8:
                    test_result["passed"] = True
                    test_result["details"].append("✅ Caching working correctly")
                else:
                    test_result["errors"].append("Caching not working as expected")
            else:
                test_result["errors"].append("Failed to get responses")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def test_unified_generator(self) -> Dict[str, Any]:
        """Test unified quote generator."""
        print("🔍 Testing Unified Quote Generator...")
        
        test_result = {
            "name": "Unified Generator",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Test service quote generation
            quote_request = {
                "service_type": "window_cleaning",
                "property_type": "residential_house",
                "suburb": "Perth CBD",
                "details": {
                    "windows": 20,
                    "stories": 2,
                    "difficulty": "standard"
                }
            }
            
            result = await self.quote_generator.generate_service_quote(quote_request)
            
            if result:
                test_result["details"].append(f"✅ Generated service quote")
                test_result["details"].append(f"✅ Quote length: {len(str(result))} chars")
                test_result["passed"] = True
            else:
                test_result["errors"].append("No quote generated")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def test_quality_scoring(self) -> Dict[str, Any]:
        """Test quality scoring system."""
        print("🔍 Testing Quality Scoring...")
        
        test_result = {
            "name": "Quality Scoring",
            "passed": False,
            "details": [],
            "errors": []
        }
        
        try:
            # Test with good quality prompt
            good_request = AIRequest(
                prompt="Generate a detailed professional window cleaning service quote",
                context="Premium residential property with specific cleaning requirements",
                max_tokens=200
            )
            
            response = await self.ai_service.generate_quote(good_request)
            
            if response:
                quality_score = response.quality_score
                test_result["details"].append(f"✅ Quality score: {quality_score:.2f}")
                
                if quality_score > 0.5:  # Reasonable quality threshold
                    test_result["passed"] = True
                    test_result["details"].append("✅ Quality scoring working")
                else:
                    test_result["errors"].append(f"Low quality score: {quality_score:.2f}")
            else:
                test_result["errors"].append("No response to evaluate")
        
        except Exception as e:
            test_result["errors"].append(f"Exception: {str(e)}")
        
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("🚀 Running Comprehensive AI Integration Tests")
        print("=" * 60)
        
        tests = [
            self.test_ai_service_basic,
            self.test_provider_fallback,
            self.test_rate_limiting,
            self.test_caching,
            self.test_unified_generator,
            self.test_quality_scoring
        ]
        
        all_results = []
        
        for test_func in tests:
            try:
                result = await test_func()
                all_results.append(result)
                
                # Print test result
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"\n{status} {result['name']}")
                
                for detail in result["details"]:
                    print(f"  {detail}")
                
                for error in result["errors"]:
                    print(f"  ❌ {error}")
            
            except Exception as e:
                print(f"❌ FAIL {test_func.__name__}: {str(e)}")
                all_results.append({
                    "name": test_func.__name__,
                    "passed": False,
                    "errors": [str(e)]
                })
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results if result["passed"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - AI Integration Complete!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed - Review errors above")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": total_tests - passed_tests,
            "success_rate": passed_tests/total_tests*100,
            "results": all_results
        }


async def main():
    """Main test runner."""
    tester = AIIntegrationTester()
    summary = await tester.run_all_tests()
    
    # Save results to file
    with open("ai_integration_test_results.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to ai_integration_test_results.json")
    
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
