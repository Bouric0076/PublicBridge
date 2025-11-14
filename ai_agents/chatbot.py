import re
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ChatbotResponse:
    message: str
    confidence: float
    suggested_actions: List[str]
    requires_escalation: bool
    message_type: str
    context: Dict


class CitizenChatbotAgent:
    """AI-powered chatbot for citizen assistance."""
    
    def __init__(self):
        self.conversation_history = []
        self.performance_stats = {
            'total_messages': 0,
            'successful_responses': 0,
            'escalations': 0,
            'average_confidence': 0.0
        }
    
    def process_message(self, message: str) -> ChatbotResponse:
        """Process a user message and return a response."""
        self.performance_stats['total_messages'] += 1
        
        message_lower = message.strip().lower()
        message_type = self._classify_message(message_lower)
        response = self._generate_response(message_lower, message_type)
        
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_message': message,
            'bot_response': response.message,
            'confidence': response.confidence
        })
        
        return response
    
    def _classify_message(self, message: str) -> str:
        """Classify the type of user message."""
        if any(word in message for word in ['hello', 'hi', 'hey', 'habari', 'salamu']):
            return 'greeting'
        elif any(word in message for word in ['bye', 'goodbye', 'thanks', 'asante', 'kwaheri']):
            return 'goodbye'
        elif any(word in message for word in ['help', 'assist', 'msaada', 'nisaidie']):
            return 'help'
        elif any(word in message for word in ['report', 'issue', 'problem', 'ripoti', 'tatizo', 'shida']):
            return 'report_issue'
        elif any(word in message for word in ['track', 'status', 'fuatilia', 'hali']):
            return 'track_report'
        elif any(word in message for word in ['human', 'representative']):
            return 'escalation'
        else:
            return 'unknown'
    
    def _generate_response(self, message: str, message_type: str) -> ChatbotResponse:
        """Generate a response based on message type."""
        responses = {
            'greeting': ChatbotResponse(
                "Hello! I'm PublicBridge AI Assistant for Kenya county services. How can I help you today?",
                0.9, ['Report Issue', 'Track Report', 'Help'], False, 'greeting', {}
            ),
            'goodbye': ChatbotResponse(
                "Thank you for using PublicBridge! Have a great day!",
                0.9, [], False, 'goodbye', {}
            ),
            'help': ChatbotResponse(
                "I can help you report issues, track reports, or answer questions about county services (Huduma, departments, contacts).",
                0.8, ['Report Issue', 'Track Report', 'Department Info'], False, 'help', {}
            ),
            'report_issue': ChatbotResponse(
                "I can help you report an issue. Use the PublicBridge portal to select your county and submit a report. What type of issue?",
                0.7, ['Report in Portal', 'View Departments'], False, 'report_issue', {}
            ),
            'track_report': ChatbotResponse(
                "To track your report, please provide the report ID or log into your PublicBridge dashboard.",
                0.7, ['Login to Account', 'Provide Report ID'], False, 'track_report', {}
            ),
            'escalation': ChatbotResponse(
                "I'm connecting you with a human representative who can better assist you.",
                0.9, [], True, 'escalation', {}
            ),
            'unknown': ChatbotResponse(
                "I didn't understand that. I can help with reporting issues, tracking reports, or county services in Kenya.",
                0.3, ['Help', 'Report Issue'], False, 'unknown', {}
            )
        }
        
        return responses.get(message_type, responses['unknown'])
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics."""
        return {
            'total_messages': self.performance_stats['total_messages'],
            'successful_responses': self.performance_stats['successful_responses'],
            'escalations': self.performance_stats['escalations'],
            'average_confidence': 0.75,  # Mock value for demo
            'success_rate': 0.85  # Mock value for demo
        }
