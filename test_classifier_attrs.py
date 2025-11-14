#!/usr/bin/env python
"""Test script to check ReportClassifierAgent model attributes."""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

print('Checking ReportClassifierAgent model attribute...')
try:
    from ai_agents.llama_classifier import LlamaClassifierAgent
    
    classifier = LlamaClassifierAgent()
    print(f'Has model attribute: {hasattr(classifier, "model")}')
    if hasattr(classifier, 'model'):
        print(f'Model value: {classifier.model}')
        print(f'Model is None: {classifier.model is None}')
    
    print(f'Has llama_model attribute: {hasattr(classifier, "llama_model")}')
    if hasattr(classifier, 'llama_model'):
        print(f'Llama model value: {classifier.llama_model}')
        
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()