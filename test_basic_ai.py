#!/usr/bin/env python
"""
Basic test script for AI agents without requiring large model downloads.
This tests the fallback mechanisms and basic functionality.
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

def test_fallback_agents():
    """Test fallback agent creation."""
    print("Testing fallback agent creation...")
    try:
        from ai_agents.llama_classifier import LlamaClassifierAgent
        from ai_agents.advanced_sentiment import AdvancedSentimentAnalyzer
        from ai_agents.civic_chatbot import CivicChatbotAgent
        
        # Test creation with fallback mode (no model loading)
        classifier = LlamaClassifierAgent()
        sentiment = AdvancedSentimentAnalyzer()
        chatbot = CivicChatbotAgent()
        
        print("✓ Fallback agent creation successful")
        print(f"  - LlamaClassifierAgent: {'Available' if classifier.model else 'Fallback mode'}")
        print(f"  - AdvancedSentimentAnalyzer: {'Available' if sentiment.model else 'Fallback mode'}")
        print(f"  - CivicChatbotAgent: {'Available' if chatbot.model else 'Fallback mode'}")
        
        return True
    except Exception as e:
        print(f"✗ Agent creation error: {e}")
        return False

def test_basic_orchestrator():
    """Test orchestrator with fallback agents."""
    print("Testing orchestrator with fallbacks...")
    try:
        from ai_agents.orchestrator import MultiAgentOrchestrator
        
        orchestrator = MultiAgentOrchestrator()
        capabilities = orchestrator.get_agent_capabilities()
        
        print(f"✓ Orchestrator created successfully")
        print(f"  Available agents: {len(capabilities)}")
        for agent in capabilities:
            print(f"  - {agent['name']}: {'Available' if agent['available'] else 'Fallback mode'}")
        
        return True
    except Exception as e:
        print(f"✗ Orchestrator error: {e}")
        return False

def test_report_analysis_fallback():
    """Test report analysis with fallback mechanisms."""
    print("Testing report analysis with fallbacks...")
    try:
        from ai_agents.orchestrator import MultiAgentOrchestrator
        from reports.models import Report
        
        # Create a sample report if none exists
        if not Report.objects.exists():
            print("  Creating sample report...")
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Create a test user if none exists
            if not User.objects.filter(role='citizen').exists():
                user = User.objects.create_user(
                    username='test_citizen',
                    email='test@example.com',
                    password='testpass123',
                    role='citizen',
                    ai_user_profile={}  # Initialize empty AI profile
                )
            else:
                user = User.objects.filter(role='citizen').first()
            
            report = Report.objects.create(
                title="Pothole on Main Street",
                description="Large pothole causing traffic delays and vehicle damage. Needs immediate attention.",
                category="service",  # Using the available choices
                priority="high",
                user=user,
                user_contact="+1234567890",
                urgency=4  # 1-5 scale
            )
        else:
            report = Report.objects.first()
        
        orchestrator = MultiAgentOrchestrator()
        
        # Convert report to dictionary format expected by analyze_report
        report_data = {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'category': report.category,
            'priority': report.priority,
            'urgency': report.urgency,
            'created_at': report.created_at.isoformat(),
            'user_id': report.user.id,
            'text': report.description  # Add text field for NLP processing
        }
        
        result = orchestrator.analyze_report_sync(report_data)
        
        print(f"✓ Report analysis completed (with fallbacks)")
        print(f"  Confidence: {result.confidence_score}")
        print(f"  Category: {result.category}")
        print(f"  Sentiment: {result.sentiment}")
        print(f"  Urgency: {result.urgency}")
        
        return True
    except Exception as e:
        print(f"✗ Report analysis error: {e}")
        return False

def test_basic_chatbot():
    """Test basic chatbot functionality with fallbacks."""
    print("Testing basic chatbot with fallbacks...")
    try:
        from ai_agents.civic_chatbot import CivicChatbotAgent
        
        chatbot = CivicChatbotAgent()
        
        # Test basic response generation
        response = chatbot.generate_response("How do I report a pothole?")
        
        print(f"✓ Basic chatbot response received")
        print(f"  Response: {response['response'][:100]}...")
        print(f"  Confidence: {response['confidence']}")
        
        return True
    except Exception as e:
        print(f"✗ Chatbot error: {e}")
        return False

def main():
    """Run all basic tests."""
    print("=" * 60)
    print("BASIC AI AGENTS INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Fallback Agents", test_fallback_agents),
        ("Basic Orchestrator", test_basic_orchestrator),
        ("Report Analysis Fallback", test_report_analysis_fallback),
        ("Basic Chatbot", test_basic_chatbot),
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
        print("🎉 All basic tests passed! AI integration is working correctly.")
        print("Note: Full Llama model features require model downloads and authentication.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("The system should still work with fallback mechanisms.")

if __name__ == "__main__":
    main()