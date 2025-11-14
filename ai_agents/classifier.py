"""
AI Report Classification Agent

Intelligent categorization of citizen reports using advanced NLP and ML techniques.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

from .base import BaseAIAgent, ReportCategory, AIAnalysisResult

logger = logging.getLogger(__name__)

class ReportClassifierAgent(BaseAIAgent):
    """
    Advanced AI agent for categorizing citizen reports.
    
    Uses multiple classification approaches:
    - Rule-based keyword matching
    - Pattern recognition
    - Contextual analysis
    - Confidence scoring
    """
    
    def __init__(self, version: str = "2.0.0"):
        super().__init__("ReportClassifier", version)
        self.confidence_threshold = 0.75
        self._initialize_category_patterns()
        
    def _initialize_category_patterns(self):
        """Initialize keyword patterns for each category."""
        self.category_patterns = {
            ReportCategory.INFRASTRUCTURE: {
                'keywords': [
                    'road', 'bridge', 'building', 'construction', 'pothole',
                    'sidewalk', 'street', 'highway', 'infrastructure',
                    'drainage', 'sewer', 'water pipe', 'electricity',
                    'maintenance', 'repair', 'damaged', 'broken'
                ],
                'patterns': [
                    r'\b(road|bridge|building)\s+(repair|maintenance|construction)\b',
                    r'\b(damaged|broken|pothole|crack)\s+(road|bridge|sidewalk)\b',
                    r'\binfrastructure\s+(issue|problem|concern)\b'
                ],
                'weight': 1.0
            },
            ReportCategory.HEALTHCARE: {
                'keywords': [
                    'hospital', 'clinic', 'doctor', 'nurse', 'medical',
                    'health', 'sick', 'disease', 'medicine', 'treatment',
                    'patient', 'emergency', 'ambulance', 'healthcare',
                    'covid', 'vaccine', 'pandemic', 'epidemic'
                ],
                'patterns': [
                    r'\b(hospital|clinic)\s+(issue|problem|concern)\b',
                    r'\b(medical|healthcare)\s+(service|treatment)\b',
                    r'\b(doctor|nurse|staff)\s+(shortage|unavailable)\b'
                ],
                'weight': 1.2
            },
            ReportCategory.PUBLIC_SAFETY: {
                'keywords': [
                    'police', 'crime', 'safety', 'security', 'accident',
                    'theft', 'robbery', 'violence', 'emergency', 'fire',
                    'danger', 'threat', 'attack', 'assault', 'murder'
                ],
                'patterns': [
                    r'\b(police|crime|safety)\s+(issue|concern|problem)\b',
                    r'\b(accident|emergency|fire)\s+(incident|situation)\b',
                    r'\b(dangerous|unsafe|threat)\s+(area|location|situation)\b'
                ],
                'weight': 1.5
            },
            ReportCategory.EDUCATION: {
                'keywords': [
                    'school', 'teacher', 'student', 'education', 'university',
                    'college', 'classroom', 'academic', 'learning', 'curriculum',
                    'tuition', 'fees', 'scholarship', 'textbook'
                ],
                'patterns': [
                    r'\b(school|university|college)\s+(issue|problem|concern)\b',
                    r'\b(teacher|student|education)\s+(shortage|quality)\b',
                    r'\b(classroom|facility)\s+(condition|maintenance)\b'
                ],
                'weight': 1.0
            },
            ReportCategory.ENVIRONMENT: {
                'keywords': [
                    'pollution', 'waste', 'garbage', 'environment', 'air',
                    'water', 'contamination', 'toxic', 'chemical', 'smoke',
                    'noise', 'deforestation', 'climate', 'green'
                ],
                'patterns': [
                    r'\b(air|water)\s+(pollution|contamination)\b',
                    r'\b(waste|garbage)\s+(disposal|management)\b',
                    r'\b(environmental|climate)\s+(issue|concern)\b'
                ],
                'weight': 1.1
            },
            ReportCategory.CORRUPTION: {
                'keywords': [
                    'corruption', 'bribe', 'bribery', 'fraud', 'embezzlement',
                    'kickback', 'extortion', 'misuse', 'abuse', 'illegal',
                    'unethical', 'transparency', 'accountability'
                ],
                'patterns': [
                    r'\b(corruption|bribe|fraud)\s+(allegation|report)\b',
                    r'\b(embezzlement|kickback|extortion)\s+(incident)\b',
                    r'\b(misuse|abuse)\s+(of\s+(power|funds|authority))\b'
                ],
                'weight': 1.3
            },
            ReportCategory.TRANSPORTATION: {
                'keywords': [
                    'bus', 'train', 'metro', 'subway', 'transportation',
                    'traffic', 'congestion', 'parking', 'vehicle', 'driver',
                    'route', 'schedule', 'delay', 'cancellation'
                ],
                'patterns': [
                    r'\b(bus|train|metro)\s+(delay|cancellation|issue)\b',
                    r'\b(traffic|congestion|parking)\s+(problem|issue)\b',
                    r'\b(transportation|public\s+transport)\s+(service)\b'
                ],
                'weight': 1.0
            },
            ReportCategory.UTILITIES: {
                'keywords': [
                    'electricity', 'power', 'water', 'gas', 'internet',
                    'utility', 'outage', 'disconnection', 'billing',
                    'service', 'supply', 'grid', 'network'
                ],
                'patterns': [
                    r'\b(electricity|power|water)\s+(outage|disconnection)\b',
                    r'\b(utility|service)\s+(issue|problem|billing)\b',
                    r'\b(internet|network)\s+(connection|speed|issue)\b'
                ],
                'weight': 1.0
            },
            ReportCategory.EMERGENCY: {
                'keywords': [
                    'emergency', 'urgent', 'immediate', 'critical',
                    'life-threatening', 'disaster', 'flood', 'earthquake',
                    'fire', 'medical emergency', 'accident', 'injury'
                ],
                'patterns': [
                    r'\b(emergency|urgent|immediate|critical)\b',
                    r'\b(life-threatening|disaster|flood|earthquake)\b',
                    r'\b(medical\s+emergency|fire|accident)\b'
                ],
                'weight': 2.0
            }
        }
    
    async def _analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze report text and determine category with confidence scoring."""
        text = input_data.get('text', '')
        context = input_data.get('context', {})
        
        if not text:
            return {
                'confidence': 0.0,
                'predictions': {'category': ReportCategory.GENERAL.value},
                'metadata': {'error': 'No text provided'}
            }
        
        # Run multiple classification approaches
        keyword_scores = self._keyword_classification(text)
        pattern_scores = self._pattern_classification(text)
        contextual_scores = await self._contextual_classification(text, context)
        
        # Combine scores with weighted ensemble
        combined_scores = self._combine_scores(
            keyword_scores, pattern_scores, contextual_scores
        )
        
        # Determine final category and confidence
        best_category = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[best_category]
        
        # Generate detailed predictions
        predictions = {
            'category': best_category.value,
            'category_scores': {cat.value: score for cat, score in combined_scores.items()},
            'primary_keywords': self._extract_primary_keywords(text, best_category),
            'classification_method': self._get_classification_method(confidence)
        }
        
        return {
            'confidence': confidence,
            'predictions': predictions,
            'metadata': {
                'input_length': len(text),
                'keyword_matches': len(self._get_all_keyword_matches(text)),
                'pattern_matches': len(self._get_all_pattern_matches(text))
            }
        }
    
    def _keyword_classification(self, text: str) -> Dict[ReportCategory, float]:
        """Keyword-based classification with TF-IDF-like scoring."""
        text_lower = text.lower()
        scores = {category: 0.0 for category in ReportCategory}
        
        for category, config in self.category_patterns.items():
            keyword_matches = 0
            total_keywords = len(config['keywords'])
            
            for keyword in config['keywords']:
                if keyword in text_lower:
                    keyword_matches += 1
                    # Weight by keyword position (earlier = more important)
                    position_weight = 1.0 / (text_lower.find(keyword) + 1)
                    scores[category] += position_weight
            
            # Normalize by total keywords and apply category weight
            if total_keywords > 0:
                scores[category] = (scores[category] / total_keywords) * config['weight']
        
        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores.values() else 1.0
        if max_score > 0:
            scores = {cat: score / max_score for cat, score in scores.items()}
        
        return scores
    
    def _pattern_classification(self, text: str) -> Dict[ReportCategory, float]:
        """Pattern-based classification using regex."""
        scores = {category: 0.0 for category in ReportCategory}
        
        for category, config in self.category_patterns.items():
            pattern_matches = 0
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                pattern_matches += len(matches)
            
            # Score based on pattern matches and category weight
            scores[category] = min(pattern_matches * 0.3 * config['weight'], 1.0)
        
        return scores
    
    async def _contextual_classification(self, text: str, context: Dict[str, Any]) -> Dict[ReportCategory, float]:
        """Contextual classification using additional metadata."""
        scores = {category: 0.0 for category in ReportCategory}
        
        # Location-based context
        if 'location_type' in context:
            location_scores = self._get_location_category_scores(context['location_type'])
            for category, score in location_scores.items():
                scores[category] += score * 0.2
        
        # Time-based context (emergency patterns)
        if self._is_emergency_context(text, context):
            scores[ReportCategory.EMERGENCY] += 0.4
        
        # User history context
        if 'user_history' in context:
            history_scores = self._get_user_history_scores(context['user_history'])
            for category, score in history_scores.items():
                scores[category] += score * 0.15
        
        return scores
    
    def _combine_scores(self, *score_dicts) -> Dict[ReportCategory, float]:
        """Combine multiple classification scores using weighted ensemble."""
        combined = {category: 0.0 for category in ReportCategory}
        
        weights = [0.4, 0.35, 0.25]  # keyword, pattern, contextual
        
        for weight, scores in zip(weights, score_dicts):
            for category, score in scores.items():
                combined[category] += score * weight
        
        return combined
    
    def _extract_primary_keywords(self, text: str, category: ReportCategory) -> List[str]:
        """Extract primary keywords that contributed to classification."""
        text_lower = text.lower()
        keywords = []
        
        if category in self.category_patterns:
            for keyword in self.category_patterns[category]['keywords']:
                if keyword in text_lower:
                    keywords.append(keyword)
        
        return keywords[:5]  # Return top 5 keywords
    
    def _get_classification_method(self, confidence: float) -> str:
        """Determine the primary classification method based on confidence."""
        if confidence >= 0.9:
            return "high_confidence_ensemble"
        elif confidence >= 0.75:
            return "ensemble_classification"
        elif confidence >= 0.6:
            return "keyword_dominant"
        else:
            return "low_confidence_fallback"
    
    def _get_all_keyword_matches(self, text: str) -> List[str]:
        """Get all keyword matches across all categories."""
        text_lower = text.lower()
        matches = []
        
        for category, config in self.category_patterns.items():
            for keyword in config['keywords']:
                if keyword in text_lower:
                    matches.append(keyword)
        
        return matches
    
    def _get_all_pattern_matches(self, text: str) -> List[str]:
        """Get all pattern matches across all categories."""
        matches = []
        
        for category, config in self.category_patterns.items():
            for pattern in config['patterns']:
                found_matches = re.findall(pattern, text, re.IGNORECASE)
                matches.extend(found_matches)
        
        return matches
    
    def _get_location_category_scores(self, location_type: str) -> Dict[ReportCategory, float]:
        """Get category scores based on location type."""
        location_mappings = {
            'hospital': {ReportCategory.HEALTHCARE: 0.8},
            'school': {ReportCategory.EDUCATION: 0.8},
            'police_station': {ReportCategory.PUBLIC_SAFETY: 0.8},
            'government_office': {ReportCategory.GOVERNMENT_SERVICES: 0.6},
            'residential_area': {ReportCategory.INFRASTRUCTURE: 0.4, ReportCategory.UTILITIES: 0.3},
            'commercial_area': {ReportCategory.INFRASTRUCTURE: 0.5, ReportCategory.TRANSPORTATION: 0.4}
        }
        
        return location_mappings.get(location_type, {})
    
    def _is_emergency_context(self, text: str, context: Dict[str, Any]) -> bool:
        """Determine if the context indicates an emergency."""
        emergency_keywords = ['emergency', 'urgent', 'immediate', 'critical', 'life-threatening']
        text_lower = text.lower()
        
        return any(keyword in text_lower for keyword in emergency_keywords)
    
    def _get_user_history_scores(self, user_history: List[Dict[str, Any]]) -> Dict[ReportCategory, float]:
        """Get category scores based on user history."""
        if not user_history:
            return {}
        
        category_counts = Counter()
        for report in user_history:
            category = report.get('category', ReportCategory.GENERAL.value)
            try:
                report_category = ReportCategory(category)
                category_counts[report_category] += 1
            except ValueError:
                continue
        
        total_reports = sum(category_counts.values())
        if total_reports == 0:
            return {}
        
        return {cat: count / total_reports for cat, count in category_counts.items()}