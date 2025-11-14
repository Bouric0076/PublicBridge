#!/usr/bin/env python3
"""
Simple test script to verify the chatbot API is working.
Run this to debug chatbot connectivity issues.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

def test_environment_variables():
    """Test if environment variables are properly loaded."""
    print("=== Testing Environment Variables ===")
    
    groq_key = os.getenv('GROQ_API_KEY')
    debug = os.getenv('DEBUG')
    secret_key = os.getenv('SECRET_KEY')
    
    print(f"GROQ_API_KEY: {'✓ Set' if groq_key else '✗ Missing'}")
    print(f"DEBUG: {debug}")
    print(f"SECRET_KEY: {'✓ Set' if secret_key else '✗ Missing'}")
    print()

def test_groq_orchestrator():
    """Test if Groq orchestrator can be imported and initialized."""
    print("=== Testing Groq Orchestrator ===")
    
    try:
        from ai_agents.groq_orchestrator import groq_orchestrator
        print("✓ Groq orchestrator imported successfully")
        
        # Test health check
        health = groq_orchestrator.health_check()
        print(f"Orchestrator status: {health['orchestrator']['status']}")
        
        # Test capabilities
        capabilities = groq_orchestrator.get_capabilities()
        print(f"Available capabilities: {len(capabilities)} features")
        
        return True
        
    except Exception as e:
        print(f"✗ Groq orchestrator failed: {e}")
        return False

def test_chatbot_response():
    """Test if chatbot can generate a response."""
    print("=== Testing Chatbot Response ===")
    
    try:
        from ai_agents.groq_orchestrator import groq_orchestrator
        
        test_message = "Hello, can you help me?"
        context = {
            'user_id': 'test_user',
            'session_id': 'test_session',
            'page_context': 'test'
        }
        
        response = groq_orchestrator.generate_chatbot_response(test_message, context)
        
        if response and 'response' in response:
            print(f"✓ Chatbot response generated: {response['response'][:100]}...")
            print(f"Confidence: {response.get('confidence', 'N/A')}")
            return True
        else:
            print(f"✗ Invalid response format: {response}")
            return False
            
    except Exception as e:
        print(f"✗ Chatbot response failed: {e}")
        return False

def test_django_views():
    """Test if Django views can be imported."""
    print("=== Testing Django Views ===")
    
    try:
        from dashboard.views import chatbot_api, ai_status_api
        print("✓ Dashboard views imported successfully")
        return True
        
    except Exception as e:
        print(f"✗ Django views import failed: {e}")
        return False

def main():
    """Run all tests."""
    print("PublicBridge Chatbot API Test")
    print("=" * 40)
    
    tests = [
        test_environment_variables,
        test_django_views,
        test_groq_orchestrator,
        test_chatbot_response
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! Chatbot should be working.")
    else:
        print("✗ Some tests failed. Check the errors above.")
        
        # Provide troubleshooting tips
        print("\nTroubleshooting Tips:")
        print("1. Make sure .env file exists with GROQ_API_KEY")
        print("2. Install missing dependencies: pip install -r requirements_updated.txt")
        print("3. Check Django settings are loading environment variables")
        print("4. Verify Groq API key is valid")

if __name__ == "__main__":
    main()
