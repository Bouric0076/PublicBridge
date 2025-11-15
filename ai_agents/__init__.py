# PublicBridge AI Agents Package
"""
Agentic AI system for PublicBridge civic engagement platform.

This package contains intelligent agents that enhance citizen-government interaction
through advanced AI capabilities including natural language processing, predictive
analytics, and automated decision making.
"""

__version__ = "1.0.0"
__author__ = "PublicBridge AI Team - Lead Bouric Enos"

from .orchestrator import MultiAgentOrchestrator
from .conversation import ContextManager
from .nlp import EnhancedNLPEngine

__all__ = [
    'MultiAgentOrchestrator',
    'ContextManager',
    'EnhancedNLPEngine'
]