"""
Comprehensive Testing Suite for PublicBridge Chatbot Framework

This module provides comprehensive testing protocols for:
- Functional correctness validation
- Performance benchmarking
- User experience testing
- Integration testing
- Load testing and stress testing
"""

import unittest
import asyncio
import time
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any
from datetime import datetime, timedelta
import concurrent.futures
import threading

# Import the enhanced AI agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agents.conversation import ContextManager, ConversationTurn, UserProfile
from ai_agents.nlp import EnhancedNLPEngine, NLPEngine
from ai_agents.civic_chatbot import CivicChatbotAgent
from ai_agents.orchestrator import MultiAgentOrchestrator

logger = logging.getLogger(__name__)

class ChatbotFrameworkTestSuite:
    """
    Comprehensive test suite for the chatbot framework.
    
    Test Categories:
    1. Functional Testing
    2. Performance Testing
    3. Integration Testing
    4. User Experience Testing
    5. Load Testing
    6. Quality Metrics Validation
    """
    
    def __init__(self):
        """Initialize the test suite."""
        self.test_results = {
            'functional': {},
            'performance': {},
            'integration': {},
            'user_experience': {},
            'load_testing': {},
            'quality_metrics': {}
        }
        
        # Test data
        self.test_conversations = [
            {
                'input': 'Hello, I need help submitting a report about a broken road in Nairobi',
                'expected_intent': 'report_help',
                'expected_entities': ['nairobi', 'infrastructure'],
                'expected_urgency': 'medium'
            },
            {
                'input': 'Habari, nina tatizo la dharura la maji katika Kisumu',
                'expected_intent': 'emergency',
                'expected_entities': ['kisumu', 'water'],
                'expected_urgency': 'high',
                'expected_language': 'sw'
            },
            {
                'input': 'Can you check the status of my report? Reference number is 12345',
                'expected_intent': 'status_inquiry',
                'expected_entities': ['12345'],
                'expected_urgency': 'low'
            },
            {
                'input': 'Thank you for your excellent service!',
                'expected_intent': 'appreciation',
                'expected_sentiment': 'positive',
                'expected_urgency': 'low'
            },
            {
                'input': 'I am very frustrated with the poor service from the health department',
                'expected_intent': 'complaint',
                'expected_sentiment': 'negative',
                'expected_urgency': 'medium',
                'expected_escalation': True
            }
        ]

