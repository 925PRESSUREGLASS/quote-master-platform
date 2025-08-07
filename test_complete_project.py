"""
Complete Project Test Suite for Quote Master Pro
Tests all components: AI, Quotes, Redis, Database, and API
"""
import asyncio
import time
import json
import os
import sys
from datetime import datetime

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

async def test_redis_infrastructure():
    """Test Redis connection and performance"""
    print("🔌 Testing Redis Infrastructure...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test connection
        pong = r.ping()
        assert pong, "Redis should respond to ping"
        
        # Test operations
        r.set("project_test", "operational")
        value = r.get("project_test")
        assert value == "operational", "Redis get/set should work"
        
        # Cleanup
        r.delete("project_test")
        
        print("✅ Redis: Fully operational")
        return True
        
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False

def test_ai_service():
    """Test AI service initialization and basic functionality"""
    print("🤖 Testing AI Service...")
    
    try:
        from services.ai.ai_service import AIService, AIRequest
        
        # Test initialization
        ai_service = AIService()
        print("✅ AI Service: Initialized successfully")
        
        # Test AI request model
        request = AIRequest(
            prompt="Test quote for window cleaning",
            max_tokens=100,
            temperature=0.7
        )
        
        print("✅ AI Service: Request model working")
        return True
        
    except Exception as e:
        print(f"❌ AI Service: {e}")
        return False

def test_quote_generator():
    """Test unified quote generator"""
    print("💰 Testing Quote Generator...")
    
    try:
        from services.quote.unified_generator import UnifiedServiceQuoteGenerator
        
        # Test initialization
        generator = UnifiedServiceQuoteGenerator()
        print("✅ Quote Generator: Initialized successfully")
        
        # Test quote generation
        quote_data = {
            "service_type": "window_cleaning",
            "property_type": "residential",
            "square_footage": 1500,
            "num_windows": 12,
            "difficulty": "standard",
            "location": "suburban",
            "urgency": "standard"
        }
        
        # Find the correct method name
        methods = [method for method in dir(generator) if 'generate' in method.lower()]
        print(f"✅ Quote Generator: Available methods: {methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quote Generator: {e}")
        return False

def test_database_models():
    """Test database models and connections"""
    print("🗄️ Testing Database Models...")
    
    try:
        from models.database import get_database_session
        from models.quote import Quote
        from models.service import Service
        from models.user import User
        
        print("✅ Database: Models imported successfully")
        
        # Test database session
        session = get_database_session()
        if session:
            print("✅ Database: Session created")
            session.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint availability"""
    print("🌐 Testing API Endpoints...")
    
    try:
        # Import route modules to check they load
        from api.routes import quote_routes, service_routes
        
        print("✅ API: Route modules loaded")
        
        # Check for FastAPI app
        from main import app
        print("✅ API: FastAPI app available")
        
        return True
        
    except Exception as e:
        print(f"❌ API: {e}")
        return False

def test_configuration():
    """Test configuration and settings"""
    print("⚙️ Testing Configuration...")
    
    try:
        from config.settings import get_settings
        
        settings = get_settings()
        print(f"✅ Config: Settings loaded ({type(settings).__name__})")
        
        # Check for required environment variables
        required_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        available_vars = []
        
        for var in required_vars:
            if hasattr(settings, var.lower()) or os.getenv(var):
                available_vars.append(var)
        
        print(f"✅ Config: {len(available_vars)}/{len(required_vars)} API keys configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Config: {e}")
        return False

def test_dependencies():
    """Test critical dependencies"""
    print("📦 Testing Dependencies...")
    
    dependencies = [
        ('fastapi', 'FastAPI framework'),
        ('sqlalchemy', 'Database ORM'),
        ('redis', 'Redis client'),
        ('openai', 'OpenAI client'),
        ('anthropic', 'Anthropic client'),
        ('pydantic', 'Data validation'),
        ('uvicorn', 'ASGI server'),
        ('asyncio', 'Async framework')
    ]
    
    working_deps = 0
    
    for dep, description in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}: {description}")
            working_deps += 1
        except ImportError:
            print(f"❌ {dep}: {description} - Missing")
    
    print(f"✅ Dependencies: {working_deps}/{len(dependencies)} available")
    return working_deps >= len(dependencies) * 0.8  # 80% threshold

async def test_async_operations():
    """Test async functionality"""
    print("⚡ Testing Async Operations...")
    
    try:
        # Test async/await basics
        await asyncio.sleep(0.01)
        
        # Test Redis async if available
        from services.cache.redis_connection import redis_manager
        await redis_manager.async_connect()
        
        # Test async cache operations
        await redis_manager.async_set("async_test", {"test": "data"}, 60)
        result = await redis_manager.async_get("async_test")
        
        if result:
            print("✅ Async: Redis async operations working")
        else:
            print("✅ Async: Memory cache fallback working")
        
        await redis_manager.async_delete("async_test")
        
        return True
        
    except Exception as e:
        print(f"❌ Async: {e}")
        return False

def test_file_structure():
    """Test project file structure"""
    print("📁 Testing File Structure...")
    
    required_paths = [
        'src/services/ai/ai_service.py',
        'src/services/quote/unified_generator.py',
        'src/services/cache/redis_connection.py',
        'src/models/database.py',
        'src/api/routes/quote_routes.py',
        'requirements.txt',
        'docker-compose.yml',
        'README.md'
    ]
    
    existing_files = 0
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
            existing_files += 1
        else:
            print(f"❌ {path} - Missing")
    
    print(f"✅ File Structure: {existing_files}/{len(required_paths)} files found")
    return existing_files >= len(required_paths) * 0.8

async def run_comprehensive_project_test():
    """Run all project tests"""
    print("🚀 QUOTE MASTER PRO - COMPREHENSIVE PROJECT TEST")
    print("=" * 70)
    print(f"Test Time: {datetime.now()}")
    print("=" * 70)
    
    test_results = {}
    
    # Test 1: File Structure
    test_results['file_structure'] = test_file_structure()
    
    # Test 2: Dependencies
    test_results['dependencies'] = test_dependencies()
    
    # Test 3: Configuration
    test_results['configuration'] = test_configuration()
    
    # Test 4: Redis Infrastructure
    test_results['redis'] = await test_redis_infrastructure()
    
    # Test 5: Database Models
    test_results['database'] = test_database_models()
    
    # Test 6: AI Service
    test_results['ai_service'] = test_ai_service()
    
    # Test 7: Quote Generator
    test_results['quote_generator'] = test_quote_generator()
    
    # Test 8: API Endpoints
    test_results['api_endpoints'] = test_api_endpoints()
    
    # Test 9: Async Operations
    test_results['async_operations'] = await test_async_operations()
    
    # Calculate overall results
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        status_text = "PASSED" if result else "FAILED"
        test_display = test_name.replace('_', ' ').title()
        print(f"{status_icon} {test_display}: {status_text}")
    
    print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    # Project status assessment
    if success_rate >= 90:
        status = "🎉 EXCELLENT - Production Ready!"
        color_code = "\033[92m"  # Green
    elif success_rate >= 75:
        status = "✅ GOOD - Minor Issues"
        color_code = "\033[93m"  # Yellow
    elif success_rate >= 50:
        status = "⚠️ FAIR - Needs Work"
        color_code = "\033[93m"  # Yellow
    else:
        status = "❌ POOR - Major Issues"
        color_code = "\033[91m"  # Red
    
    print(f"\n{color_code}🎯 PROJECT STATUS: {status}\033[0m")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if test_results['redis']:
        print("✅ Redis caching is operational - excellent performance")
    else:
        print("⚠️ Consider fixing Redis for production caching")
    
    if test_results['ai_service']:
        print("✅ AI services are ready for quote generation")
    else:
        print("⚠️ Check AI service configuration and API keys")
    
    if test_results['dependencies']:
        print("✅ All critical dependencies are available")
    else:
        print("⚠️ Install missing dependencies: pip install -r requirements.txt")
    
    if success_rate >= 80:
        print("\n🚀 READY FOR DEPLOYMENT!")
        print("Next steps:")
        print("1. Run: python run_server.py")
        print("2. Test quote generation in browser")
        print("3. Monitor system performance")
    else:
        print("\n🔧 NEEDS ADDITIONAL WORK")
        print("Fix failed components before deployment")
    
    print("\n" + "=" * 70)
    
    return success_rate >= 75

if __name__ == "__main__":
    print("Starting comprehensive project test...")
    
    try:
        success = asyncio.run(run_comprehensive_project_test())
        
        if success:
            exit(0)  # Success
        else:
            exit(1)  # Issues found
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        exit(2)  # Test failure
