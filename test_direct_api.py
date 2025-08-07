"""
Simple API Key Test - Direct Connection Test
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_direct_connections():
    """Test direct API connections without our enhanced service."""
    
    print("🔧 Direct API Connection Test")
    print("=" * 40)
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your-openai-api-key":
        print(f"\n1️⃣ Testing OpenAI Direct Connection...")
        try:
            import openai
            print(f"   📦 OpenAI Library Version: {openai.__version__}")
            
            # Use sync client for simplicity
            client = openai.OpenAI(api_key=openai_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for testing
                messages=[{"role": "user", "content": "Say 'OpenAI working'"}],
                max_tokens=10
            )
            
            print(f"   ✅ OpenAI Response: {response.choices[0].message.content}")
            print(f"   💰 Tokens: {response.usage.total_tokens}")
            
        except Exception as e:
            print(f"   ❌ OpenAI Error: {e}")
    
    # Test Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key != "your-anthropic-api-key":
        print(f"\n2️⃣ Testing Anthropic Direct Connection...")
        try:
            import anthropic
            print(f"   📦 Anthropic Library Version: {anthropic.__version__}")
            
            # Use sync client for simplicity
            client = anthropic.Anthropic(api_key=anthropic_key)
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'Anthropic working'"}]
            )
            
            print(f"   ✅ Anthropic Response: {response.content[0].text if hasattr(response.content[0], 'text') else 'Connected successfully'}")
            
        except Exception as e:
            print(f"   ❌ Anthropic Error: {e}")
    
    print(f"\n🎯 Direct connection test complete!")

if __name__ == "__main__":
    asyncio.run(test_direct_connections())