class TestConversationManagement(unittest.TestCase):
    """Test conversation management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.context_manager = ContextManager()
        self.test_user_id = "test_user_123"
        
    def test_session_creation(self):
        """Test session creation and initialization."""
        session_id = self.context_manager.start_session(self.test_user_id)
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.context_manager.active_sessions)
        
        session = self.context_manager.active_sessions[session_id]
        self.assertEqual(session.user_id, self.test_user_id)
        self.assertTrue(session.active)
        self.assertEqual(len(session.turns), 0)
    
    def test_conversation_turn_addition(self):
        """Test adding conversation turns."""
        session_id = self.context_manager.start_session(self.test_user_id)
        
        # Add a conversation turn
        intent = {'primary_intent': 'greeting', 'confidence': 0.9}
        sentiment = {'sentiment': 'positive', 'intensity': 0.7}
        
        turn = self.context_manager.add_turn(
            session_id=session_id,
            user_input="Hello, how can I submit a report?",
            assistant_response="Hello! I can help you submit a report. What issue would you like to report?",
            intent=intent,
            sentiment=sentiment
        )
        
        self.assertIsNotNone(turn.turn_id)
        self.assertEqual(turn.intent, intent)
        self.assertEqual(turn.sentiment, sentiment)
        
        # Check session has the turn
        session = self.context_manager.active_sessions[session_id]
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0], turn)
    
    def test_user_profile_creation(self):
        """Test user profile creation and updates."""
        session_id = self.context_manager.start_session(self.test_user_id)
        
        # Check user profile was created
        self.assertIn(self.test_user_id, self.context_manager.user_profiles)
        
        profile = self.context_manager.user_profiles[self.test_user_id]
        self.assertEqual(profile.user_id, self.test_user_id)
        self.assertEqual(profile.preferred_language, 'en')
        self.assertEqual(profile.total_interactions, 0)
    
    def test_context_building(self):
        """Test context building functionality."""
        session_id = self.context_manager.start_session(self.test_user_id)
        
        # Add some conversation history
        intent = {'primary_intent': 'report_help', 'confidence': 0.8}
        sentiment = {'sentiment': 'neutral', 'intensity': 0.5}
        
        self.context_manager.add_turn(
            session_id=session_id,
            user_input="I need to report a pothole",
            assistant_response="I can help you report that. Which county is this in?",
            intent=intent,
            sentiment=sentiment
        )
        
        # Build context
        context = self.context_manager.get_conversation_context(session_id)
        
        self.assertEqual(context['session_id'], session_id)
        self.assertEqual(context['user_id'], self.test_user_id)
        self.assertEqual(context['turn_count'], 1)
        self.assertIn('recent_conversation', context)
        self.assertIn('user_profile', context)
    
    def test_session_timeout(self):
        """Test session timeout functionality."""
        # Create context manager with short timeout for testing
        cm = ContextManager(session_timeout_minutes=0.01)  # 0.6 seconds
        
        session_id = cm.start_session(self.test_user_id)
        self.assertIn(session_id, cm.active_sessions)
        
        # Wait for timeout
        time.sleep(1)
        
        # Trigger cleanup
        cm._cleanup_expired_sessions()
        
        # Session should be removed
        self.assertNotIn(session_id, cm.active_sessions)

class TestNLPEngine(unittest.TestCase):
    """Test enhanced NLP engine functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nlp_engine = EnhancedNLPEngine()
    
    def test_intent_detection_english(self):
        """Test intent detection for English text."""
        result = self.nlp_engine.detect_intent("Hello, I need help submitting a report")
        
        self.assertEqual(result['primary_intent'], 'report_help')
        self.assertEqual(result['detected_language'], 'en')
        self.assertGreater(result['confidence'], 0.0)
        self.assertIn('greeting', result['secondary_intents'])
    
    def test_intent_detection_swahili(self):
        """Test intent detection for Swahili text."""
        result = self.nlp_engine.detect_intent("Habari, nina tatizo la dharura")
        
        self.assertEqual(result['primary_intent'], 'emergency')
        self.assertEqual(result['detected_language'], 'sw')
        self.assertGreater(result['confidence'], 0.0)
        self.assertTrue(result['requires_escalation'])
        self.assertEqual(result['urgency_level'], 'high')
    
    def test_entity_extraction(self):
        """Test entity extraction functionality."""
        text = "I have a water problem in Nairobi county, it's urgent"
        entities = self.nlp_engine.extract_entities(text)
        
        self.assertIn('locations', entities)
        self.assertIn('urgency_indicators', entities)
        
        # Check location extraction
        locations = entities['locations']
        nairobi_found = any(loc['name'] == 'nairobi' for loc in locations)
        self.assertTrue(nairobi_found)
        
        # Check urgency indicators
        self.assertIn('urgent', entities['urgency_indicators'])
    
    def test_sentiment_analysis(self):
        """Test sentiment and emotion analysis."""
        positive_text = "Thank you for the excellent service!"
        negative_text = "I am very frustrated with this terrible service"
        neutral_text = "Can you check my report status?"
        
        # Test positive sentiment
        result = self.nlp_engine.analyze_sentiment_and_emotion(positive_text)
        self.assertEqual(result['sentiment'], 'positive')
        self.assertEqual(result['emotion'], 'appreciation')
        
        # Test negative sentiment
        result = self.nlp_engine.analyze_sentiment_and_emotion(negative_text)
        self.assertEqual(result['sentiment'], 'negative')
        self.assertEqual(result['emotion'], 'frustration')
        
        # Test neutral sentiment
        result = self.nlp_engine.analyze_sentiment_and_emotion(neutral_text)
        self.assertEqual(result['sentiment'], 'neutral')
    
    def test_context_aware_intent_detection(self):
        """Test context-aware intent detection."""
        context = {
            'page_context': 'reports',
            'user_has_active_reports': True
        }
        
        result = self.nlp_engine.detect_intent("I need help", context)
        
        # Should boost report_help intent due to context
        self.assertIn('report_help', result['intent_scores'])
        self.assertGreater(result['intent_scores'].get('report_help', 0), 0)

