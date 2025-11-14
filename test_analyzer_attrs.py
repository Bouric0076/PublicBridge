#!/usr/bin/env python
"""Test script to check AdvancedSentimentAnalyzer model attributes."""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

print('Checking AdvancedSentimentAnalyzer model attribute...')
try:
    from ai_agents.advanced_sentiment import AdvancedSentimentAnalyzer
    
    analyzer = AdvancedSentimentAnalyzer()
    print(f'Has model attribute: {hasattr(analyzer, "model")}')
    if hasattr(analyzer, 'model'):
        print(f'Model value: {analyzer.model}')
        print(f'Model is None: {analyzer.model is None}')
    
    print(f'Has sentiment_model attribute: {hasattr(analyzer, "sentiment_model")}')
    if hasattr(analyzer, 'sentiment_model'):
        print(f'Sentiment model value: {analyzer.sentiment_model}')
    
    print(f'Has emotion_model attribute: {hasattr(analyzer, "emotion_model")}')
    if hasattr(analyzer, 'emotion_model'):
        print(f'Emotion model value: {analyzer.emotion_model}')
    
    print(f'Has urgency_model attribute: {hasattr(analyzer, "urgency_model")}')
    if hasattr(analyzer, 'urgency_model'):
        print(f'Urgency model value: {analyzer.urgency_model}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()