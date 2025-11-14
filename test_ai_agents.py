#!/usr/bin/env python
"""
Test script for AI agents integration.
This script tests the Llama-based AI agents without requiring Django setup.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

def test_basic_imports():
    """Test basic imports work."""
    print("Testing basic imports...")
    try:
        from ai_agents.base import BaseAIAgent, AIAnalysisResult
        from ai_agents.orchestrator import MultiAgentOrchestrator
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_agent_creation():
    """Test agent creation without model loading."""
    print("Testing agent creation...")
    try:
        from ai_agents.llama_classifier import LlamaClassifierAgent
        from ai_agents.advanced_sentiment import AdvancedSentimentAnalyzer
        from ai_agents.civic_chatbot import CivicChatbotAgent
        
        # Test creation with fallback mode (no model loading)
        classifier = LlamaClassifierAgent()
        sentiment = AdvancedSentimentAnalyzer()
        chatbot = CivicChatbotAgent()
        
        print("✓ Agent creation successful (fallback mode)")
        return True
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False

def test_orchestrator():
    """Test orchestrator functionality."""
    print("Testing orchestrator...")
    try:
        from ai_agents.orchestrator import MultiAgentOrchestrator
        
        orchestrator = MultiAgentOrchestrator()
        capabilities = orchestrator.get_agent_capabilities()
        
        print(f"✓ Orchestrator created successfully")
        print(f"  Available agents: {len(capabilities)}")
        for agent in capabilities:
            print(f"  - {agent['name']}: {'Available' if agent['available'] else 'Not available'}")
        
        return True
    except Exception as e:
        print(f"✗ Orchestrator error: {e}")
        return False

def test_report_analysis():
    """Test report analysis with sample data."""
    print("Testing report analysis...")
    try:
        from ai_agents.orchestrator import MultiAgentOrchestrator
        from reports.models import Report
        
        # Create a sample report if none exists
        if not Report.objects.exists():
            print("  Creating sample report...")
            report = Report.objects.create(
                title="Pothole on Main Street",
                description="Large pothole causing traffic delays and vehicle damage. Needs immediate attention.",
                category="infrastructure",
                priority="high",
                location="Main Street and Oak Avenue"
            )
        else:
            report = Report.objects.first()
        
        orchestrator = MultiAgentOrchestrator()
        
        # Convert Report object to dictionary format expected by analyze_report
        report_data = {
            'id': report.id,
            'title': report.title,
            'text': report.description,  # This is the field the AI agents expect
            'description': report.description,
            'category': report.category,
            'priority': report.priority,
            'urgency': getattr(report, 'urgency', 3),  # Default urgency if not available
            'location': getattr(report, 'location', 'Unknown'),
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'user_id': report.user.id if report.user else None,
        }
        
        result = orchestrator.analyze_report_sync(report_data)
        
        print(f"✓ Report analysis completed")
        print(f"  Confidence: {result.confidence_score}")
        print(f"  Category: {result.category}")
        print(f"  Sentiment: {result.sentiment}")
        print(f"  Urgency: {result.urgency}")
        
        return True
    except Exception as e:
        print(f"✗ Report analysis error: {e}")
        return False

def test_chatbot():
    """Test chatbot functionality."""
    print("Testing chatbot...")
    try:
        from ai_agents.orchestrator import MultiAgentOrchestrator
        import asyncio
        
        orchestrator = MultiAgentOrchestrator()
        
        # Test basic chatbot interaction (async)
        async def test_chat():
            return await orchestrator.process_chatbot_message(
                "How do I report a pothole?",
                {"user_id": 1, "session_id": "test_session"}
            )
        
        response = asyncio.run(test_chat())
        
        print(f"✓ Chatbot response received")
        print(f"  Response: {response['response'][:100]}...")
        print(f"  Confidence: {response['confidence']}")
        
        return True
    except Exception as e:
        print(f"✗ Chatbot error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("AI AGENTS INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Agent Creation", test_agent_creation),
        ("Orchestrator", test_orchestrator),
        ("Report Analysis", test_report_analysis),
        ("Chatbot", test_chatbot),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
            else:
                print(f"  Test failed")
        except Exception as e:
            print(f"  Test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! AI integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("This might be due to missing models or dependencies.")

if __name__ == "__main__":
    main()