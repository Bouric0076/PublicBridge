import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from .groq_chatbot import GroqChatbotAgent
from .groq_classifier import GroqClassifierAgent
from .device_manager import device_manager
from .exception_handler import (
    safe_ai_operation, 
    safe_classification_operation, 
    safe_sentiment_operation,
    error_logger,
    check_ai_agent_health
)

logger = logging.getLogger(__name__)

class GroqAIOrchestrator:
    """
    Orchestrator for Groq-based AI agents with robust fallback mechanisms.
    Manages chatbot, classification, and sentiment analysis operations.
    """
    
    def __init__(self):
        self.name = "GroqAIOrchestrator"
        self.version = "2.0.0"
        
        # Initialize agents
        self.chatbot_agent = None
        self.classifier_agent = None
        self.sentiment_agent = None
        
        # Performance tracking
        self.operation_counts = {
            'chatbot': 0,
            'classification': 0,
            'sentiment': 0,
            'errors': 0
        }
        
        self.initialization_status = {
            'chatbot': False,
            'classifier': False,
            'sentiment': False,
            'device_manager': False
        }
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all AI agents with error handling."""
        logger.info("Initializing Groq AI Orchestrator...")
        
        # Initialize device manager
        try:
            device_info = device_manager.health_check()
            self.initialization_status['device_manager'] = device_info['status'] == 'healthy'
            logger.info(f"Device manager status: {device_info['status']}")
        except Exception as e:
            logger.error(f"Device manager initialization failed: {e}")
            self.initialization_status['device_manager'] = False
        
        # Initialize chatbot agent
        try:
            self.chatbot_agent = GroqChatbotAgent()
            health = check_ai_agent_health(self.chatbot_agent)
            self.initialization_status['chatbot'] = health['status'] in ['healthy', 'degraded']
            logger.info(f"Chatbot agent initialized: {health['status']}")
        except Exception as e:
            logger.error(f"Chatbot agent initialization failed: {e}")
            self.chatbot_agent = None
            self.initialization_status['chatbot'] = False
        
        # Initialize classifier agent
        try:
            self.classifier_agent = GroqClassifierAgent()
            health = check_ai_agent_health(self.classifier_agent)
            self.initialization_status['classifier'] = health['status'] in ['healthy', 'degraded']
            logger.info(f"Classifier agent initialized: {health['status']}")
        except Exception as e:
            logger.error(f"Classifier agent initialization failed: {e}")
            self.classifier_agent = None
            self.initialization_status['classifier'] = False
        
        # Initialize sentiment agent - using fallback only
        self.sentiment_agent = None
        self.initialization_status['sentiment'] = False
        logger.info("Sentiment agent disabled - using fallback mechanisms only")
        
        # Log overall initialization status
        successful_agents = sum(self.initialization_status.values())
        total_agents = len(self.initialization_status)
        logger.info(f"AI Orchestrator initialized: {successful_agents}/{total_agents} components ready")
    
    @safe_ai_operation(
        user_friendly_message="I'm sorry, I'm having trouble responding right now. Please try again in a moment."
    )
    def generate_chatbot_response(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate chatbot response with comprehensive error handling.
        
        Args:
            user_input: User's message
            context: Optional conversation context
            
        Returns:
            Response dictionary with fallback handling
        """
        self.operation_counts['chatbot'] += 1
        
        if not self.chatbot_agent:
            logger.warning("Chatbot agent not available, using basic fallback")
            return self._basic_chatbot_fallback(user_input)
        
        try:
            response = self.chatbot_agent.generate_response(user_input, context)
            
            # Enhance response with orchestrator metadata
            response['response_metadata']['orchestrator'] = {
                'version': self.version,
                'operation_count': self.operation_counts['chatbot'],
                'agent_status': 'active'
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Chatbot response generation failed: {e}")
            self.operation_counts['errors'] += 1
            return self._basic_chatbot_fallback(user_input)
    
    @safe_classification_operation(fallback_category='INFRASTRUCTURE')
    def classify_report(self, text: str) -> Dict[str, Any]:
        """
        Classify citizen report with comprehensive error handling.
        
        Args:
            text: Report text to classify
            
        Returns:
            Classification result with fallback handling
        """
        self.operation_counts['classification'] += 1
        
        if not self.classifier_agent:
            logger.warning("Classifier agent not available, using basic fallback")
            return self._basic_classification_fallback(text)
        
        try:
            result = self.classifier_agent.classify_report(text)
            
            # Enhance result with orchestrator metadata
            result['orchestrator_metadata'] = {
                'version': self.version,
                'operation_count': self.operation_counts['classification'],
                'agent_status': 'active'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Report classification failed: {e}")
            self.operation_counts['errors'] += 1
            return self._basic_classification_fallback(text)
    
    @safe_sentiment_operation()
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment with comprehensive error handling.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result with fallback handling
        """
        self.operation_counts['sentiment'] += 1
        
        if not self.sentiment_agent:
            logger.warning("Sentiment agent not available, using basic fallback")
            return self._basic_sentiment_fallback(text)
        
        try:
            result = self.sentiment_agent.analyze_sentiment(text)
            
            # Enhance result with orchestrator metadata
            result['processing_metadata']['orchestrator'] = {
                'version': self.version,
                'operation_count': self.operation_counts['sentiment'],
                'agent_status': 'active'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            self.operation_counts['errors'] += 1
            return self._basic_sentiment_fallback(text)
    
    def comprehensive_analysis(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis including classification, sentiment, and response generation.
        
        Args:
            text: Input text to analyze
            context: Optional context information
            
        Returns:
            Comprehensive analysis results
        """
        logger.info(f"Starting comprehensive analysis for text: {text[:50]}...")
        
        results = {
            'input_text': text,
            'timestamp': datetime.now().isoformat(),
            'orchestrator_version': self.version
        }
        
        # Perform classification
        try:
            classification = self.classify_report(text)
            results['classification'] = classification
        except Exception as e:
            logger.error(f"Classification in comprehensive analysis failed: {e}")
            results['classification'] = {'error': str(e)}
        
        # Perform sentiment analysis
        try:
            sentiment = self.analyze_sentiment(text)
            results['sentiment'] = sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis in comprehensive analysis failed: {e}")
            results['sentiment'] = {'error': str(e)}
        
        # Generate chatbot response
        try:
            chatbot_response = self.generate_chatbot_response(text, context)
            results['chatbot_response'] = chatbot_response
        except Exception as e:
            logger.error(f"Chatbot response in comprehensive analysis failed: {e}")
            results['chatbot_response'] = {'error': str(e)}
        
        # Add summary
        results['summary'] = {
            'category': results.get('classification', {}).get('category', 'UNKNOWN'),
            'sentiment': results.get('sentiment', {}).get('sentiment', {}).get('label', 'unknown'),
            'urgency': results.get('classification', {}).get('urgency_level', 'MEDIUM'),
            'response_available': 'response' in results.get('chatbot_response', {})
        }
        
        return results
    
    def _basic_chatbot_fallback(self, user_input: str) -> Dict[str, Any]:
        """Basic rule-based chatbot fallback."""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            response = "Hello! I'm your PublicBridge civic engagement assistant. How can I help you today?"
        elif any(word in user_lower for word in ['report', 'submit', 'issue', 'problem']):
            response = "I can help you submit a report about civic issues. Please describe the problem you're experiencing."
        elif any(word in user_lower for word in ['status', 'track', 'check']):
            response = "I can help you check your report status. Please provide your report ID or access your dashboard."
        elif any(word in user_lower for word in ['thank', 'thanks']):
            response = "You're welcome! Is there anything else I can help you with?"
        elif any(word in user_lower for word in ['bye', 'goodbye', 'exit']):
            response = "Thank you for using PublicBridge! Feel free to return anytime."
        else:
            response = "I can help with government services, reporting issues, and civic engagement. What would you like to know?"
        
        return {
            'response': response,
            'confidence': 0.6,
            'intent': {'primary_intent': 'general', 'confidence': 0.6},
            'sentiment_analysis': {'sentiment': 'neutral', 'intensity': 'low'},
            'response_metadata': {
                'model_used': 'basic_fallback',
                'response_length': len(response),
                'processing_time': 0.01,
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.6,
                'api_provider': 'fallback'
            }
        }
    
    def _basic_classification_fallback(self, text: str) -> Dict[str, Any]:
        """Basic rule-based classification fallback."""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ['road', 'bridge', 'building', 'construction', 'infrastructure']):
            category = 'INFRASTRUCTURE'
        elif any(word in text_lower for word in ['hospital', 'clinic', 'doctor', 'medical', 'health']):
            category = 'HEALTHCARE'
        elif any(word in text_lower for word in ['police', 'crime', 'safety', 'security']):
            category = 'PUBLIC_SAFETY'
        elif any(word in text_lower for word in ['school', 'teacher', 'education']):
            category = 'EDUCATION'
        elif any(word in text_lower for word in ['pollution', 'waste', 'environment']):
            category = 'ENVIRONMENT'
        elif any(word in text_lower for word in ['corruption', 'bribe', 'fraud']):
            category = 'CORRUPTION'
        elif any(word in text_lower for word in ['bus', 'transport', 'traffic']):
            category = 'TRANSPORTATION'
        elif any(word in text_lower for word in ['water', 'electricity', 'power', 'utility']):
            category = 'UTILITIES'
        elif any(word in text_lower for word in ['emergency', 'urgent', 'critical']):
            category = 'EMERGENCY'
        else:
            category = 'INFRASTRUCTURE'  # Default
        
        urgency = 'HIGH' if any(word in text_lower for word in ['emergency', 'urgent', 'critical']) else 'MEDIUM'
        
        return {
            'category': category,
            'confidence': 0.5,
            'reasoning': 'Basic keyword-based classification fallback',
            'urgency_level': urgency,
            'keywords_found': [],
            'model_used': 'basic_fallback',
            'processing_time': 0.01,
            'text_length': len(text),
            'language_detected': 'en',
            'api_provider': 'fallback'
        }
    
    def _basic_sentiment_fallback(self, text: str) -> Dict[str, Any]:
        """Basic rule-based sentiment fallback."""
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'happy', 'satisfied', 'thank']
        negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            polarity = 1.0
        elif negative_count > positive_count:
            sentiment = 'negative'
            polarity = -1.0
        else:
            sentiment = 'neutral'
            polarity = 0.0
        
        return {
            'sentiment': {
                'label': sentiment,
                'confidence': 0.6,
                'polarity': polarity,
                'method': 'basic_fallback'
            },
            'emotions': {
                'emotions': {sentiment: 1.0},
                'dominant_emotion': sentiment,
                'dominant_score': 1.0,
                'method': 'basic_fallback'
            },
            'urgency': {
                'urgency_level': 'MEDIUM',
                'urgency_score': 0.5,
                'method': 'basic_fallback'
            },
            'intensity': {
                'intensity_level': 'MEDIUM',
                'intensity_score': 0.5,
                'intensity_markers': {},
                'method': 'basic_fallback'
            },
            'overall_assessment': {
                'citizen_satisfaction_score': 0.5,
                'overall_tone': sentiment.upper(),
                'engagement_level': 'MEDIUM',
                'recommendation': 'Basic analysis - limited capabilities'
            },
            'processing_metadata': {
                'text_length': len(text),
                'models_used': ['basic_fallback'],
                'processing_timestamp': datetime.now().isoformat()
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all agents."""
        health_status = {
            'orchestrator': {
                'status': 'healthy',
                'version': self.version,
                'timestamp': datetime.now().isoformat()
            },
            'agents': {},
            'device_manager': {},
            'operation_counts': self.operation_counts.copy(),
            'initialization_status': self.initialization_status.copy()
        }
        
        # Check device manager
        try:
            health_status['device_manager'] = device_manager.health_check()
        except Exception as e:
            health_status['device_manager'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check chatbot agent
        if self.chatbot_agent:
            try:
                health_status['agents']['chatbot'] = check_ai_agent_health(self.chatbot_agent)
            except Exception as e:
                health_status['agents']['chatbot'] = {'status': 'unhealthy', 'error': str(e)}
        else:
            health_status['agents']['chatbot'] = {'status': 'not_initialized'}
        
        # Check classifier agent
        if self.classifier_agent:
            try:
                health_status['agents']['classifier'] = check_ai_agent_health(self.classifier_agent)
            except Exception as e:
                health_status['agents']['classifier'] = {'status': 'unhealthy', 'error': str(e)}
        else:
            health_status['agents']['classifier'] = {'status': 'not_initialized'}
        
        # Check sentiment agent
        if self.sentiment_agent:
            try:
                health_status['agents']['sentiment'] = check_ai_agent_health(self.sentiment_agent)
            except Exception as e:
                health_status['agents']['sentiment'] = {'status': 'unhealthy', 'error': str(e)}
        else:
            health_status['agents']['sentiment'] = {'status': 'not_initialized'}
        
        # Determine overall status
        agent_statuses = [agent.get('status', 'unknown') for agent in health_status['agents'].values()]
        healthy_agents = sum(1 for status in agent_statuses if status in ['healthy', 'degraded'])
        
        if healthy_agents == 0:
            health_status['orchestrator']['status'] = 'critical'
        elif healthy_agents < len(agent_statuses):
            health_status['orchestrator']['status'] = 'degraded'
        else:
            health_status['orchestrator']['status'] = 'healthy'
        
        return health_status
    
    def get_capabilities(self) -> List[str]:
        """Get list of orchestrator capabilities."""
        capabilities = [
            'Groq-powered conversational AI',
            'Advanced report classification',
            'Multi-dimensional sentiment analysis',
            'Comprehensive error handling',
            'Robust fallback mechanisms',
            'Performance monitoring',
            'Health checking',
            'Device-aware optimization'
        ]
        
        # Add agent-specific capabilities
        if self.chatbot_agent:
            capabilities.extend(self.chatbot_agent.get_capabilities())
        if self.classifier_agent:
            capabilities.extend(self.classifier_agent.get_capabilities())
        if self.sentiment_agent:
            capabilities.extend(self.sentiment_agent.get_capabilities())
        
        return list(set(capabilities))  # Remove duplicates
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_operations = sum(self.operation_counts.values())
        error_rate = self.operation_counts['errors'] / max(total_operations, 1)
        
        return {
            'total_operations': total_operations,
            'operation_breakdown': self.operation_counts.copy(),
            'error_rate': error_rate,
            'success_rate': 1.0 - error_rate,
            'initialization_status': self.initialization_status.copy(),
            'error_summary': error_logger.get_error_summary(),
            'timestamp': datetime.now().isoformat()
        }

# Global orchestrator instance
groq_orchestrator = GroqAIOrchestrator()
