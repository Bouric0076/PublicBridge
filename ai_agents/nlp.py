from typing import Dict, List, Optional, Tuple, Any
import re
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class EnhancedNLPEngine:
    """
    Enhanced NLP Engine with advanced intent detection, entity extraction, and context awareness.
    
    Features:
    - Multi-level intent classification with confidence scoring
    - Comprehensive entity extraction (locations, departments, urgency indicators)
    - Language detection (English/Kiswahili)
    - Context-aware intent resolution
    - Sentiment and emotion indicators
    - Urgency level detection
    """
    
    def __init__(self):
        """Initialize the enhanced NLP engine with comprehensive patterns."""
        
        # Enhanced intent patterns with multilingual support
        self.intent_patterns = {
            'greeting': {
                'en': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings'],
                'sw': ['habari', 'salamu', 'hujambo', 'mambo', 'shikamoo', 'hodi'],
                'weight': 1.0
            },
            'report_help': {
                'en': ['report', 'submit', 'file', 'complaint', 'issue', 'problem', 'incident', 'concern'],
                'sw': ['ripoti', 'wasilisha', 'malalamiko', 'tatizo', 'shida', 'tukio', 'wasiwasi'],
                'weight': 1.2
            },
            'status_inquiry': {
                'en': ['status', 'track', 'check', 'update', 'progress', 'reference', 'follow up', 'inquiry'],
                'sw': ['hali', 'fuatilia', 'angalia', 'sasisho', 'maendeleo', 'rujuko', 'ulizo'],
                'weight': 1.1
            },
            'civic_info': {
                'en': ['information', 'help', 'service', 'contact', 'office', 'department', 'government', 'ministry'],
                'sw': ['habari', 'msaada', 'huduma', 'mawasiliano', 'ofisi', 'idara', 'serikali', 'wizara'],
                'weight': 1.0
            },
            'emergency': {
                'en': ['emergency', 'urgent', 'critical', 'immediate', 'crisis', 'disaster', 'danger'],
                'sw': ['dharura', 'haraka', 'muhimu', 'mara moja', 'janga', 'hatari'],
                'weight': 2.0
            },
            'complaint': {
                'en': ['complain', 'dissatisfied', 'poor service', 'bad', 'terrible', 'awful', 'unacceptable'],
                'sw': ['lalamika', 'kutoridhika', 'huduma mbaya', 'mbaya', 'haiwezekani'],
                'weight': 1.3
            },
            'appreciation': {
                'en': ['thank', 'thanks', 'appreciate', 'grateful', 'excellent', 'good job', 'well done'],
                'sw': ['asante', 'shukrani', 'nashukuru', 'vizuri', 'kazi nzuri', 'hongera'],
                'weight': 1.0
            },
            'goodbye': {
                'en': ['bye', 'goodbye', 'see you', 'farewell', 'take care'],
                'sw': ['kwaheri', 'tutaonana', 'heri za kuonana', 'jisahau'],
                'weight': 1.0
            }
        }
        
        # Entity patterns
        self.entity_patterns = {
            'counties': [
                'nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'malindi', 'garissa',
                'kakamega', 'kitale', 'machakos', 'meru', 'nyeri', 'embu', 'kericho', 'bomet',
                'narok', 'kajiado', 'kiambu', 'murang\'a', 'kirinyaga', 'nyandarua', 'laikipia',
                'samburu', 'isiolo', 'marsabit', 'mandera', 'wajir', 'turkana', 'west pokot',
                'baringo', 'elgeyo marakwet', 'uasin gishu', 'trans nzoia', 'bungoma', 'busia',
                'siaya', 'kisii', 'nyamira', 'migori', 'homa bay', 'rachuonyo', 'tana river',
                'lamu', 'taita taveta', 'kwale', 'kilifi'
            ],
            'departments': [
                'health', 'education', 'infrastructure', 'water', 'roads', 'environment',
                'agriculture', 'transport', 'security', 'planning', 'finance', 'administration',
                'afya', 'elimu', 'miundombinu', 'maji', 'barabara', 'mazingira', 'kilimo',
                'usalama', 'mipango', 'fedha', 'utawala'
            ],
            'urgency_indicators': [
                'urgent', 'emergency', 'immediate', 'asap', 'critical', 'severe', 'serious',
                'haraka', 'dharura', 'mara moja', 'muhimu', 'mkuu', 'mbaya'
            ],
            'report_categories': [
                'infrastructure', 'healthcare', 'education', 'environment', 'corruption',
                'public safety', 'transportation', 'utilities', 'government services',
                'miundombinu', 'afya', 'elimu', 'mazingira', 'rushwa', 'usalama',
                'usafiri', 'huduma za umma'
            ]
        }
        
        # Language detection patterns
        self.language_indicators = {
            'sw': ['habari', 'asante', 'sawa', 'ndiyo', 'hapana', 'tafadhali', 'pole', 'karibu', 
                   'hujambo', 'mambo', 'poa', 'safi', 'vizuri', 'mbaya', 'haraka', 'pole'],
            'en': ['the', 'and', 'or', 'but', 'with', 'from', 'please', 'thank', 'hello', 
                   'good', 'bad', 'help', 'service', 'government', 'report']
        }
        
        # Sentiment indicators
        self.sentiment_patterns = {
            'positive': {
                'en': ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'satisfied', 'happy'],
                'sw': ['vizuri', 'nzuri', 'bora', 'ajabu', 'furaha', 'ridhaa']
            },
            'negative': {
                'en': ['bad', 'terrible', 'awful', 'horrible', 'disappointed', 'frustrated', 'angry', 'upset'],
                'sw': ['mbaya', 'vibaya', 'hasira', 'uchungu', 'kutoridhika']
            },
            'neutral': {
                'en': ['okay', 'fine', 'normal', 'average', 'standard'],
                'sw': ['sawa', 'kawaida', 'wastani']
            }
        }

    def detect_intent(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced intent detection with context awareness and confidence scoring.
        
        Args:
            text: Input text to analyze
            context: Optional context for better intent resolution
            
        Returns:
            Comprehensive intent analysis with confidence scores
        """
        if not text or not text.strip():
            return self._empty_intent_result()
        
        text_lower = text.lower().strip()
        
        # Detect language
        detected_language = self._detect_language(text_lower)
        
        # Calculate intent scores
        intent_scores = self._calculate_intent_scores(text_lower, detected_language)
        
        # Apply context-aware adjustments
        if context:
            intent_scores = self._apply_context_adjustments(intent_scores, context)
        
        # Determine primary and secondary intents
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else 'general'
        secondary_intents = [intent for intent, score in intent_scores.items() 
                           if score > 0.2 and intent != primary_intent]
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent_scores, primary_intent)
        
        # Extract additional metadata
        metadata = self._extract_intent_metadata(text_lower, detected_language, context)
        
        return {
            'primary_intent': primary_intent,
            'secondary_intents': secondary_intents[:3],  # Top 3 secondary intents
            'confidence': confidence,
            'detected_language': detected_language,
            'intent_scores': intent_scores,
            'metadata': metadata,
            'requires_escalation': self._requires_escalation(primary_intent, intent_scores, metadata),
            'urgency_level': self._determine_urgency_level(text_lower, intent_scores, metadata)
        }

    def extract_entities(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced entity extraction with comprehensive coverage.
        
        Args:
            text: Input text to analyze
            context: Optional context for better entity resolution
            
        Returns:
            Extracted entities with confidence scores
        """
        if not text or not text.strip():
            return {}
        
        text_lower = text.lower().strip()
        entities = {}
        
        # Extract location entities
        locations = self._extract_locations(text_lower)
        if locations:
            entities['locations'] = locations
        
        # Extract department entities
        departments = self._extract_departments(text_lower)
        if departments:
            entities['departments'] = departments
        
        # Extract urgency indicators
        urgency_indicators = self._extract_urgency_indicators(text_lower)
        if urgency_indicators:
            entities['urgency_indicators'] = urgency_indicators
        
        # Extract report categories
        categories = self._extract_report_categories(text_lower)
        if categories:
            entities['report_categories'] = categories
        
        # Extract temporal expressions
        temporal = self._extract_temporal_expressions(text_lower)
        if temporal:
            entities['temporal'] = temporal
        
        # Extract contact information
        contacts = self._extract_contact_info(text)
        if contacts:
            entities['contacts'] = contacts
        
        return entities

    def analyze_sentiment_and_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment and emotional indicators in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Sentiment and emotion analysis results
        """
        if not text or not text.strip():
            return {'sentiment': 'neutral', 'emotion': 'neutral', 'intensity': 0.0}
        
        text_lower = text.lower().strip()
        detected_language = self._detect_language(text_lower)
        
        # Calculate sentiment scores
        sentiment_scores = {}
        for sentiment, patterns in self.sentiment_patterns.items():
            lang_patterns = patterns.get(detected_language, []) + patterns.get('en', [])
            score = sum(1 for pattern in lang_patterns if pattern in text_lower)
            sentiment_scores[sentiment] = score
        
        # Determine primary sentiment
        primary_sentiment = max(sentiment_scores, key=sentiment_scores.get) if any(sentiment_scores.values()) else 'neutral'
        
        # Calculate intensity
        total_indicators = sum(sentiment_scores.values())
        intensity = min(total_indicators / 3.0, 1.0)  # Normalize to 0-1
        
        # Detect specific emotions
        emotion = self._detect_emotion(text_lower, detected_language)
        
        return {
            'sentiment': primary_sentiment,
            'emotion': emotion,
            'intensity': intensity,
            'sentiment_scores': sentiment_scores,
            'detected_language': detected_language
        }

    def _detect_language(self, text: str) -> str:
        """Detect the primary language of the text."""
        sw_score = sum(1 for word in self.language_indicators['sw'] if word in text)
        en_score = sum(1 for word in self.language_indicators['en'] if word in text)
        
        return 'sw' if sw_score > en_score else 'en'

    def _calculate_intent_scores(self, text: str, language: str) -> Dict[str, float]:
        """Calculate weighted intent scores."""
        scores = {}
        
        for intent, pattern_data in self.intent_patterns.items():
            # Get patterns for detected language and fallback to English
            patterns = pattern_data.get(language, []) + pattern_data.get('en', [])
            weight = pattern_data.get('weight', 1.0)
            
            # Calculate raw score
            raw_score = sum(1 for pattern in patterns if pattern in text)
            
            # Apply weight and normalize
            if raw_score > 0:
                scores[intent] = (raw_score / len(patterns)) * weight
        
        return scores

    def _apply_context_adjustments(self, intent_scores: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
        """Apply context-aware adjustments to intent scores."""
        adjusted_scores = intent_scores.copy()
        
        # Boost certain intents based on context
        if context.get('page_context') == 'reports':
            adjusted_scores['report_help'] = adjusted_scores.get('report_help', 0) * 1.3
        
        if context.get('user_has_active_reports'):
            adjusted_scores['status_inquiry'] = adjusted_scores.get('status_inquiry', 0) * 1.2
        
        if context.get('session_goal') == 'submit_report':
            adjusted_scores['report_help'] = adjusted_scores.get('report_help', 0) * 1.5
        
        return adjusted_scores

    def _calculate_confidence(self, intent_scores: Dict[str, float], primary_intent: str) -> float:
        """Calculate confidence score for the primary intent."""
        if not intent_scores or primary_intent not in intent_scores:
            return 0.0
        
        primary_score = intent_scores[primary_intent]
        total_score = sum(intent_scores.values())
        
        if total_score == 0:
            return 0.0
        
        # Confidence is the ratio of primary score to total, with minimum threshold
        confidence = primary_score / total_score
        return max(confidence, 0.1) if primary_score > 0 else 0.0

    def _extract_intent_metadata(self, text: str, language: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract additional metadata about the intent."""
        metadata = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'contains_question': '?' in text,
            'contains_exclamation': '!' in text,
            'is_polite': any(word in text for word in ['please', 'kindly', 'tafadhali']),
            'is_urgent': any(word in text for word in ['urgent', 'emergency', 'asap', 'haraka', 'dharura']),
            'detected_language': language
        }
        
        if context:
            metadata['context_provided'] = True
            metadata['session_context'] = context.get('session_context', {})
        
        return metadata

    def _requires_escalation(self, primary_intent: str, intent_scores: Dict[str, float], metadata: Dict[str, Any]) -> bool:
        """Determine if the intent requires escalation."""
        escalation_intents = ['emergency', 'complaint']
        
        if primary_intent in escalation_intents:
            return True
        
        if metadata.get('is_urgent') and intent_scores.get('report_help', 0) > 0.5:
            return True
        
        return False

    def _determine_urgency_level(self, text: str, intent_scores: Dict[str, float], metadata: Dict[str, Any]) -> str:
        """Determine the urgency level of the request."""
        if intent_scores.get('emergency', 0) > 0.3 or metadata.get('is_urgent'):
            return 'high'
        elif intent_scores.get('complaint', 0) > 0.5:
            return 'medium'
        elif intent_scores.get('status_inquiry', 0) > 0.5:
            return 'medium'
        else:
            return 'low'

    def _extract_locations(self, text: str) -> List[Dict[str, Any]]:
        """Extract location entities."""
        locations = []
        for county in self.entity_patterns['counties']:
            if county in text:
                locations.append({
                    'name': county,
                    'type': 'county',
                    'confidence': 0.9
                })
        return locations

    def _extract_departments(self, text: str) -> List[Dict[str, Any]]:
        """Extract department entities."""
        departments = []
        for dept in self.entity_patterns['departments']:
            if dept in text:
                departments.append({
                    'name': dept,
                    'type': 'department',
                    'confidence': 0.8
                })
        return departments

    def _extract_urgency_indicators(self, text: str) -> List[str]:
        """Extract urgency indicators."""
        return [indicator for indicator in self.entity_patterns['urgency_indicators'] if indicator in text]

    def _extract_report_categories(self, text: str) -> List[str]:
        """Extract report category indicators."""
        return [category for category in self.entity_patterns['report_categories'] if category in text]

    def _extract_temporal_expressions(self, text: str) -> List[Dict[str, Any]]:
        """Extract temporal expressions."""
        temporal_patterns = [
            r'\b(today|tomorrow|yesterday|now|immediately)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{1,2}:\d{2})\b'
        ]
        
        temporal_expressions = []
        for pattern in temporal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_expressions.append({
                    'text': match.group(),
                    'type': 'temporal',
                    'position': match.span()
                })
        
        return temporal_expressions

    def _extract_contact_info(self, text: str) -> List[Dict[str, Any]]:
        """Extract contact information."""
        contact_patterns = [
            (r'\b(\d{10}|\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b', 'phone'),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email')
        ]
        
        contacts = []
        for pattern, contact_type in contact_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                contacts.append({
                    'value': match.group(),
                    'type': contact_type,
                    'confidence': 0.9
                })
        
        return contacts

    def _detect_emotion(self, text: str, language: str) -> str:
        """Detect specific emotions in text."""
        emotion_patterns = {
            'anger': ['angry', 'furious', 'mad', 'hasira', 'ghadhabu'],
            'frustration': ['frustrated', 'annoyed', 'irritated', 'uchungu'],
            'satisfaction': ['satisfied', 'pleased', 'content', 'ridhaa'],
            'concern': ['worried', 'concerned', 'anxious', 'wasiwasi'],
            'appreciation': ['grateful', 'thankful', 'appreciate', 'shukrani']
        }
        
        emotion_scores = {}
        for emotion, patterns in emotion_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                emotion_scores[emotion] = score
        
        return max(emotion_scores, key=emotion_scores.get) if emotion_scores else 'neutral'

    def _empty_intent_result(self) -> Dict[str, Any]:
        """Return empty intent result for invalid input."""
        return {
            'primary_intent': 'unclear',
            'secondary_intents': [],
            'confidence': 0.0,
            'detected_language': 'en',
            'intent_scores': {},
            'metadata': {},
            'requires_escalation': False,
            'urgency_level': 'low'
        }

# Maintain backward compatibility
class NLPEngine(EnhancedNLPEngine):
    """Backward compatible NLP Engine."""
    
    def detect_intent(self, text: str) -> Dict:
        """Backward compatible intent detection."""
        result = super().detect_intent(text)
        return {
            'primary_intent': result['primary_intent'],
            'secondary_intents': result['secondary_intents'],
            'confidence': result['confidence'],
            'all_scores': result['intent_scores']
        }

    def extract_entities(self, text: str) -> Dict:
        """Backward compatible entity extraction."""
        entities = super().extract_entities(text)
        
        # Convert to old format
        old_format = {}
        if 'locations' in entities:
            counties = [loc['name'] for loc in entities['locations'] if loc['type'] == 'county']
            if counties:
                old_format['counties'] = counties
        
        return old_format
