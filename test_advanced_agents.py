#!/usr/bin/env python
"""Test script to debug advanced agent initialization."""

import logging
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PublicBridge.settings')
django.setup()

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print('Testing advanced agent initialization...')
try:
    from ai_agents.orchestrator import MultiAgentOrchestrator
    
    print('Creating orchestrator with advanced agents...')
    orchestrator = MultiAgentOrchestrator(use_advanced_agents=True)
    
    print('Getting agent capabilities...')
    capabilities = orchestrator.get_agent_capabilities()
    for agent in capabilities:
        print(f'Agent: {agent["name"]}')
        print(f'  Available: {agent["available"]}')
        print(f'  Capabilities: {agent["capabilities"]}')
    
    print('SUCCESS: Advanced agents initialized')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()