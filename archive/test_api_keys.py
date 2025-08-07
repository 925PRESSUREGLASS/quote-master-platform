"""
API Key Tester for Quote Master Pro
Tests your API keys before running the full system
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_openai_key():
    """Test OpenAI API key"""
    print("🔑 Testing OpenAI API Key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your-openai-api-key-here':
        print("❌ OpenAI API key not set in .env file")
        return False
    
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=api_key)
        
        # Simple test request
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API key working!")
        print(f"   Model: {response.model}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API key error: {e}")
        return False

async def test_anthropic_key():
    """Test Anthropic API key"""
    print("\n🔑 Testing Anthropic API Key...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key == 'your-anthropic-api-key-here':
        print("❌ Anthropic API key not set in .env file")
        return False
    
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        # Simple test request
        response = await client.completions.create(
            model="claude-2",
            prompt="Test",
            max_tokens_to_sample=5
        )
        
        print("✅ Anthropic API key working!")
        return True
        
    except Exception as e:
        print(f"❌ Anthropic API key error: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔗 Testing Redis Connection...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        pong = r.ping()
        
        if pong:
            print("✅ Redis connection working!")
            return True
        else:
            print("❌ Redis not responding")
            return False
            
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Quote Master Pro API Key Tester")
    print("=" * 50)
    
    # Test all components
    openai_ok = await test_openai_key()
    anthropic_ok = await test_anthropic_key()
    redis_ok = test_redis_connection()
    
    print("\n" + "=" * 50)
    print("📊 API KEY TEST RESULTS")
    print("=" * 50)
    
    total_tests = 3
    passed_tests = sum([openai_ok, anthropic_ok, redis_ok])
    
    print(f"OpenAI API:     {'✅ WORKING' if openai_ok else '❌ NEEDS SETUP'}")
    print(f"Anthropic API:  {'✅ WORKING' if anthropic_ok else '❌ NEEDS SETUP'}")
    print(f"Redis Cache:    {'✅ WORKING' if redis_ok else '❌ NEEDS SETUP'}")
    
    print(f"\n📈 Status: {passed_tests}/{total_tests} services working")
    
    if passed_tests >= 2:
        print("\n🎉 READY FOR PRODUCTION!")
        print("✅ At least 2 AI providers working")
        if redis_ok:
            print("✅ Redis caching enabled")
        print("\n▶️  Run: python run_server.py")
        
    elif passed_tests >= 1:
        print("\n⚠️  PARTIALLY READY")
        print("✅ Basic functionality available")
        print("💡 Add more API keys for full redundancy")
        
    else:
        print("\n❌ SETUP REQUIRED")
        print("Please add your API keys to the .env file:")
        print("1. Edit .env file")
        print("2. Replace 'your-api-key-here' with real keys")
        print("3. Run this test again")

if __name__ == "__main__":
    asyncio.run(main())