class TestChatbotIntegration(unittest.TestCase):
    """Test chatbot integration and response generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chatbot = CivicChatbotAgent()
    
    def test_response_generation(self):
        """Test chatbot response generation."""
        user_input = "Hello, I need help submitting a report"
        
        response = self.chatbot.generate_response(user_input)
        
        self.assertIn('response', response)
        self.assertIn('confidence', response)
        self.assertIn('intent', response)
        self.assertIsInstance(response['response'], str)
        self.assertGreater(len(response['response']), 0)
    
    def test_multilingual_support(self):
        """Test multilingual response support."""
        swahili_input = "Habari, ninahitaji msaada"
        
        response = self.chatbot.generate_response(swahili_input)
        
        self.assertIn('response', response)
        self.assertGreater(len(response['response']), 0)
        # Should detect Swahili and respond appropriately
    
    def test_context_awareness(self):
        """Test context-aware responses."""
        context = {
            'conversation_history': [
                {'user': 'Hello', 'assistant': 'Hi, how can I help?'}
            ],
            'user_profile': {
                'preferred_language': 'en',
                'communication_style': 'formal'
            }
        }
        
        response = self.chatbot.generate_response("I need to follow up", context)
        
        self.assertIn('response', response)
        # Response should be contextually appropriate

class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance benchmarks and response times."""
    
    def setUp(self):
        """Set up performance testing fixtures."""
        self.chatbot = CivicChatbotAgent()
        self.nlp_engine = EnhancedNLPEngine()
        self.context_manager = ContextManager()
    
    def test_response_time_benchmarks(self):
        """Test response time benchmarks."""
        test_inputs = [
            "Hello, how can I submit a report?",
            "Check status of report 12345",
            "I have an emergency in Nairobi",
            "Thank you for your help"
        ]
        
        response_times = []
        
        for user_input in test_inputs:
            start_time = time.time()
            response = self.chatbot.generate_response(user_input)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Assert response time is under 5 seconds (target)
            self.assertLess(response_time, 5.0, f"Response time {response_time:.2f}s exceeds 5s target")
        
        average_response_time = sum(response_times) / len(response_times)
        logger.info(f"Average response time: {average_response_time:.2f}s")
        
        # Assert average response time is under 3 seconds
        self.assertLess(average_response_time, 3.0)
    
    def test_nlp_processing_speed(self):
        """Test NLP processing speed."""
        test_texts = [
            "I need to report a broken road in Nairobi county",
            "Habari, nina tatizo la maji katika Kisumu",
            "Can you check the status of my report?",
            "Emergency: There's a fire at the hospital"
        ]
        
        processing_times = []
        
        for text in test_texts:
            start_time = time.time()
            intent_result = self.nlp_engine.detect_intent(text)
            entity_result = self.nlp_engine.extract_entities(text)
            sentiment_result = self.nlp_engine.analyze_sentiment_and_emotion(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Assert processing time is under 1 second
            self.assertLess(processing_time, 1.0)
        
        average_processing_time = sum(processing_times) / len(processing_times)
        logger.info(f"Average NLP processing time: {average_processing_time:.3f}s")
    
    def test_memory_usage(self):
        """Test memory usage during conversation management."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple sessions and conversations
        session_ids = []
        for i in range(100):
            session_id = self.context_manager.start_session(f"user_{i}")
            session_ids.append(session_id)
            
            # Add multiple turns to each session
            for j in range(10):
                self.context_manager.add_turn(
                    session_id=session_id,
                    user_input=f"Message {j}",
                    assistant_response=f"Response {j}",
                    intent={'primary_intent': 'general', 'confidence': 0.5},
                    sentiment={'sentiment': 'neutral', 'intensity': 0.5}
                )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        logger.info(f"Memory usage increased by {memory_increase:.2f} MB for 100 sessions with 10 turns each")
        
        # Assert memory increase is reasonable (less than 100MB for this test)
        self.assertLess(memory_increase, 100)

class TestLoadAndStress(unittest.TestCase):
    """Test load handling and stress testing."""
    
    def setUp(self):
        """Set up load testing fixtures."""
        self.orchestrator = MultiAgentOrchestrator(use_advanced_agents=False)  # Use fallback for testing
    
    def test_concurrent_users(self):
        """Test handling of concurrent users."""
        def simulate_user_interaction(user_id):
            """Simulate a single user interaction."""
            try:
                response = self.orchestrator.process_chatbot_message_sync(
                    f"Hello from user {user_id}",
                    {'user_id': user_id}
                )
                return response is not None and 'response' in response
            except Exception as e:
                logger.error(f"User {user_id} interaction failed: {e}")
                return False
        
        # Simulate 50 concurrent users
        num_users = 50
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user_interaction, i) for i in range(num_users)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        logger.info(f"Concurrent user test: {success_rate:.2%} success rate")
        
        # Assert at least 90% success rate
        self.assertGreaterEqual(success_rate, 0.9)
    
    def test_high_volume_processing(self):
        """Test high volume message processing."""
        messages = [
            "Hello, I need help",
            "Check my report status",
            "I have an emergency",
            "Thank you for your service"
        ] * 25  # 100 total messages
        
        start_time = time.time()
        successful_responses = 0
        
        for i, message in enumerate(messages):
            try:
                response = self.orchestrator.process_chatbot_message_sync(
                    message,
                    {'user_id': f'user_{i % 10}'}  # 10 different users
                )
                if response and 'response' in response:
                    successful_responses += 1
            except Exception as e:
                logger.error(f"Message {i} processing failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        messages_per_second = len(messages) / total_time
        success_rate = successful_responses / len(messages)
        
        logger.info(f"Processed {messages_per_second:.2f} messages/second with {success_rate:.2%} success rate")
        
        # Assert reasonable throughput and success rate
        self.assertGreater(messages_per_second, 5)  # At least 5 messages/second
        self.assertGreaterEqual(success_rate, 0.95)  # At least 95% success rate

class TestQualityMetrics(unittest.TestCase):
    """Test quality metrics and accuracy validation."""
    
    def setUp(self):
        """Set up quality testing fixtures."""
        self.test_suite = ChatbotFrameworkTestSuite()
        self.nlp_engine = EnhancedNLPEngine()
        self.chatbot = CivicChatbotAgent()
    
    def test_intent_recognition_accuracy(self):
        """Test intent recognition accuracy against test data."""
        correct_predictions = 0
        total_predictions = len(self.test_suite.test_conversations)
        
        for test_case in self.test_suite.test_conversations:
            result = self.nlp_engine.detect_intent(test_case['input'])
            
            if result['primary_intent'] == test_case['expected_intent']:
                correct_predictions += 1
            else:
                logger.warning(f"Intent mismatch: expected {test_case['expected_intent']}, got {result['primary_intent']}")
        
        accuracy = correct_predictions / total_predictions
        logger.info(f"Intent recognition accuracy: {accuracy:.2%}")
        
        # Assert accuracy is above 80% (target: >90%)
        self.assertGreaterEqual(accuracy, 0.8)
    
    def test_entity_extraction_accuracy(self):
        """Test entity extraction accuracy."""
        correct_extractions = 0
        total_tests = 0
        
        for test_case in self.test_suite.test_conversations:
            if 'expected_entities' in test_case:
                total_tests += 1
                entities = self.nlp_engine.extract_entities(test_case['input'])
                
                # Check if expected entities are found
                found_entities = []
                for entity_list in entities.values():
                    if isinstance(entity_list, list):
                        for entity in entity_list:
                            if isinstance(entity, dict):
                                found_entities.append(entity.get('name', ''))
                            else:
                                found_entities.append(str(entity))
                    else:
                        found_entities.extend(entity_list)
                
                expected_found = all(
                    any(expected in found for found in found_entities)
                    for expected in test_case['expected_entities']
                )
                
                if expected_found:
                    correct_extractions += 1
        
        if total_tests > 0:
            accuracy = correct_extractions / total_tests
            logger.info(f"Entity extraction accuracy: {accuracy:.2%}")
            self.assertGreaterEqual(accuracy, 0.7)
    
    def test_response_quality_metrics(self):
        """Test response quality metrics."""
        quality_scores = []
        
        for test_case in self.test_suite.test_conversations:
            response = self.chatbot.generate_response(test_case['input'])
            
            # Quality metrics
            response_text = response.get('response', '')
            
            # Length check (should be substantial but not too long)
            length_score = 1.0 if 10 <= len(response_text) <= 500 else 0.5
            
            # Relevance check (basic keyword matching)
            input_words = test_case['input'].lower().split()
            response_words = response_text.lower().split()
            common_words = set(input_words) & set(response_words)
            relevance_score = min(len(common_words) / max(len(input_words), 1), 1.0)
            
            # Politeness check
            polite_words = ['please', 'thank', 'help', 'assist', 'welcome']
            politeness_score = 1.0 if any(word in response_text.lower() for word in polite_words) else 0.5
            
            # Combined quality score
            quality_score = (length_score + relevance_score + politeness_score) / 3
            quality_scores.append(quality_score)
        
        average_quality = sum(quality_scores) / len(quality_scores)
        logger.info(f"Average response quality score: {average_quality:.2f}/1.0")
        
        # Assert average quality is above 0.6
        self.assertGreaterEqual(average_quality, 0.6)

def run_comprehensive_tests():
    """Run the comprehensive test suite."""
    test_classes = [
        TestConversationManagement,
        TestNLPEngine,
        TestChatbotIntegration,
        TestPerformanceBenchmarks,
        TestLoadAndStress,
        TestQualityMetrics
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting PublicBridge Chatbot Framework Comprehensive Test Suite...")
    print("=" * 80)
    
    # Run the comprehensive tests
    test_result = run_comprehensive_tests()
    
    print("=" * 80)
    print(f"Tests run: {test_result.testsRun}")
    print(f"Failures: {len(test_result.failures)}")
    print(f"Errors: {len(test_result.errors)}")
    print(f"Success rate: {((test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun * 100):.1f}%")
    
    if test_result.failures:
        print("\nFailures:")
        for test, traceback in test_result.failures:
            print(f"- {test}: {traceback}")
    
    if test_result.errors:
        print("\nErrors:")
        for test, traceback in test_result.errors:
            print(f"- {test}: {traceback}")
