import os
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import BaseAIAgent
from .nlp import NLPEngine

logger = logging.getLogger(__name__)

class GroqChatbotAgent(BaseAIAgent):
    """
    Intelligent civic engagement chatbot using Groq API.
    Provides natural language responses to citizen inquiries about government services,
    report status, and civic engagement opportunities.
    """
    
    def __init__(self):
        super().__init__("GroqChatbotAgent")
        self.api_key = os.getenv('GROQ_API_KEY')
        
        # Groq model configuration (updated for November 2025)
        self.models = {
            'fast': 'llama-3.1-8b-instant',      # Fast responses
            'balanced': 'llama-3.1-8b-instant',  # Replacement for deprecated gemma2-9b-it
            'powerful': 'llama-3.1-70b-versatile' # Large, reasoning-capable
        }
        self.model_name = self.models['fast']  # Default to fast model
        
        # Knowledge base for civic information
        self.civic_knowledge = {
            'report_categories': {
                'infrastructure': 'Infrastructure includes roads, bridges, buildings, and public facilities.',
                'healthcare': 'Healthcare covers hospitals, clinics, medical services, and public health issues.',
                'public_safety': 'Public safety includes police, fire departments, security, and crime prevention.',
                'education': 'Education covers schools, universities, educational programs, and student services.',
                'environment': 'Environment includes pollution, waste management, parks, and environmental protection.',
                'corruption': 'Corruption reports involve bribery, fraud, misuse of public funds, or misconduct.',
                'transportation': 'Transportation includes public transit, traffic management, and road maintenance.',
                'utilities': 'Utilities cover water, electricity, gas, internet services, and infrastructure.',
                'emergency': 'Emergency reports involve natural disasters, urgent situations, or crises.'
            },
            'kenya_context': {
                'about_publicbridge': 'PublicBridge is a civic engagement platform connecting citizens with county departments in Kenya to report issues, track progress, and access services.',
                'service_channels': 'You can use county government channels, Huduma Centres, official hotlines, and the PublicBridge portal to access services.',
                'languages': 'Support is available in English and Kiswahili. Try asking in either language.'
            },
            'report_status': {
                'submitted': 'Your report has been received and is being reviewed by our team.',
                'under_review': 'Your report is currently being evaluated by the relevant department.',
                'assigned': 'Your report has been assigned to the appropriate team for action.',
                'in_progress': 'Work is currently underway to address your reported issue.',
                'resolved': 'Your reported issue has been successfully resolved.',
                'closed': 'This report has been closed. Thank you for your civic engagement!'
            },
            'civic_engagement': {
                'town_hall': 'Town hall meetings are held monthly. Check our calendar for upcoming dates.',
                'volunteer': 'We have various volunteer opportunities in community programs and events.',
                'feedback': 'Your feedback helps us improve services. You can submit suggestions anytime.',
                'contact': 'You can contact your local representatives through our official channels.'
            }
        }
        
        # Response templates for different scenarios
        self.response_templates = {
            'greeting': [
                "Hello! I'm your PublicBridge civic engagement assistant. How can I help you today?",
                "Karibu PublicBridge! Niko hapa kukusaidia. Unaweza uliza kuhusu huduma za serikali au kuripoti shida.",
                "Hi there! I help with county services in Kenya, report submissions, and tracking."
            ],
            'report_help': [
                "I can help you submit a report about civic issues in your county. What would you like to report?",
                "Let me guide you through submitting a report. What issue are you experiencing?",
                "I can assist with reporting civic issues. Please describe the problem you're facing."
            ],
            'status_inquiry': [
                "I can help you check the status of your report. Do you have your report ID or can you open your dashboard?",
                "Let me help you track your report. What's your report reference number?",
                "I can check your report status. Please provide your report ID if you have one."
            ],
            'general_help': [
                "I can help with civic questions, county services, report submissions, and general information.",
                "I'm here to assist with government services, reporting issues, and civic engagement.",
                "I can provide information about local services, help with reports, and answer civic questions."
            ],
            'unclear': [
                "I'm not sure I understand. Could you rephrase your question?",
                "Let me make sure I understand correctly. What specific information are you looking for?",
                "I want to help, but I need a bit more clarity. What would you like to know?"
            ]
        }
        
        self.conversation_memory = {}
        self.nlp_engine = NLPEngine()
        
        # Initialize Groq client
        self._initialize_groq_client()
    
    def _select_optimal_model(self, user_input: str, context: Dict = None) -> str:
        """Select the optimal Groq model based on input complexity."""
        try:
            # Use fast model for simple queries
            if len(user_input) < 50:
                return self.models['fast']
            
            # Use balanced model for medium complexity
            elif len(user_input) < 200:
                return self.models['balanced']
            
            # Use powerful model for complex queries or when context suggests complexity
            else:
                return self.models['powerful']
                
        except Exception as e:
            logger.warning(f"Model selection failed: {e}, using default")
            return self.models['fast']
    
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
                logger.info("Groq client initialized successfully")
            except ImportError:
                logger.warning("Groq library not installed. Install with: pip install groq")
                self.groq_client = None
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.groq_client = None
                
        except Exception as e:
            logger.error(f"Groq initialization failed: {e}")
            self.groq_client = None
    
    def _create_chatbot_prompt(self, user_input: str, context: Dict = None) -> str:
        """Create an optimized prompt for civic chatbot responses."""
        
        # Analyze user intent
        intent = self._detect_intent(user_input)
        
        # Build context-aware prompt
        system_context = """You are a helpful civic engagement assistant for PublicBridge (Kenya), a government-citizen communication platform. Your role is to:

1. Provide accurate information about government services and civic engagement
2. Help citizens understand how to submit reports and track their status
3. Answer questions about local government processes and services
4. Be empathetic and professional in all interactions
5. Encourage civic participation and engagement
6. Provide clear, actionable information
7. Maintain a friendly, approachable tone while being professional

IMPORTANT GUIDELINES:
- Always be helpful and provide accurate information
- If you don't know something, direct users to official channels
- Encourage civic engagement and participation
- Be sensitive to citizen concerns and frustrations
- Provide specific, actionable information when possible
- Maintain privacy and don't ask for personal information
- Keep responses concise but comprehensive

Civic Knowledge Base:"""
        
        # Add relevant knowledge based on intent
        if intent['primary_intent'] == 'report_help':
            system_context += f"\nReport Categories: {json.dumps(self.civic_knowledge['report_categories'], indent=2)}"
        elif intent['primary_intent'] == 'status_inquiry':
            system_context += f"\nReport Status Information: {json.dumps(self.civic_knowledge['report_status'], indent=2)}"
        elif intent['primary_intent'] == 'civic_info':
            system_context += f"\nCivic Engagement Info: {json.dumps(self.civic_knowledge['civic_engagement'], indent=2)}"
        
        # Always include Kenya context for better grounding
        system_context += f"\nKenya Context: {json.dumps(self.civic_knowledge['kenya_context'], indent=2)}"
        
        # Add conversation context if available
        conversation_history = ""
        if context and 'conversation_history' in context:
            recent_history = context['conversation_history'][-3:]  # Last 3 exchanges
            for exchange in recent_history:
                conversation_history += f"User: {exchange.get('user', '')}\n"
                conversation_history += f"Assistant: {exchange.get('assistant', '')}\n"
        
        prompt = f"""{system_context}

CONVERSATION HISTORY:
{conversation_history}

USER INPUT: "{user_input}"

DETECTED INTENT: {json.dumps(intent, indent=2)}

RESPONSE GUIDELINES:
1. Address the user's specific question or concern
2. Provide helpful, actionable information
3. Be empathetic if the user expresses frustration
4. Encourage civic engagement when appropriate
5. Keep the response conversational but professional
6. If relevant, mention how PublicBridge can help

Please provide a helpful response to the citizen's inquiry:"""
        
        return prompt
    
    def _detect_intent(self, user_input: str) -> Dict:
        """Detect user intent using NLP engine."""
        return self.nlp_engine.detect_intent(user_input)
    
    def generate_response(self, user_input: str, context: Dict = None) -> Dict:
        """
        Generate a contextual response to citizen inquiries.
        
        Args:
            user_input: The citizen's message
            context: Additional context (conversation history, user info, etc.)
            
        Returns:
            Response with generated text and metadata
        """
        try:
            if not user_input or not user_input.strip():
                return self._empty_response()
            
            # Check if Groq client is available
            if not self.groq_client:
                return self._generate_rule_based_response(user_input, context)
            
            # Create optimized prompt
            prompt = self._create_chatbot_prompt(user_input, context)
            
            # Select optimal model for this request
            selected_model = self._select_optimal_model(user_input, context)
            
            # Generate response using Groq
            try:
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful civic engagement assistant for PublicBridge Kenya."},
                        {"role": "user", "content": prompt}
                    ],
                    model=selected_model,
                    temperature=0.7,
                    max_tokens=300,
                    top_p=0.9,
                    stream=False
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean up response
                response_text = self._clean_response(response_text, user_input)
                
                # Detect sentiment and emotion for response quality
                sentiment_analysis = self._analyze_input_sentiment(user_input)
                
                return {
                    'response': response_text,
                    'confidence': 0.9,  # High confidence for Groq API responses
                    'intent': self._detect_intent(user_input),
                    'sentiment_analysis': sentiment_analysis,
                    'response_metadata': {
                        'model_used': selected_model,
                        'model_type': 'groq_dynamic',
                        'response_length': len(response_text),
                        'processing_time': self.get_processing_time(),
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': 0.9,
                        'api_provider': 'groq'
                    }
                }
                
            except Exception as api_error:
                logger.error(f"Groq API call failed: {api_error}")
                return self._generate_rule_based_response(user_input, context)
            
        except Exception as e:
            logger.error(f"Chatbot response generation failed: {e}")
            return self._fallback_response(user_input)
    
    def _clean_response(self, response_text: str, user_input: str) -> str:
        """Clean and format the generated response."""
        # Remove any remaining prompt artifacts
        response_text = re.sub(r'USER INPUT:.*', '', response_text, flags=re.DOTALL)
        response_text = re.sub(r'DETECTED INTENT:.*', '', response_text, flags=re.DOTALL)
        response_text = re.sub(r'RESPONSE GUIDELINES:.*', '', response_text, flags=re.DOTALL)
        
        # Remove JSON artifacts
        response_text = re.sub(r'\{[^}]*\}', '', response_text)
        
        # Clean up whitespace and formatting
        response_text = response_text.strip()
        
        # Ensure response is appropriate length
        if len(response_text) > 1000:
            response_text = response_text[:1000] + "..."
        
        # Ensure response ends properly
        if not response_text.endswith(('.', '!', '?')):
            response_text += "."
        
        return response_text
    
    def _analyze_input_sentiment(self, user_input: str) -> Dict:
        """Analyze sentiment of user input for response context."""
        try:
            # Simple sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'thank', 'appreciate', 'helpful']
            negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed']
            
            input_lower = user_input.lower()
            positive_count = sum(1 for word in positive_words if word in input_lower)
            negative_count = sum(1 for word in negative_words if word in input_lower)
            
            if negative_count > positive_count:
                return {'sentiment': 'negative', 'intensity': 'high' if negative_count > 2 else 'medium'}
            elif positive_count > negative_count:
                return {'sentiment': 'positive', 'intensity': 'high' if positive_count > 2 else 'medium'}
            else:
                return {'sentiment': 'neutral', 'intensity': 'low'}
                
        except Exception:
            return {'sentiment': 'neutral', 'intensity': 'low'}
    
    def _generate_rule_based_response(self, user_input: str, context: Dict = None) -> Dict:
        """Generate intelligent rule-based response using enhanced NLP."""
        # Analyze user intent with enhanced NLP
        intent = self._detect_intent(user_input)
        
        # Analyze sentiment
        sentiment_analysis = self._analyze_input_sentiment(user_input)
        
        # Get context-aware response
        response_text = self._get_contextual_response(intent, user_input, context, sentiment_analysis)
        
        return {
            'response': response_text,
            'confidence': intent.get('confidence', 0.7),
            'intent': intent,
            'sentiment_analysis': sentiment_analysis,
            'response_metadata': {
                'model_used': 'enhanced_rule_based',
                'response_length': len(response_text),
                'processing_time': 0.1,
                'timestamp': datetime.now().isoformat(),
                'confidence_score': intent.get('confidence', 0.7),
                'api_provider': 'rule_based'
            }
        }
    
    def _get_contextual_response(self, intent: Dict, user_input: str, context: Dict = None, sentiment: Dict = None) -> str:
        """Get contextual response based on intent and context."""
        primary_intent = intent.get('primary_intent', 'general')
        confidence = intent.get('confidence', 0.0)
        
        # Handle different intents with context awareness
        if primary_intent == 'greeting':
            if context and context.get('user_profile', {}).get('preferred_language') == 'sw':
                return "Habari! Mimi ni msaidizi wako wa PublicBridge. Ninaweza kukusaidia vipi leo?"
            return "Hello! I'm your PublicBridge civic engagement assistant. I can help you with government services, report submissions, and tracking. How can I assist you today?"
        
        elif primary_intent == 'civic_info':
            if 'publicbridge' in user_input.lower():
                return "PublicBridge is a civic engagement platform that connects citizens with county governments in Kenya. You can use it to report issues, track progress, access government services, and engage with your local representatives. It supports multiple languages and provides real-time updates on your submissions."
            return "I can provide information about government services, county departments, and civic processes in Kenya. What specific information do you need?"
        
        elif primary_intent == 'report_help':
            if context and context.get('user_has_active_reports'):
                return "I see you have active reports. I can help you submit a new report or check the status of existing ones. To submit a new report, please select your county and describe the issue you're experiencing."
            return "I can guide you through submitting a report to your county government. Please describe the issue you'd like to report, and I'll help you with the next steps."
        
        elif primary_intent == 'status_inquiry':
            return "To check your report status, you can either provide your report reference number or log into your PublicBridge dashboard where all your submissions are tracked with real-time updates."
        
        elif primary_intent == 'appreciation':
            return "Thank you for your kind words! I'm here to help make government services more accessible. Is there anything else I can assist you with today?"
        
        elif primary_intent == 'complaint':
            return "I understand your frustration. Let me help you address this issue properly. Can you provide more details about the problem you're experiencing? I can guide you through the appropriate channels for resolution."
        
        elif primary_intent == 'emergency':
            return "This sounds urgent. For immediate emergencies, please contact your local emergency services. For urgent government issues, I can help you submit a high-priority report that will be fast-tracked to the relevant department."
        
        elif primary_intent == 'goodbye':
            return "Thank you for using PublicBridge! Feel free to return anytime you need assistance with government services or civic engagement."
        
        else:
            # Handle unclear or general queries with helpful suggestions
            if confidence < 0.3:
                return "I want to help you, but I need a bit more information. I can assist with: reporting issues to county governments, checking report status, finding government services, or answering questions about civic processes. What would you like to know?"
            else:
                return "I'm here to help with government services and civic engagement in Kenya. You can ask me about reporting issues, tracking submissions, finding contact information for departments, or general civic processes. How can I assist you?"
    
    def _fallback_response(self, user_input: str) -> Dict:
        """Generate fallback response when all methods fail."""
        intent = self._detect_intent(user_input)
        
        # Simple rule-based responses
        if intent['primary_intent'] == 'greeting':
            response = "Hello! I'm your civic engagement assistant. How can I help you today?"
        elif intent['primary_intent'] == 'report_help':
            response = "I can help you submit a report about civic issues. Please open the PublicBridge Reports section to get started and select your county."
        elif intent['primary_intent'] == 'status_inquiry':
            response = "I can help you check your report status. Please provide your report ID or open your PublicBridge dashboard to track progress."
        elif intent['primary_intent'] == 'goodbye':
            response = "Thank you for using PublicBridge! Feel free to reach out anytime."
        else:
            response = "PublicBridge connects citizens with county departments in Kenya. I can help with county services, reporting issues, and tracking. What would you like to know?"
        
        return {
            'response': response,
            'confidence': 0.5,
            'intent': intent,
            'sentiment_analysis': {'sentiment': 'neutral', 'intensity': 'low'},
            'response_metadata': {
                'model_used': 'rule_based_fallback',
                'response_length': len(response),
                'processing_time': 0.1,
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.5,
                'api_provider': 'fallback'
            }
        }
    
    def _empty_response(self) -> Dict:
        """Return empty response for invalid input."""
        return {
            'response': "I'm sorry, I didn't receive any input. How can I help you?",
            'confidence': 0.0,
            'intent': {'primary_intent': 'unclear', 'confidence': 0.0},
            'sentiment_analysis': {'sentiment': 'neutral', 'intensity': 'low'},
            'response_metadata': {
                'model_used': self.model_name,
                'response_length': 0,
                'processing_time': 0,
                'timestamp': datetime.now().isoformat(),
                'confidence_score': 0.0,
                'api_provider': 'groq'
            }
        }
    
    def get_processing_time(self) -> float:
        """Get the processing time for the last operation."""
        return 0.1  # Placeholder for processing time
    
    async def _analyze(self, data: Dict) -> Dict[str, Any]:
        """
        Core AI analysis for the BaseAIAgent interface.
        
        Args:
            data: Dictionary containing 'user_input' and optional 'context'
            
        Returns:
            Analysis results with predictions and metadata
        """
        user_input = data.get('user_input', '')
        context = data.get('context', {})
        response_data = self.generate_response(user_input, context)
        
        return {
            'confidence': response_data['response_metadata']['confidence_score'],
            'predictions': {
                'response': response_data['response'],
                'intent': response_data['intent'],
                'sentiment': response_data['sentiment_analysis']
            },
            'metadata': response_data['response_metadata']
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            'Natural language conversation via Groq API',
            'Civic information provision',
            'Report submission guidance',
            'Status inquiry assistance',
            'Multilingual support',
            'Intent recognition',
            'Sentiment-aware responses',
            'Contextual conversation memory',
            'Robust fallback mechanisms'
        ]
    
    def health_check(self) -> Dict:
        """Check if the chatbot is properly configured and functional."""
        try:
            test_input = "Hello, can you help me submit a report?"
            result = self.generate_response(test_input)
            
            return {
                'status': 'healthy' if len(result['response']) > 10 else 'degraded',
                'groq_client_available': self.groq_client is not None,
                'api_key_configured': bool(self.api_key),
                'test_response': result,
                'model_name': self.model_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'groq_client_available': False,
                'api_key_configured': bool(self.api_key)
            }
