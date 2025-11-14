#!/usr/bin/env python
"""
Debug script to understand the emotion pipeline format.
"""
import os
import sys
import django
import logging

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_emotion_pipeline():
    """Debug the emotion pipeline format."""
    print("🔍 Debugging Emotion Pipeline Format...")
    
    try:
        from transformers import pipeline
        from ai_agents.device_manager import device_manager
        
        # Get device configuration
        model_config = device_manager.get_model_config()
        
        # Initialize emotion pipeline directly
        emotion_model_name = "j-hartmann/emotion-english-distilroberta-base"
        
        print(f"📦 Initializing emotion pipeline with model: {emotion_model_name}")
        
        emotion_pipeline = pipeline(
            "text-classification",
            model=emotion_model_name,
            tokenizer=emotion_model_name,
            device_map=model_config.get('device_map'),
            max_length=512,
            truncation=True,
            top_k=None  # Return all emotions with scores
        )
        
        # Test with a simple text
        test_text = "I am very happy today!"
        print(f"\n🧪 Testing with text: '{test_text}'")
        
        results = emotion_pipeline(test_text)
        
        print(f"\n📊 Raw Results:")
        print(f"Type: {type(results)}")
        print(f"Content: {results}")
        
        if isinstance(results, list):
            print(f"\nList length: {len(results)}")
            for i, item in enumerate(results):
                print(f"Item {i}: Type={type(item)}, Content={item}")
                if isinstance(item, dict):
                    for key, value in item.items():
                        print(f"  {key}: {value} (type: {type(value)})")
        
        # Test with different top_k values
        print(f"\n🔄 Testing with top_k=5:")
        emotion_pipeline_top5 = pipeline(
            "text-classification",
            model=emotion_model_name,
            tokenizer=emotion_model_name,
            device_map=model_config.get('device_map'),
            max_length=512,
            truncation=True,
            top_k=5
        )
        
        results_top5 = emotion_pipeline_top5(test_text)
        print(f"Top-5 Results: {results_top5}")
        
        print(f"\n🔄 Testing with top_k=1:")
        emotion_pipeline_top1 = pipeline(
            "text-classification",
            model=emotion_model_name,
            tokenizer=emotion_model_name,
            device_map=model_config.get('device_map'),
            max_length=512,
            truncation=True,
            top_k=1
        )
        
        results_top1 = emotion_pipeline_top1(test_text)
        print(f"Top-1 Results: {results_top1}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_emotion_pipeline()
    sys.exit(0 if success else 1)
