#!/usr/bin/env python3
"""
AI Services Validation Script

Validates that all AI services are properly implemented and can be imported.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test all AI service imports."""
    print("🔍 Testing AI Service Imports...")
    
    tests = [
        ("Core Config", "from src.core.config import get_settings"),
        ("AI Service", "from src.services.ai.ai_service import AIService, AIProvider, AIRequest, AIResponse"),
        ("Unified Generator", "from src.services.quote.unified_generator import UnifiedServiceQuoteGenerator"),
        ("Service Quote", "from src.services.quote.service_quote import ServiceQuoteService"),
        ("OpenAI Service", "from src.services.ai.openai_service import OpenAIService"),
        ("Claude Service", "from src.services.ai.claude import ClaudeService"),
    ]
    
    results = []
    
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"✅ {test_name}: Import successful")
            results.append((test_name, True, None))
        except Exception as e:
            print(f"❌ {test_name}: Import failed - {str(e)}")
            results.append((test_name, False, str(e)))
    
    return results

def test_ai_service_functionality():
    """Test basic AI service functionality."""
    print("\n🔍 Testing AI Service Functionality...")
    
    try:
        from src.services.ai.ai_service import AIService, AIProvider, AIRequest
        
        # Test creating AI service instance
        ai_service = AIService()
        print("✅ AI Service instance created successfully")
        
        # Test creating AI request
        request = AIRequest(
            prompt="Generate a professional window cleaning quote",
            context="2-story house with 20 windows in Perth",
            max_tokens=200,
            temperature=0.7
        )
        print("✅ AI Request created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Service functionality test failed: {str(e)}")
        return False

def test_unified_generator():
    """Test unified generator functionality."""
    print("\n🔍 Testing Unified Generator...")
    
    try:
        from src.services.quote.unified_generator import UnifiedServiceQuoteGenerator
        
        # Test creating generator instance
        generator = UnifiedServiceQuoteGenerator()
        print("✅ Unified Generator instance created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified Generator test failed: {str(e)}")
        return False

def check_dependencies():
    """Check required dependencies."""
    print("\n🔍 Checking Dependencies...")
    
    dependencies = [
        "openai",
        "anthropic", 
        "redis",
        "tenacity",
        "textblob",
        "numpy",
        "aiohttp"
    ]
    
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError:
            print(f"❌ {dep}: Missing")
            missing.append(dep)
    
    return missing

def main():
    """Main validation function."""
    print("🚀 Quote Master Pro - AI Services Validation")
    print("=" * 50)
    
    # Test imports
    import_results = test_imports()
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    # Test functionality if imports successful
    functionality_passed = False
    generator_passed = False
    
    if any(result[1] for result in import_results if result[0] == "AI Service"):
        functionality_passed = test_ai_service_functionality()
    
    if any(result[1] for result in import_results if result[0] == "Unified Generator"):
        generator_passed = test_unified_generator()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    total_tests = len(import_results)
    passed_tests = sum(1 for result in import_results if result[1])
    
    print(f"Import Tests: {passed_tests}/{total_tests} passed")
    print(f"AI Service Functionality: {'✅ PASS' if functionality_passed else '❌ FAIL'}")
    print(f"Unified Generator: {'✅ PASS' if generator_passed else '❌ FAIL'}")
    print(f"Missing Dependencies: {len(missing_deps)}")
    
    if missing_deps:
        print(f"Missing: {', '.join(missing_deps)}")
    
    overall_status = (
        passed_tests == total_tests and 
        not missing_deps and 
        functionality_passed and 
        generator_passed
    )
    
    if overall_status:
        print("\n🎉 ALL TESTS PASSED - AI Services are ready!")
        return 0
    else:
        print("\n⚠️  Some tests failed - Review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
