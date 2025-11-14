"""
AI Sentiment and Urgency Detection Agent

Advanced sentiment analysis and urgency detection for civic reports.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from datetime import datetime

from .base import BaseAIAgent, UrgencyLevel, AIAnalysisResult

logger = logging.getLogger(__name__)

class SentimentAnalyzerAgent(BaseAIAgent):
    """
    Advanced sentiment and urgency analysis agent for civic reports.
    
    Features:
    - Multi-dimensional sentiment analysis (positive/negative/neutral)
    - Urgency level detection (LOW/MEDIUM/HIGH/CRITICAL)
    - Emotional intensity scoring
    - Time-sensitive urgency detection
    - Citizen frustration assessment
    """
    
    def __init__(self, version: str = "2.0.0"):
        super().__init__("SentimentAnalyzer", version)
        self.confidence_threshold = 0.8
        self._initialize_sentiment_lexicons()
        self._initialize_urgency_indicators()
        
    def _initialize_sentiment_lexicons(self):
        """Initialize sentiment lexicons for civic domain."""
        self.sentiment_lexicons = {
            'positive': {
                'words': [
                    'good', 'excellent', 'great', 'wonderful', 'amazing',
                    'helpful', 'efficient', 'professional', 'courteous',
                    'responsive', 'effective', 'satisfactory', 'pleased',
                    'grateful', 'appreciate', 'thank', 'impressed'
                ],
                'weight': 1.0
            },
            'negative': {
                'words': [
                    'bad', 'terrible', 'awful', 'horrible', 'disgusting',
                    'frustrated', 'angry', 'disappointed', 'unsatisfied',
                    'useless', 'pathetic', 'ridiculous', 'unacceptable',
                    'broken', 'failed', 'problem', 'issue', 'concern',
                    'complain', 'criticize', 'blame', 'fault'
                ],
                'weight': 1.2
            },
            'urgent_negative': {
                'words': [
                    'urgent', 'emergency', 'critical', 'immediate',
                    'life-threatening', 'dangerous', 'unsafe', 'hazardous',
                    'disaster', 'crisis', 'panic', 'desperate',
                    'severe', 'serious', 'alarming', 'worried'
                ],
                'weight': 1.5
            }
        }
        
        # Civic-specific sentiment modifiers
        self.civic_modifiers = {
            'service_quality': {
                'positive': ['efficient', 'responsive', 'helpful', 'professional'],
                'negative': ['slow', 'unresponsive', 'unhelpful', 'rude']
            },
            'government_response': {
                'positive': ['addressed', 'resolved', 'fixed', 'improved'],
                'negative': ['ignored', 'neglected', 'overlooked', 'dismissed']
            }
        }
    
    def _initialize_urgency_indicators(self):
        """Initialize urgency detection indicators."""
        self.urgency_indicators = {
            UrgencyLevel.CRITICAL: {
                'keywords': [
                    'emergency', 'life-threatening', 'critical', 'urgent',
                    'immediate', 'dangerous', 'unsafe', 'hazardous',
                    'disaster', 'crisis', 'accident', 'injury',
                    'fire', 'flood', 'earthquake', 'medical emergency'
                ],
                'patterns': [
                    r'\b(emergency|life-threatening|critical)\b',
                    r'\b(accident|injury|fire|flood)\b',
                    r'\b(need\s+(immediate|urgent)\s+(help|assistance))\b'
                ],
                'intensity_multiplier': 2.0,
                'time_sensitivity': True
            },
            UrgencyLevel.HIGH: {
                'keywords': [
                    'urgent', 'important', 'serious', 'severe',
                    'significant', 'major', 'alarming', 'concerning',
                    'broken', 'failed', 'outage', 'disruption'
                ],
                'patterns': [
                    r'\b(urgent|serious|severe|major)\b',
                    r'\b(broken|failed|outage|disruption)\b',
                    r'\b(need\s+(quick|fast)\s+(response|action))\b'
                ],
                'intensity_multiplier': 1.5,
                'time_sensitivity': True
            },
            UrgencyLevel.MEDIUM: {
                'keywords': [
                    'issue', 'problem', 'concern', 'inconvenience',
                    'delay', 'slow', 'inefficient', 'suboptimal',
                    'improvement', 'better', 'enhance'
                ],
                'patterns': [
                    r'\b(issue|problem|concern)\b',
                    r'\b(delay|slow|inefficient)\b',
                    r'\b(would\s+like\s+(improvement|better))\b'
                ],
                'intensity_multiplier': 1.0,
                'time_sensitivity': False
            },
            UrgencyLevel.LOW: {
                'keywords': [
                    'suggestion', 'feedback', 'comment', 'observation',
                    'minor', 'small', 'little', 'slight',
                    'consider', 'maybe', 'possibly', 'future'
                ],
                'patterns': [
                    r'\b(suggestion|feedback|comment)\b',
                    r'\b(minor|small|little|slight)\b',
                    r'\b(consider|maybe|possibly)\b'
                ],
                'intensity_multiplier': 0.5,
                'time_sensitivity': False
            }
        }
        
        # Time-based urgency boosters
        self.time_urgency_boosters = {
            'time_sensitive_phrases': [
                'as soon as possible', 'immediately', 'right now',
                'today', 'this week', 'urgently needed'
            ],
            'escalation_indicators': [
                'multiple times', 'repeatedly', 'still not', 'ongoing',
                'continues to', 'keeps happening', 'persists'
            ]
        }
    
    async def _analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment and urgency of civic reports."""
        text = input_data.get('text', '')
        context = input_data.get('context', {})
        
        if not text:
            return {
                'confidence': 0.0,
                'predictions': {
                    'sentiment': 'neutral',
                    'urgency': UrgencyLevel.LOW.value,
                    'emotional_intensity': 0.0
                },
                'metadata': {'error': 'No text provided'}
            }
        
        # Perform sentiment analysis
        sentiment_analysis = self._analyze_sentiment(text, context)
        
        # Perform urgency detection
        urgency_analysis = self._analyze_urgency(text, context)
        
        # Calculate emotional intensity
        emotional_intensity = self._calculate_emotional_intensity(text, sentiment_analysis)
        
        # Generate comprehensive predictions
        predictions = {
            'sentiment': sentiment_analysis['primary_sentiment'],
            'sentiment_score': sentiment_analysis['sentiment_score'],
            'urgency': urgency_analysis['urgency_level'].value,
            'urgency_score': urgency_analysis['urgency_score'],
            'emotional_intensity': emotional_intensity,
            'citizen_frustration': sentiment_analysis['frustration_level'],
            'time_sensitivity': urgency_analysis['time_sensitive'],
            'escalation_risk': self._calculate_escalation_risk(sentiment_analysis, urgency_analysis)
        }
        
        # Calculate overall confidence
        confidence = min(sentiment_analysis['confidence'], urgency_analysis['confidence'])
        
        return {
            'confidence': confidence,
            'predictions': predictions,
            'metadata': {
                'text_length': len(text),
                'sentiment_keywords': sentiment_analysis['keyword_count'],
                'urgency_keywords': urgency_analysis['keyword_count'],
                'emotional_triggers': sentiment_analysis['emotional_triggers'],
                'time_indicators': urgency_analysis['time_indicators']
            }
        }