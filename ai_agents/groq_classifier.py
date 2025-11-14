import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import BaseAIAgent, AIAnalysisResult

logger = logging.getLogger(__name__)

class GroqClassifierAgent(BaseAIAgent):
    """
    Advanced report classification using Groq API.
    Provides contextual understanding and multilingual support for citizen reports.
    """
    
    def __init__(self):
        super().__init__("GroqClassifierAgent")
        self.api_key = os.getenv('GROQ_API_KEY')
        
        # Groq model configuration (updated for November 2025)
        self.models = {
            'fast': 'llama-3.1-8b-instant',      # Fast classification
            'balanced': 'llama-3.1-8b-instant',  # Replacement for deprecated gemma2-9b-it
            'powerful': 'llama-3.1-70b-versatile' # Large, reasoning-capable
        }
        self.model_name = self.models['fast']  # Default to fast model
        
        self.categories = [
            'INFRASTRUCTURE', 'HEALTHCARE', 'PUBLIC_SAFETY', 'EDUCATION',
            'ENVIRONMENT', 'CORRUPTION', 'TRANSPORTATION', 'UTILITIES', 'EMERGENCY'
        ]
        
        self.category_descriptions = {
            'INFRASTRUCTURE': 'Roads, bridges, buildings, public facilities',
            'HEALTHCARE': 'Hospitals, clinics, medical services, health issues',
            'PUBLIC_SAFETY': 'Police, fire, security, crime, safety concerns',
            'EDUCATION': 'Schools, universities, educational services',
            'ENVIRONMENT': 'Pollution, waste management, environmental issues',
            'CORRUPTION': 'Bribery, fraud, government misconduct',
            'TRANSPORTATION': 'Public transit, traffic, transportation services',
            'UTILITIES': 'Water, electricity, gas, internet services',
            'EMERGENCY': 'Natural disasters, urgent situations, crises'
        }
        
        # Initialize Groq client
        self._initialize_groq_client()
    
    def _initialize_groq_client(self):
        """Initialize Groq API client."""
        try:
            if not self.api_key:
                logger.warning("GROQ_API_KEY not found in environment variables")
                self.groq_client = None
                return
                
            # Try to import and initialize Groq client
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.api_key)
                logger.info("Groq classifier client initialized successfully")
            except ImportError:
                logger.warning("Groq library not installed. Install with: pip install groq")
                self.groq_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.groq_client = None
                
        except Exception as e:
            logger.error(f"Groq initialization failed: {e}")
            self.groq_client = None
    
    def _create_classification_prompt(self, text: str) -> str:
        """Create an optimized prompt for report classification."""
        categories_str = "\n".join([
            f"- {cat}: {desc}" 
            for cat, desc in self.category_descriptions.items()
        ])
        
        prompt = f"""You are a civic engagement AI assistant that classifies citizen reports into appropriate categories for Kenya's county governments.

CITIZEN REPORT: "{text}"

CLASSIFICATION CATEGORIES:
{categories_str}

INSTRUCTIONS:
1. Analyze the citizen report carefully
2. Identify the primary category that best describes the issue
3. Consider context, urgency, and subject matter
4. Provide confidence score (0.0 to 1.0)
5. Explain your reasoning briefly
6. Assess urgency level based on content

RESPOND ONLY WITH VALID JSON in this exact format:
{{
    "category": "CATEGORY_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification",
    "urgency_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "keywords_found": ["keyword1", "keyword2"]
}}

Classification:"""
        
        return prompt
    
    def classify_report(self, text: str) -> Dict:
        """
        Classify a citizen report using Groq API with contextual understanding.
        
        Args:
            text: The citizen report text
            
        Returns:
            Dict with category, confidence, reasoning, and metadata
        """
        try:
            if not text or not text.strip():
                return self._empty_classification_result()
            
            # Check if Groq client is available
            if not self.groq_client:
                return self._rule_based_classification(text)
            
            # Create optimized prompt
            prompt = self._create_classification_prompt(text)
            
            # Use fast model for classification (it's usually sufficient)
            selected_model = self.models['fast']
            
            # Generate classification using Groq
            try:
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert civic report classifier for Kenya's government services."},
                        {"role": "user", "content": prompt}
                    ],
                    model=selected_model,
                    temperature=0.3,  # Low temperature for consistent classification
                    max_tokens=200,
                    top_p=0.9,
                    stream=False
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Parse JSON response
                try:
                    result = json.loads(response_text)
                    return self._validate_classification_result(result, text, selected_model)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON response, using fallback parsing")
                    return self._fallback_classification_parse(response_text, text, selected_model)
                    
            except Exception as api_error:
                logger.error(f"Groq API call failed: {api_error}")
                return self._rule_based_classification(text)
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return self._empty_classification_result()
    
    def _validate_classification_result(self, result: Dict, original_text: str, selected_model: str = None) -> Dict:
        """Validate and enhance the classification result."""
        # Ensure category is valid
        category = result.get('category', 'INFRASTRUCTURE')
        if category not in self.categories:
            category = self._find_closest_category(category)
        
        # Ensure confidence is within valid range
        confidence = max(0.0, min(1.0, float(result.get('confidence', 0.5))))
        
        # Add additional metadata
        enhanced_result = {
            'category': category,
            'confidence': confidence,
            'reasoning': result.get('reasoning', 'Contextual analysis performed'),
            'urgency_level': result.get('urgency_level', 'MEDIUM'),
            'keywords_found': result.get('keywords_found', []),
            'model_used': selected_model,
            'model_type': 'groq_fast',
            'processing_time': self.get_processing_time(),
            'text_length': len(original_text),
            'language_detected': self._detect_language(original_text),
            'api_provider': 'groq'
        }
        
        return enhanced_result
    
    def _rule_based_classification(self, text: str) -> Dict:
        """Fallback rule-based classification when API is unavailable."""
        # Simple keyword-based classification
        category_scores = {}
        text_lower = text.lower()
        
        # Define keyword mappings
        keyword_mappings = {
            'INFRASTRUCTURE': ['road', 'bridge', 'building', 'construction', 'pothole', 'sidewalk', 'street', 'highway', 'drainage', 'sewer', 'maintenance', 'repair', 'damaged', 'broken'],
            'HEALTHCARE': ['hospital', 'clinic', 'doctor', 'nurse', 'medical', 'health', 'sick', 'disease', 'medicine', 'treatment', 'patient', 'emergency', 'ambulance', 'covid', 'vaccine'],
            'PUBLIC_SAFETY': ['police', 'crime', 'safety', 'security', 'accident', 'theft', 'robbery', 'violence', 'fire', 'danger', 'threat', 'attack', 'assault'],
            'EDUCATION': ['school', 'teacher', 'student', 'education', 'university', 'college', 'classroom', 'academic', 'learning', 'curriculum', 'tuition', 'fees'],
            'ENVIRONMENT': ['pollution', 'waste', 'garbage', 'environment', 'air', 'water', 'contamination', 'toxic', 'chemical', 'smoke', 'noise', 'deforestation'],
            'CORRUPTION': ['corruption', 'bribe', 'bribery', 'fraud', 'embezzlement', 'kickback', 'extortion', 'misuse', 'abuse', 'illegal', 'unethical'],
            'TRANSPORTATION': ['bus', 'train', 'metro', 'subway', 'transportation', 'traffic', 'congestion', 'parking', 'vehicle', 'driver', 'route', 'schedule', 'delay'],
            'UTILITIES': ['electricity', 'power', 'water', 'gas', 'internet', 'utility', 'outage', 'disconnection', 'billing', 'service', 'supply', 'grid', 'network'],
            'EMERGENCY': ['emergency', 'urgent', 'immediate', 'critical', 'life-threatening', 'disaster', 'flood', 'earthquake', 'fire', 'medical emergency', 'accident', 'injury']
        }
        
        for category, keywords in keyword_mappings.items():
            score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    found_keywords.append(keyword)
            
            category_scores[category] = {
                'score': score,
                'keywords': found_keywords
            }
        
        # Find best category
        best_category = max(category_scores, key=lambda x: category_scores[x]['score'])
        best_score = category_scores[best_category]['score']
        confidence = min(0.8, best_score / 5.0)  # Normalize confidence
        
        # Determine urgency
        urgency_keywords = ['emergency', 'urgent', 'immediate', 'critical', 'life-threatening']
        urgency_level = 'HIGH' if any(word in text_lower for word in urgency_keywords) else 'MEDIUM'
        
        return {
            'category': best_category,
            'confidence': confidence,
            'reasoning': f'Rule-based classification based on {best_score} keyword matches',
            'urgency_level': urgency_level,
            'keywords_found': category_scores[best_category]['keywords'][:5],  # Top 5 keywords
            'model_used': 'rule_based_fallback',
            'processing_time': self.get_processing_time(),
            'text_length': len(text),
            'language_detected': self._detect_language(text),
            'api_provider': 'rule_based'
        }
    
    def _fallback_classification_parse(self, text: str, original_report: str, selected_model: str = None) -> Dict:
        """Fallback parsing when JSON parsing fails."""
        # Try to extract information from text response
        category = 'INFRASTRUCTURE'  # Default
        confidence = 0.5
        reasoning = 'Fallback text parsing'
        urgency_level = 'MEDIUM'
        keywords_found = []
        
        # Look for category mentions in response
        for cat in self.categories:
            if cat.lower() in text.lower():
                category = cat
                confidence = 0.7
                break
        
        # Look for urgency indicators
        if any(word in text.lower() for word in ['critical', 'high', 'urgent', 'emergency']):
            urgency_level = 'HIGH'
        elif any(word in text.lower() for word in ['low']):
            urgency_level = 'LOW'
        
        return {
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning,
            'urgency_level': urgency_level,
            'keywords_found': keywords_found,
            'model_used': selected_model or self.model_name,
            'processing_time': self.get_processing_time(),
            'text_length': len(original_report),
            'language_detected': self._detect_language(original_report),
            'api_provider': 'groq_fallback'
        }
    
    def _find_closest_category(self, category: str) -> str:
        """Find the closest valid category using string similarity."""
        category_lower = category.lower()
        
        # Direct mapping for common variations
        category_mapping = {
            'road': 'INFRASTRUCTURE',
            'building': 'INFRASTRUCTURE',
            'hospital': 'HEALTHCARE',
            'medical': 'HEALTHCARE',
            'police': 'PUBLIC_SAFETY',
            'crime': 'PUBLIC_SAFETY',
            'school': 'EDUCATION',
            'education': 'EDUCATION',
            'pollution': 'ENVIRONMENT',
            'waste': 'ENVIRONMENT',
            'bribe': 'CORRUPTION',
            'corrupt': 'CORRUPTION',
            'bus': 'TRANSPORTATION',
            'traffic': 'TRANSPORTATION',
            'water': 'UTILITIES',
            'electricity': 'UTILITIES',
            'emergency': 'EMERGENCY',
            'disaster': 'EMERGENCY'
        }
        
        for key, value in category_mapping.items():
            if key in category_lower:
                return value
        
        return 'INFRASTRUCTURE'  # Default fallback
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            # Simple heuristic based on character sets and common words
            text_lower = text.lower()
            
            # Kiswahili indicators
            swahili_words = ['na', 'ya', 'wa', 'ni', 'kwa', 'hii', 'hizo', 'haya', 'mimi', 'wewe']
            if any(word in text_lower for word in swahili_words):
                return 'sw'
            
            # Spanish indicators
            spanish_words = ['el', 'la', 'los', 'las', 'un', 'una', 'es', 'está', 'por', 'para']
            if any(word in text_lower for word in spanish_words):
                return 'es'
            
            # French indicators  
            french_words = ['le', 'la', 'les', 'un', 'une', 'est', 'pour', 'avec']
            if any(word in text_lower for word in french_words):
                return 'fr'
            
            return 'en'  # Default to English
            
        except Exception:
            return 'en'
    
    def _empty_classification_result(self) -> Dict:
        """Return empty classification result for error cases."""
        return {
            'category': 'INFRASTRUCTURE',
            'confidence': 0.1,
            'reasoning': 'Classification failed - insufficient data',
            'urgency_level': 'LOW',
            'keywords_found': [],
            'model_used': self.model_name,
            'processing_time': self.get_processing_time(),
            'text_length': 0,
            'language_detected': 'unknown',
            'api_provider': 'error'
        }
    
    def get_processing_time(self) -> float:
        """Get the processing time for the last operation."""
        return 0.1  # Placeholder for processing time
    
    async def process(self, data: Dict) -> AIAnalysisResult:
        """
        Main processing method for the BaseAIAgent interface.
        
        Args:
            data: Dictionary containing 'text' key with report content
            
        Returns:
            AIAnalysisResult with classification results
        """
        import time
        
        text = data.get('text', '')
        start_time = time.time()
        
        try:
            classification_result = self.classify_report(text)
            processing_time = time.time() - start_time
            
            # Extract key predictions for AIAnalysisResult
            predictions = {
                'category': classification_result.get('category', 'INFRASTRUCTURE'),
                'urgency_level': classification_result.get('urgency_level', 'MEDIUM'),
                'keywords_found': classification_result.get('keywords_found', [])
            }
            
            confidence = classification_result.get('confidence', 0.5)
            
            return AIAnalysisResult(
                confidence=confidence,
                predictions=predictions,
                metadata=classification_result,
                processing_time=processing_time,
                model_version=self.model_name
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Process method failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                predictions={},
                metadata={'error': str(e)},
                processing_time=processing_time,
                model_version=self.model_name
            )
    
    async def _analyze(self, input_data: Dict) -> Dict:
        """
        Required method for BaseAIAgent interface.
        
        Args:
            input_data: Dictionary containing 'text' key with content to analyze
            
        Returns:
            Analysis results with classification
        """
        text = input_data.get('text', '')
        if not text:
            return {
                'confidence': 0.0,
                'predictions': {},
                'metadata': {'error': 'No text provided'}
            }
        
        import time
        start_time = time.time()
        
        try:
            classification_result = self.classify_report(text)
            processing_time = time.time() - start_time
            
            # Extract key predictions
            predictions = {
                'category': classification_result.get('category', 'INFRASTRUCTURE'),
                'urgency_level': classification_result.get('urgency_level', 'MEDIUM'),
                'keywords_found': classification_result.get('keywords_found', [])
            }
            
            confidence = classification_result.get('confidence', 0.5)
            
            return {
                'confidence': confidence,
                'predictions': predictions,
                'metadata': {
                    'full_classification': classification_result,
                    'processing_time': processing_time
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Analysis failed: {e}")
            return {
                'confidence': 0.0,
                'predictions': {},
                'metadata': {'error': str(e), 'processing_time': processing_time}
            }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            'Contextual report classification via Groq API',
            'Multilingual support (English, Kiswahili, Spanish, French)',
            'Confidence scoring with reasoning',
            'Urgency level detection',
            'Keyword extraction',
            'Language detection',
            'Robust fallback mechanisms'
        ]
    
    def health_check(self) -> Dict:
        """Check if the classifier is properly configured and functional."""
        try:
            test_text = "There is a pothole on Main Street that needs repair."
            result = self.classify_report(test_text)
            
            return {
                'status': 'healthy' if result['confidence'] > 0.3 else 'degraded',
                'groq_client_available': self.groq_client is not None,
                'api_key_configured': bool(self.api_key),
                'test_classification': result,
                'model_name': self.model_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'groq_client_available': False,
                'api_key_configured': bool(self.api_key)
            }
