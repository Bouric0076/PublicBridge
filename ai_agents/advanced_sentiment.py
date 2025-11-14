import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Dict, List, Tuple, Optional, Any
import logging
import numpy as np
from datetime import datetime
from .base import BaseAIAgent, AIAnalysisResult
from .device_manager import device_manager

logger = logging.getLogger(__name__)

class AdvancedSentimentAnalyzer(BaseAIAgent):
    """
    Advanced sentiment analysis using DistilBERT and specialized models.
    Provides multi-dimensional sentiment analysis, emotion detection, and urgency assessment.
    """
    
    def __init__(self):
        """Initialize the advanced sentiment analyzer with publicly available models."""
        super().__init__("AdvancedSentimentAnalyzer")
        
        try:
            # Primary sentiment model (publicly available)
            self.sentiment_model_name = "distilbert-base-uncased-finetuned-sst-2-english"
            
            # Specialized models for different aspects (publicly available)
            self.emotion_model_name = "j-hartmann/emotion-english-distilroberta-base"
            self.urgency_model_name = "mrm8488/bert-tiny-finetuned-sms-spam-detection"  # Repurposed for urgency
            
            self.sentiment_pipeline = None
            self.emotion_pipeline = None
            self.urgency_pipeline = None
            
            # Sentiment lexicons for enhancement
            self.urgency_indicators = {
                'immediate': ['urgent', 'emergency', 'critical', 'immediate', 'asap', 'quickly', 'rush'],
                'high': ['serious', 'dangerous', 'alarming', 'severe', 'major', 'broken', 'failed'],
                'medium': ['concern', 'issue', 'problem', 'trouble', 'difficulty'],
                'low': ['minor', 'small', 'slight', 'suggestion', 'improvement']
            }
            
            self.emotion_indicators = {
                'frustration': ['frustrated', 'annoyed', 'irritated', 'fed up', 'tired', 'sick'],
                'anger': ['angry', 'mad', 'furious', 'outraged', 'disgusted'],
                'fear': ['scared', 'afraid', 'worried', 'concerned', 'anxious'],
                'sadness': ['sad', 'disappointed', 'depressed', 'upset'],
                'joy': ['happy', 'pleased', 'satisfied', 'glad', 'excited']
            }
            
            self._initialize_models()
            logger.info("AdvancedSentimentAnalyzer initialized successfully with public models")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced sentiment models: {e}")
            # Fallback to basic sentiment analysis
            try:
                self.sentiment_pipeline = pipeline("sentiment-analysis")
                self.emotion_pipeline = None
                self.urgency_pipeline = None
                logger.info("AdvancedSentimentAnalyzer initialized with basic fallback")
            except Exception as fallback_error:
                logger.error(f"Fallback sentiment model also failed: {fallback_error}")
                self.sentiment_pipeline = None
                self.emotion_pipeline = None
                self.urgency_pipeline = None
    
    def _initialize_models(self):
        """Initialize all transformer models with optimized settings."""
        try:
            logger.info("Initializing advanced sentiment analysis models")
            
            # Primary sentiment analysis pipeline
            # Get optimal device configuration
            model_config = device_manager.get_model_config()
            
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.sentiment_model_name,
                tokenizer=self.sentiment_model_name,
                device_map=model_config.get('device_map'),
                max_length=512,
                truncation=True
            )
            
            # Emotion detection pipeline
            try:
                self.emotion_pipeline = pipeline(
                    "text-classification",
                    model=self.emotion_model_name,
                    tokenizer=self.emotion_model_name,
                    device_map=model_config.get('device_map'),
                    max_length=512,
                    truncation=True,
                    top_k=None  # Return all emotions with scores
                )
                logger.info(f"Emotion pipeline initialized with model: {self.emotion_model_name}")
                
                # Test the pipeline format with a simple text
                try:
                    test_result = self.emotion_pipeline("I am happy")
                    logger.info(f"Emotion pipeline test result format: {type(test_result)}, sample: {test_result[:2] if isinstance(test_result, list) else test_result}")
                except Exception as test_error:
                    logger.warning(f"Emotion pipeline test failed: {test_error}")
                    
            except Exception as emotion_error:
                logger.warning(f"Failed to initialize emotion pipeline: {emotion_error}")
                self.emotion_pipeline = None
            
            # Urgency detection pipeline (repurposed spam detection)
            self.urgency_pipeline = pipeline(
                "text-classification",
                model=self.urgency_model_name,
                tokenizer=self.urgency_model_name,
                device_map=model_config.get('device_map'),
                max_length=256,
                truncation=True
            )
            
            logger.info("Advanced sentiment models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced sentiment models: {e}")
            logger.info("Falling back to simpler models or rule-based analysis")
            self._initialize_fallback_models()
    
    def _initialize_fallback_models(self):
        """Initialize smaller models for development/testing."""
        try:
            logger.info("Using fallback models for sentiment analysis")
            
            # Use smaller, faster models
            fallback_sentiment = "distilbert-base-uncased-finetuned-sst-2-english"
            
            # Use centralized device configuration
            model_config = device_manager.get_model_config()
            
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=fallback_sentiment,
                device_map=model_config.get('device_map')
            )
            
            # Create simple rule-based emotion detection
            self.emotion_pipeline = None  # Will use rule-based approach
            self.urgency_pipeline = None  # Will use rule-based approach
            
        except Exception as e:
            logger.error(f"Fallback initialization also failed: {e}")
            raise RuntimeError("Could not initialize sentiment analysis models")
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Perform comprehensive sentiment analysis using multiple models.
        
        Args:
            text: The text to analyze
            
        Returns:
            Comprehensive sentiment analysis results
        """
        try:
            if not text or not text.strip():
                return self._empty_sentiment_result()
            
            # Basic sentiment analysis
            sentiment_result = self._analyze_basic_sentiment(text)
            
            # Emotion analysis
            emotion_result = self._analyze_emotions(text)
            
            # Urgency analysis
            urgency_result = self._analyze_urgency(text)
            
            # Intensity analysis
            intensity_result = self._analyze_intensity(text)
            
            # Combine all results
            comprehensive_result = {
                'sentiment': sentiment_result,
                'emotions': emotion_result,
                'urgency': urgency_result,
                'intensity': intensity_result,
                'overall_assessment': self._generate_overall_assessment(
                    sentiment_result, emotion_result, urgency_result, intensity_result
                ),
                'processing_metadata': {
                    'text_length': len(text),
                    'models_used': [
                        self.sentiment_model_name,
                        self.emotion_model_name if self.emotion_pipeline else 'rule_based',
                        self.urgency_model_name if self.urgency_pipeline else 'rule_based'
                    ],
                    'processing_timestamp': datetime.now().isoformat()
                }
            }
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._empty_sentiment_result()
    
    def _analyze_basic_sentiment(self, text: str) -> Dict:
        """Analyze basic positive/negative/neutral sentiment."""
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text[:512])[0]  # Truncate for model
                
                return {
                    'label': result['label'].lower(),
                    'confidence': float(result['score']),
                    'polarity': 1.0 if result['label'] == 'POSITIVE' else -1.0 if result['label'] == 'NEGATIVE' else 0.0,
                    'method': 'distilbert'
                }
            else:
                # Fallback to rule-based approach
                return self._rule_based_sentiment(text)
                
        except Exception as e:
            logger.warning(f"Basic sentiment analysis failed: {e}, using fallback")
            return self._rule_based_sentiment(text)
    
    def _analyze_emotions(self, text: str) -> Dict:
        """Analyze emotional content using specialized model."""
        try:
            if self.emotion_pipeline:
                results = self.emotion_pipeline(text[:512])
                
                # Debug logging to understand the format
                logger.debug(f"Emotion pipeline results type: {type(results)}")
                if isinstance(results, list) and len(results) > 0:
                    logger.debug(f"First result type: {type(results[0])}, content: {results[0]}")
                    # Log the full structure for debugging
                    logger.debug(f"Full results structure: {results}")
                else:
                    logger.debug(f"Results content: {results}")
                
                # Convert to emotion dictionary
                emotions = {}
                
                # Handle different return formats from the emotion pipeline
                if isinstance(results, list) and len(results) > 0:
                    # Handle nested list format: [[{...}, {...}]]
                    if isinstance(results[0], list) and len(results[0]) > 0 and isinstance(results[0][0], dict):
                        # Format: [[{'label': 'joy', 'score': 0.9}, ...]]
                        emotion_list = results[0]  # Extract the inner list
                        for emotion_data in emotion_list:
                            if 'label' in emotion_data and 'score' in emotion_data:
                                try:
                                    # Handle nested score format
                                    score = emotion_data['score']
                                    if isinstance(score, dict):
                                        # Sometimes score is nested like {'score': 0.9}
                                        score = score.get('score', score)
                                    emotions[emotion_data['label']] = float(score)
                                except (ValueError, TypeError) as score_error:
                                    logger.warning(f"Could not convert score to float: {score}, error: {score_error}")
                                    continue
                    elif isinstance(results[0], dict):
                        # Format: [{'label': 'joy', 'score': 0.9}, ...]
                        for emotion_data in results:
                            if 'label' in emotion_data and 'score' in emotion_data:
                                try:
                                    # Handle nested score format
                                    score = emotion_data['score']
                                    if isinstance(score, dict):
                                        # Sometimes score is nested like {'score': 0.9}
                                        score = score.get('score', score)
                                    emotions[emotion_data['label']] = float(score)
                                except (ValueError, TypeError) as score_error:
                                    logger.warning(f"Could not convert score to float: {score}, error: {score_error}")
                                    continue
                    elif isinstance(results[0], list) and len(results[0]) >= 2 and isinstance(results[0][0], str):
                        # Format: [['joy', 0.9], ['sadness', 0.1], ...]
                        for emotion_data in results:
                            if len(emotion_data) >= 2:
                                emotions[emotion_data[0]] = float(emotion_data[1])
                    else:
                        # Unexpected format, use fallback
                        logger.warning(f"Unexpected emotion pipeline format: {type(results[0])}")
                        return self._rule_based_emotions(text)
                else:
                    # Empty or invalid results
                    logger.warning("Empty emotion pipeline results")
                    return self._rule_based_emotions(text)
                
                # Ensure we have emotions data
                if not emotions:
                    logger.warning("No emotions extracted from pipeline results")
                    return self._rule_based_emotions(text)
                
                # Find dominant emotion
                dominant_emotion = max(emotions, key=emotions.get)
                
                return {
                    'emotions': emotions,
                    'dominant_emotion': dominant_emotion,
                    'dominant_score': emotions[dominant_emotion],
                    'method': 'distilroberta'
                }
            else:
                return self._rule_based_emotions(text)
                
        except Exception as e:
            logger.warning(f"Emotion analysis failed: {e}, using fallback")
            return self._rule_based_emotions(text)
    
    def _analyze_urgency(self, text: str) -> Dict:
        """Analyze urgency level using specialized model."""
        try:
            if self.urgency_pipeline:
                result = self.urgency_pipeline(text[:256])[0]
                
                # Convert spam detection to urgency (spam = high urgency)
                urgency_score = float(result['score'])
                if result['label'] == 'SPAM':
                    urgency_level = 'HIGH' if urgency_score > 0.7 else 'MEDIUM'
                else:
                    urgency_level = 'LOW' if urgency_score > 0.7 else 'MEDIUM'
                
                return {
                    'urgency_level': urgency_level,
                    'urgency_score': urgency_score,
                    'method': 'bert-tiny'
                }
            else:
                return self._rule_based_urgency(text)
                
        except Exception as e:
            logger.warning(f"Urgency analysis failed: {e}, using fallback")
            return self._rule_based_urgency(text)
    
    def _analyze_intensity(self, text: str) -> Dict:
        """Analyze emotional intensity and strength."""
        try:
            # Count intensity indicators
            intensity_markers = {
                'very': text.lower().count('very'),
                'extremely': text.lower().count('extremely'),
                'really': text.lower().count('really'),
                'so': text.lower().count(' so '),
                '!': text.count('!'),
                'caps': sum(1 for c in text if c.isupper()) / len(text) if text else 0
            }
            
            # Calculate intensity score
            intensity_score = min(1.0, (
                intensity_markers['very'] * 0.1 +
                intensity_markers['extremely'] * 0.15 +
                intensity_markers['really'] * 0.1 +
                intensity_markers['so'] * 0.1 +
                intensity_markers['!'] * 0.1 +
                intensity_markers['caps'] * 0.3
            ))
            
            intensity_level = 'LOW'
            if intensity_score > 0.7:
                intensity_level = 'HIGH'
            elif intensity_score > 0.4:
                intensity_level = 'MEDIUM'
            
            return {
                'intensity_level': intensity_level,
                'intensity_score': intensity_score,
                'intensity_markers': intensity_markers,
                'method': 'rule_based'
            }
            
        except Exception as e:
            logger.warning(f"Intensity analysis failed: {e}")
            return {
                'intensity_level': 'MEDIUM',
                'intensity_score': 0.5,
                'intensity_markers': {},
                'method': 'rule_based'
            }
    
    def _rule_based_sentiment(self, text: str) -> Dict:
        """Fallback rule-based sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'pleased', 'thank', 'appreciate']
        negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed', 'hate', 'problem']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            label = 'positive'
            polarity = 1.0
            confidence = min(0.9, positive_count / 5.0)
        elif negative_count > positive_count:
            label = 'negative'
            polarity = -1.0
            confidence = min(0.9, negative_count / 5.0)
        else:
            label = 'neutral'
            polarity = 0.0
            confidence = 0.5
        
        return {
            'label': label,
            'confidence': confidence,
            'polarity': polarity,
            'method': 'rule_based'
        }
    
    def _rule_based_emotions(self, text: str) -> Dict:
        """Fallback rule-based emotion detection."""
        text_lower = text.lower()
        emotions = {}
        
        for emotion, indicators in self.emotion_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            emotions[emotion] = min(1.0, score / len(indicators))
        
        # Find dominant emotion
        if emotions:
            dominant_emotion = max(emotions, key=emotions.get)
            dominant_score = emotions[dominant_emotion]
        else:
            dominant_emotion = 'neutral'
            dominant_score = 0.5
        
        return {
            'emotions': emotions,
            'dominant_emotion': dominant_emotion,
            'dominant_score': dominant_score,
            'method': 'rule_based'
        }
    
    def _rule_based_urgency(self, text: str) -> Dict:
        """Fallback rule-based urgency detection."""
        text_lower = text.lower()
        
        # Check for urgency indicators
        immediate_count = sum(1 for word in self.urgency_indicators['immediate'] if word in text_lower)
        high_count = sum(1 for word in self.urgency_indicators['high'] if word in text_lower)
        medium_count = sum(1 for word in self.urgency_indicators['medium'] if word in text_lower)
        low_count = sum(1 for word in self.urgency_indicators['low'] if word in text_lower)
        
        # Determine urgency level
        if immediate_count > 0:
            urgency_level = 'CRITICAL'
            urgency_score = min(1.0, immediate_count * 0.3)
        elif high_count > 0:
            urgency_level = 'HIGH'
            urgency_score = min(1.0, high_count * 0.2)
        elif medium_count > 0:
            urgency_level = 'MEDIUM'
            urgency_score = min(0.8, medium_count * 0.15)
        else:
            urgency_level = 'LOW'
            urgency_score = min(0.6, low_count * 0.1)
        
        return {
            'urgency_level': urgency_level,
            'urgency_score': urgency_score,
            'method': 'rule_based'
        }
    
    def _generate_overall_assessment(self, sentiment: Dict, emotions: Dict, 
                                   urgency: Dict, intensity: Dict) -> Dict:
        """Generate overall sentiment assessment."""
        # Calculate overall citizen satisfaction score
        satisfaction_factors = [
            sentiment.get('polarity', 0) * 0.3,  # Sentiment weight
            (1.0 - emotions.get('emotions', {}).get('anger', 0)) * 0.2,  # Lower anger = higher satisfaction
            (1.0 - emotions.get('emotions', {}).get('frustration', 0)) * 0.2,  # Lower frustration
            (1.0 - urgency.get('urgency_score', 0)) * 0.15,  # Lower urgency = less stressed
            (1.0 - intensity.get('intensity_score', 0)) * 0.15  # Lower intensity = calmer
        ]
        
        satisfaction_score = max(0.0, min(1.0, sum(satisfaction_factors)))
        
        # Determine overall tone
        if satisfaction_score > 0.7:
            overall_tone = 'POSITIVE'
        elif satisfaction_score > 0.4:
            overall_tone = 'NEUTRAL'
        else:
            overall_tone = 'NEGATIVE'
        
        # Citizen engagement indicators
        engagement_level = 'HIGH' if intensity.get('intensity_score', 0) > 0.6 else 'MEDIUM'
        
        return {
            'citizen_satisfaction_score': satisfaction_score,
            'overall_tone': overall_tone,
            'engagement_level': engagement_level,
            'recommendation': self._generate_recommendation(sentiment, emotions, urgency, intensity)
        }
    
    def _generate_recommendation(self, sentiment: Dict, emotions: Dict, 
                                urgency: Dict, intensity: Dict) -> str:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Sentiment-based recommendations
        if sentiment.get('label') == 'negative' and sentiment.get('confidence', 0) > 0.7:
            recommendations.append("Address citizen concerns promptly")
        
        # Emotion-based recommendations
        if emotions.get('emotions', {}).get('anger', 0) > 0.6:
            recommendations.append("Consider escalation due to high anger levels")
        
        if emotions.get('emotions', {}).get('frustration', 0) > 0.6:
            recommendations.append("Provide clear communication to reduce frustration")
        
        # Urgency-based recommendations
        if urgency.get('urgency_level') in ['HIGH', 'CRITICAL']:
            recommendations.append("Prioritize immediate response")
        
        # Intensity-based recommendations
        if intensity.get('intensity_score', 0) > 0.7:
            recommendations.append("Monitor for follow-up communications")
        
        if not recommendations:
            recommendations.append("Standard processing recommended")
        
        return "; ".join(recommendations)
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result for error cases."""
        return {
            'sentiment': {
                'label': 'neutral',
                'confidence': 0.5,
                'polarity': 0.0,
                'method': 'error_fallback'
            },
            'emotions': {
                'emotions': {'neutral': 1.0},
                'dominant_emotion': 'neutral',
                'dominant_score': 1.0,
                'method': 'error_fallback'
            },
            'urgency': {
                'urgency_level': 'MEDIUM',
                'urgency_score': 0.5,
                'method': 'error_fallback'
            },
            'intensity': {
                'intensity_level': 'MEDIUM',
                'intensity_score': 0.5,
                'intensity_markers': {},
                'method': 'error_fallback'
            },
            'overall_assessment': {
                'citizen_satisfaction_score': 0.5,
                'overall_tone': 'NEUTRAL',
                'engagement_level': 'MEDIUM',
                'recommendation': 'Unable to analyze - insufficient data'
            },
            'processing_metadata': {
                'text_length': 0,
                'models_used': ['error_fallback'],
                'processing_timestamp': datetime.now().isoformat()
            }
        }
    
    async def _analyze(self, input_data: Dict) -> Dict:
        """
        Required method for BaseAIAgent interface.
        
        Args:
            input_data: Dictionary containing 'text' key with content to analyze
            
        Returns:
            AIAnalysisResult with sentiment analysis results
        """
        from .base import AIAnalysisResult
        
        text = input_data.get('text', '')
        if not text:
            return AIAnalysisResult(
                confidence=0.0,
                predictions={},
                metadata={'error': 'No text provided'},
                processing_time=0.0,
                model_version=self.version
            )
        
        import time
        start_time = time.time()
        
        try:
            # Perform comprehensive sentiment analysis
            sentiment_result = self.analyze_sentiment(text)
            
            processing_time = time.time() - start_time
            
            # Extract key predictions for BaseAIAgent interface
            predictions = {
                'sentiment': sentiment_result['sentiment']['label'],
                'sentiment_score': sentiment_result['sentiment']['confidence'],
                'urgency': sentiment_result['urgency']['urgency_level'],
                'urgency_score': sentiment_result['urgency']['urgency_score'],
                'emotional_intensity': sentiment_result['intensity']['intensity_score'],
                'dominant_emotion': sentiment_result['emotions']['dominant_emotion'],
                'citizen_satisfaction': sentiment_result['overall_assessment']['citizen_satisfaction_score']
            }
            
            # Calculate overall confidence
            confidence = min(
                sentiment_result['sentiment']['confidence'],
                sentiment_result['urgency']['urgency_score'],
                sentiment_result['intensity']['intensity_score']
            )
            
            return AIAnalysisResult(
                confidence=confidence,
                predictions=predictions,
                metadata={
                    'full_sentiment_analysis': sentiment_result,
                    'models_used': sentiment_result['processing_metadata']['models_used'],
                    'text_length': sentiment_result['processing_metadata']['text_length']
                },
                processing_time=processing_time,
                model_version=self.version
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Advanced sentiment analysis failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                predictions={},
                metadata={'error': str(e)},
                processing_time=processing_time,
                model_version=self.version
            )

    async def process(self, data: Dict) -> AIAnalysisResult:
        """
        Main processing method for the BaseAIAgent interface.
        
        Args:
            data: Dictionary containing 'text' key with content to analyze
            
        Returns:
            AIAnalysisResult with comprehensive sentiment analysis results
        """
        import time
        
        text = data.get('text', '')
        start_time = time.time()
        
        try:
            sentiment_result = self.analyze_sentiment(text)
            processing_time = time.time() - start_time
            
            # Extract key predictions for AIAnalysisResult
            predictions = {
                'sentiment': sentiment_result['sentiment']['label'],
                'sentiment_score': sentiment_result['sentiment']['confidence'],
                'urgency': sentiment_result['urgency']['urgency_level'],
                'urgency_score': sentiment_result['urgency']['urgency_score'],
                'emotional_intensity': sentiment_result['intensity']['intensity_score'],
                'dominant_emotion': sentiment_result['emotions']['dominant_emotion'],
                'citizen_satisfaction': sentiment_result['overall_assessment']['citizen_satisfaction_score']
            }
            
            # Calculate overall confidence
            confidence = min(
                sentiment_result['sentiment']['confidence'],
                sentiment_result['urgency']['urgency_score'],
                sentiment_result['intensity']['intensity_score']
            )
            
            return AIAnalysisResult(
                confidence=confidence,
                predictions=predictions,
                metadata={'full_sentiment_analysis': sentiment_result},
                processing_time=processing_time,
                model_version=self.version
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Process method failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                predictions={},
                metadata={'error': str(e)},
                processing_time=processing_time,
                model_version=self.version
            )
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            'Multi-dimensional sentiment analysis',
            'Emotion detection (anger, frustration, fear, etc.)',
            'Urgency level assessment',
            'Emotional intensity analysis',
            'Citizen satisfaction scoring',
            'Actionable recommendations',
            'Multilingual support',
            'Real-time processing'
        ]
    
    def health_check(self) -> Dict:
        """Check if all models are properly loaded and functional."""
        try:
            test_text = "I am very frustrated with the poor road conditions in my neighborhood!"
            result = self.analyze_sentiment(test_text)
            
            return {
                'status': 'healthy' if result['sentiment']['confidence'] > 0.5 else 'degraded',
                'sentiment_model': self.sentiment_pipeline is not None,
                'emotion_model': self.emotion_pipeline is not None,
                'urgency_model': self.urgency_pipeline is not None,
                'test_analysis': result,
                'models_loaded': [
                    self.sentiment_model_name,
                    self.emotion_model_name if self.emotion_pipeline else 'rule_based',
                    self.urgency_model_name if self.urgency_pipeline else 'rule_based'
                ]
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'sentiment_model': False,
                'emotion_model': False,
                'urgency_model': False
            }