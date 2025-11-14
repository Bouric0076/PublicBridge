#!/usr/bin/env python
"""
Test script to verify the emotion analysis fix.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

from ai_agents.advanced_sentiment import AdvancedSentimentAnalyzer
import logging

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_emotion_analysis():
    """Test the emotion analysis functionality."""
    print("🧪 Testing Emotion Analysis Fix...")
    
    try:
        # Initialize the analyzer
        analyzer = AdvancedSentimentAnalyzer()
        
        # Test texts with different emotions
        test_texts = [
            "I am very happy with the service!",
            "This is extremely frustrating and annoying.",
            "I'm worried about the safety issues.",
            "The response was disappointing and sad.",
            "I'm angry about this situation!"
        ]
        
        print("\n📊 Testing emotion analysis on sample texts:")
        print("-" * 60)
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n{i}. Text: '{text}'")
            
            try:
                # Test the emotion analysis
                result = analyzer._analyze_emotions(text)
                
                print(f"   ✅ Success!")
                print(f"   Dominant emotion: {result.get('dominant_emotion', 'unknown')}")
                print(f"   Score: {result.get('dominant_score', 0):.2f}")
                print(f"   Method: {result.get('method', 'unknown')}")
                
                # Show top emotions
                emotions = result.get('emotions', {})
                if emotions:
                    top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                    print(f"   Top emotions: {', '.join([f'{emotion}: {score:.2f}' for emotion, score in top_emotions])}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n🎯 Testing complete sentiment analysis:")
        print("-" * 60)
        
        # Test full sentiment analysis
        test_text = "I'm really frustrated with the slow response to my urgent report about the broken streetlight."
        
        try:
            result = analyzer.analyze_sentiment(test_text)
            print(f"✅ Full analysis successful!")
            print(f"Sentiment: {result['sentiment']['label']} ({result['sentiment']['confidence']:.2f})")
            print(f"Dominant emotion: {result['emotions']['dominant_emotion']} ({result['emotions']['dominant_score']:.2f})")
            print(f"Urgency: {result['urgency']['urgency_level']} ({result['urgency']['urgency_score']:.2f})")
            
        except Exception as e:
            print(f"❌ Full analysis error: {e}")
        
        print("\n✅ Emotion analysis test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_emotion_analysis()
    sys.exit(0 if success else 1)
