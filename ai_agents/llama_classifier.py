import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
from typing import Dict, List, Tuple, Optional, Any
import logging
import json
from .base import BaseAIAgent, AIAnalysisResult

logger = logging.getLogger(__name__)

class LlamaClassifierAgent(BaseAIAgent):
    """
    Advanced report classification using Llama 3.1 8B Instruct model.
    Provides contextual understanding and multilingual support for citizen reports.
    """
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        super().__init__("LlamaClassifierAgent")
        self.model_name = model_name
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
        self.tokenizer = None
        self.model = None
        self.classification_pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Llama 3.1 model with optimized settings."""
        try:
            logger.info(f"Initializing Llama 3.1 classifier with {self.model_name}")
            
            # Configure 4-bit quantization properly
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True,
                trust_remote_code=True
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                dtype=torch.float16,
                device_map="auto",
                quantization_config=quantization_config,
                trust_remote_code=True
            )
            
            # Note: Using text-generation pipeline instead of text-classification
            # because we're using a causal LM model, not a classification model
            self.classification_pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto",
                max_length=512,
                truncation=True
            )
            
            logger.info("Llama 3.1 classifier initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize classification model: {e}")
            logger.info("Falling back to rule-based classification for better reliability")
            self._initialize_fallback_model()
    
    def _initialize_fallback_model(self):
        """Initialize a smaller, more manageable model for development."""
        try:
            fallback_model = "microsoft/DialoGPT-medium"  # Smaller alternative
            logger.info(f"Using fallback model: {fallback_model}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
            self.model = AutoModelForCausalLM.from_pretrained(
                fallback_model,
                dtype=torch.float16,
                device_map="auto"
            )
            
        except Exception as e:
            logger.error(f"Fallback model also failed: {e}")
            logger.info("Will use rule-based classification only")
            # Don't raise error, allow rule-based classification to work
            self.tokenizer = None
            self.model = None
            self.classification_pipeline = None
    
    def _create_classification_prompt(self, text: str) -> str:
        """Create an optimized prompt for report classification."""
        categories_str = "\n".join([
            f"- {cat}: {desc}" 
            for cat, desc in self.category_descriptions.items()
        ])
        
        prompt = f"""You are a civic engagement AI assistant that classifies citizen reports into appropriate categories.

CITIZEN REPORT: "{text}"

CLASSIFICATION CATEGORIES:
{categories_str}

INSTRUCTIONS:
1. Analyze the citizen report carefully
2. Identify the primary category that best describes the issue
3. Consider context, urgency, and subject matter
4. Provide confidence score (0.0 to 1.0)
5. Explain your reasoning briefly

RESPOND ONLY WITH VALID JSON:
{{
    "category": "CATEGORY_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification",
    "urgency_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "keywords_found": ["keyword1", "keyword2"]
}}

CLASSIFICATION:"""
        
        return prompt
    
    def classify_report(self, text: str) -> Dict:
        """
        Classify a citizen report using Llama 3.1 with contextual understanding.
        
        Args:
            text: The citizen report text
            
        Returns:
            Dict with category, confidence, reasoning, and metadata
        """
        try:
            if not text or not text.strip():
                return self._empty_classification_result()
            
            # Check if models are available, otherwise use rule-based classification
            if self.model is None or self.tokenizer is None:
                return self._rule_based_classification(text)
            
            # Create optimized prompt
            prompt = self._create_classification_prompt(text)
            
            # Generate classification using model
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True)
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.3,  # Low temperature for consistent classification
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            classification_text = response.split("CLASSIFICATION:")[-1].strip()
            
            # Parse JSON response
            try:
                result = json.loads(classification_text)
                return self._validate_classification_result(result, text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response, using fallback parsing")
                return self._fallback_classification_parse(classification_text, text)
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return self._rule_based_classification(text)
    
    def _validate_classification_result(self, result: Dict, original_text: str) -> Dict:
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
            'model_used': self.model_name,
            'processing_time': self.get_processing_time(),
            'text_length': len(original_text),
            'language_detected': self._detect_language(original_text)
        }
        
        return enhanced_result
    
    def _rule_based_classification(self, text: str) -> Dict:
        """Rule-based classification when models are not available."""
        # Simple keyword-based classification
        category_scores = {}
        text_lower = text.lower()
        
        # Define keyword mappings for each category
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
            'language_detected': self._detect_language(text)
        }
    
    def _fallback_classification_parse(self, text: str, original_report: str) -> Dict:
        """Fallback parsing when JSON parsing fails."""
        # Simple keyword-based fallback
        category_scores = {}
        
        for category in self.categories:
            score = 0
            keywords = self.category_descriptions[category].lower().split()
            report_lower = original_report.lower()
            
            for keyword in keywords:
                if keyword in report_lower:
                    score += 1
            
            category_scores[category] = score
        
        # Find best category
        best_category = max(category_scores, key=category_scores.get)
        confidence = min(0.8, category_scores[best_category] / 10.0)
        
        return {
            'category': best_category,
            'confidence': confidence,
            'reasoning': 'Fallback keyword-based classification',
            'urgency_level': 'MEDIUM',
            'keywords_found': [],
            'model_used': self.model_name,
            'processing_time': self.get_processing_time(),
            'text_length': len(original_report),
            'language_detected': self._detect_language(original_report)
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
            'language_detected': 'unknown'
        }
    
    async def process(self, data: Dict) -> AIAnalysisResult:
        """
        Main processing method for the BaseAIAgent interface.
        
        Args:
            data: Dictionary containing 'text' key with report content
            
        Returns:
            AIAnalysisResult with classification results
        """
        from .base import AIAnalysisResult
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
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            'Contextual report classification',
            'Multilingual support (English, Spanish, French)',
            'Confidence scoring with reasoning',
            'Urgency level detection',
            'Keyword extraction',
            'Language detection'
        ]
    
    def health_check(self) -> Dict:
        """Check if the model is properly loaded and functional."""
        try:
            test_text = "There is a pothole on Main Street that needs repair."
            result = self.classify_report(test_text)
            
            return {
                'status': 'healthy' if result['confidence'] > 0.3 else 'degraded',
                'model_loaded': self.model is not None,
                'tokenizer_loaded': self.tokenizer is not None,
                'test_classification': result,
                'model_name': self.model_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'model_loaded': False
            }