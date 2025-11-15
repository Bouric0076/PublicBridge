"""
AI Multi-Agent Orchestrator

Coordinates multiple AI agents to provide comprehensive report analysis.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from collections import Counter

from .base import BaseAIAgent, ReportCategory, UrgencyLevel, AIAnalysisResult, ReportAnalysis
from .groq_classifier import GroqClassifierAgent
from .groq_chatbot import GroqChatbotAgent
from .advanced_sentiment import AdvancedSentimentAnalyzer
from .llama_classifier import LlamaClassifierAgent  # Keep as fallback
from .civic_chatbot import CivicChatbotAgent  # Keep as fallback
from .conversation import ContextManager
from .analytics_tracker import ChatAnalyticsTracker
from .classifier import ReportClassifierAgent  # Keep as fallback
from .sentiment import SentimentAnalyzerAgent   # Keep as fallback

logger = logging.getLogger(__name__)

@dataclass
class ComprehensiveReportAnalysis:
    """Complete analysis results from all AI agents."""
    report_id: str
    timestamp: datetime
    category: ReportCategory
    urgency: UrgencyLevel
    confidence_score: float
    sentiment: str
    urgency_score: float
    priority_score: float
    key_entities: List[str]
    extracted_keywords: List[str]
    recommended_action: str
    processing_time: float
    agent_results: Dict[str, AIAnalysisResult]
    advanced_insights: Dict[str, Any] = None  # New field for Llama insights
    multilingual_analysis: Dict[str, Any] = None  # New field for multilingual support
    contextual_understanding: str = ""  # New field for context analysis

class MultiAgentOrchestrator:
    """
    Orchestrates multiple AI agents for comprehensive report analysis.
    
    Features:
    - Coordinates multiple specialized AI agents
    - Combines results with weighted scoring
    - Provides unified analysis output
    - Handles agent failures gracefully
    - Supports real-time processing
    """
    
    def __init__(self, use_advanced_agents: bool = True):
        """
        Initialize the orchestrator with AI agents.
        
        Args:
            use_advanced_agents: If True, use Llama-based agents; otherwise use fallback agents
        """
        self.use_advanced_agents = use_advanced_agents
        self.agents = {}
        
        # Initialize agents based on configuration
        if use_advanced_agents:
            try:
                # Use only Groq-based agents to avoid heavy ML dependencies
                self.agents['classifier'] = GroqClassifierAgent()
                # Use GroqClassifierAgent for sentiment analysis too (it handles urgency/emotion)
                self.agents['sentiment'] = GroqClassifierAgent()  
                self.agents['chatbot'] = GroqChatbotAgent()
                logger.info("Initialized with lightweight Groq-based agents")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq agents, using basic fallback: {e}")
                self._initialize_fallback_agents()
        else:
            self._initialize_fallback_agents()
        
        self.processing_stats = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'average_processing_time': 0.0
        }
        
        # Advanced analytics tracking
        self.advanced_stats = {
            'llama_insights_generated': 0,
            'multilingual_reports_processed': 0,
            'contextual_analysis_performed': 0,
            'chatbot_interactions': 0
        }

        self.context_manager = ContextManager()
        self.chat_analytics = ChatAnalyticsTracker()
        
    def analyze_report_sync(self, report_data: Dict[str, Any]) -> ComprehensiveReportAnalysis:
        """Synchronous wrapper for analyze_report for compatibility with synchronous code."""
        try:
            # Run the async method in an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new task
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.analyze_report(report_data))
            else:
                return loop.run_until_complete(self.analyze_report(report_data))
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.analyze_report(report_data))
            finally:
                loop.close()
    
    async def analyze_report(self, report_data: Dict[str, Any]) -> ComprehensiveReportAnalysis:
        """Perform comprehensive analysis using all available agents."""
        import time
        start_time = time.time()
        
        report_id = report_data.get('id', 'unknown')
        
        try:
            # Run all agents in parallel
            agent_tasks = []
            for agent_name, agent in self.agents.items():
                task = asyncio.create_task(agent.process(report_data))
                agent_tasks.append((agent_name, task))
            
            # Wait for all agents to complete
            agent_results = {}
            for agent_name, task in agent_tasks:
                try:
                    result = await task
                    agent_results[agent_name] = result
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    agent_results[agent_name] = AIAnalysisResult(
                        confidence=0.0,
                        predictions={},
                        metadata={'error': str(e)},
                        processing_time=0.0,
                        model_version="error"
                    )
            
            # Combine results
            combined_analysis = self._combine_agent_results(
                agent_results, report_data, report_id
            )
            
            processing_time = time.time() - start_time
            combined_analysis.processing_time = processing_time
            combined_analysis.agent_results = agent_results
            
            # Update statistics
            self._update_stats(processing_time, success=True)
            
            return combined_analysis
            
        except Exception as e:
            processing_time = time.time() - start_time
            self._update_stats(processing_time, success=False)
            
            logger.error(f"Comprehensive analysis failed for report {report_id}: {e}")
            
            # Return fallback analysis
            return ComprehensiveReportAnalysis(
                report_id=report_id,
                timestamp=datetime.now(),
                category=ReportCategory.GENERAL,
                urgency=UrgencyLevel.MEDIUM,
                confidence_score=0.0,
                sentiment='neutral',
                urgency_score=0.5,
                priority_score=0.5,
                key_entities=[],
                extracted_keywords=[],
                recommended_action='manual_review_required',
                processing_time=processing_time,
                agent_results={}
            )
    
    def _combine_agent_results(self, agent_results: Dict[str, AIAnalysisResult], 
                             report_data: Dict[str, Any], report_id: str) -> ComprehensiveReportAnalysis:
        """Combine results from multiple agents with enhanced Llama capabilities."""
        
        # Extract classifier results
        classifier_result = agent_results.get('classifier', AIAnalysisResult(0.0, {}, {}, 0.0, "error"))
        category = ReportCategory(classifier_result.predictions.get('category', 'general'))
        category_confidence = classifier_result.confidence
        
        # Extract sentiment results
        sentiment_result = agent_results.get('sentiment', AIAnalysisResult(0.0, {}, {}, 0.0, "error"))
        sentiment = sentiment_result.predictions.get('sentiment', 'neutral')
        urgency = UrgencyLevel(sentiment_result.predictions.get('urgency', 'medium'))
        urgency_score = sentiment_result.predictions.get('urgency_score', 0.5)
        emotional_intensity = sentiment_result.predictions.get('emotional_intensity', 0.0)
        
        # Calculate combined confidence score
        confidence_score = self._calculate_combined_confidence(agent_results)
        
        # Calculate priority score based on multiple factors
        priority_score = self._calculate_priority_score(
            category, urgency, category_confidence, urgency_score, emotional_intensity
        )
        
        # Extract keywords and entities
        key_entities = classifier_result.predictions.get('primary_keywords', [])
        extracted_keywords = self._extract_keywords(report_data.get('text', ''))
        
        # Generate recommended action
        recommended_action = self._generate_recommended_action(
            category, urgency, priority_score, confidence_score
        )
        
        # Extract advanced Llama insights if available
        advanced_insights = self._extract_advanced_insights(agent_results)
        multilingual_analysis = self._extract_multilingual_analysis(agent_results)
        contextual_understanding = self._extract_contextual_understanding(agent_results)
        
        return ComprehensiveReportAnalysis(
            report_id=report_id,
            timestamp=datetime.now(),
            category=category,
            urgency=urgency,
            confidence_score=confidence_score,
            sentiment=sentiment,
            urgency_score=urgency_score,
            priority_score=priority_score,
            key_entities=key_entities,
            extracted_keywords=extracted_keywords,
            recommended_action=recommended_action,
            processing_time=0.0,  # Will be set by caller
            agent_results=agent_results,
            advanced_insights=advanced_insights,
            multilingual_analysis=multilingual_analysis,
            contextual_understanding=contextual_understanding
        )
    
    def _extract_advanced_insights(self, agent_results: Dict[str, AIAnalysisResult]) -> Optional[Dict]:
        """Extract advanced insights from Llama-based agents."""
        if not self.use_advanced_agents:
            return None
        
        insights = {}
        
        # Extract from classifier
        classifier_result = agent_results.get('classifier')
        if classifier_result and classifier_result.metadata:
            insights.update({
                'contextual_summary': classifier_result.metadata.get('contextual_summary'),
                'urgency_indicators': classifier_result.metadata.get('urgency_indicators', []),
                'citizen_satisfaction_score': classifier_result.metadata.get('citizen_satisfaction_score'),
                'trend_prediction': classifier_result.metadata.get('trend_prediction')
            })
        
        # Extract from sentiment analyzer
        sentiment_result = agent_results.get('sentiment')
        if sentiment_result and sentiment_result.metadata:
            insights.update({
                'emotion_detection': sentiment_result.metadata.get('emotion_detection'),
                'citizen_frustration_level': sentiment_result.metadata.get('citizen_frustration_level'),
                'urgency_assessment': sentiment_result.metadata.get('urgency_assessment'),
                'satisfaction_prediction': sentiment_result.metadata.get('satisfaction_prediction')
            })
        
        # Filter out None values
        return {k: v for k, v in insights.items() if v is not None}
    
    def _extract_multilingual_analysis(self, agent_results: Dict[str, AIAnalysisResult]) -> Optional[Dict]:
        """Extract multilingual analysis results."""
        if not self.use_advanced_agents:
            return None
        
        multilingual = {}
        
        # Extract from classifier
        classifier_result = agent_results.get('classifier')
        if classifier_result and classifier_result.metadata:
            if 'detected_language' in classifier_result.metadata:
                multilingual['detected_language'] = classifier_result.metadata['detected_language']
            if 'translation_quality' in classifier_result.metadata:
                multilingual['translation_quality'] = classifier_result.metadata['translation_quality']
            if 'cultural_context' in classifier_result.metadata:
                multilingual['cultural_context'] = classifier_result.metadata['cultural_context']
        
        return multilingual if multilingual else None
    
    def _extract_contextual_understanding(self, agent_results: Dict[str, AIAnalysisResult]) -> str:
        """Extract contextual understanding from Llama analysis."""
        if not self.use_advanced_agents:
            return ""
        
        classifier_result = agent_results.get('classifier')
        if classifier_result and classifier_result.metadata:
            return classifier_result.metadata.get('contextual_understanding', "")
        
        return ""
    
    def _calculate_combined_confidence(self, agent_results: Dict[str, AIAnalysisResult]) -> float:
        """Calculate combined confidence score from all agents."""
        confidences = []
        weights = []
        
        # Weight different agents based on their reliability
        agent_weights = {
            'classifier': 0.6,
            'sentiment': 0.4
        }
        
        for agent_name, result in agent_results.items():
            if result.confidence > 0:
                confidences.append(result.confidence)
                weights.append(agent_weights.get(agent_name, 0.5))
        
        if not confidences:
            return 0.0
        
        # Weighted average
        weighted_sum = sum(conf * weight for conf, weight in zip(confidences, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0
    
    def _calculate_priority_score(self, category: ReportCategory, urgency: UrgencyLevel,
                                category_confidence: float, urgency_score: float, 
                                emotional_intensity: float) -> float:
        """Calculate overall priority score."""
        # Base urgency weight
        urgency_weights = {
            UrgencyLevel.CRITICAL: 1.0,
            UrgencyLevel.HIGH: 0.8,
            UrgencyLevel.MEDIUM: 0.5,
            UrgencyLevel.LOW: 0.2
        }
        
        urgency_weight = urgency_weights.get(urgency, 0.5)
        
        # Category importance weights
        category_weights = {
            ReportCategory.EMERGENCY: 1.0,
            ReportCategory.PUBLIC_SAFETY: 0.9,
            ReportCategory.HEALTHCARE: 0.85,
            ReportCategory.INFRASTRUCTURE: 0.7,
            ReportCategory.UTILITIES: 0.7,
            ReportCategory.ENVIRONMENT: 0.6,
            ReportCategory.TRANSPORTATION: 0.6,
            ReportCategory.EDUCATION: 0.5,
            ReportCategory.GOVERNMENT_SERVICES: 0.5,
            ReportCategory.CORRUPTION: 0.8,
            ReportCategory.GENERAL: 0.3
        }
        
        category_weight = category_weights.get(category, 0.5)
        
        # Calculate combined priority score
        priority_score = (
            urgency_weight * 0.4 +
            category_weight * 0.3 +
            category_confidence * 0.2 +
            urgency_score * 0.1
        )
        
        # Boost priority based on emotional intensity (citizen distress)
        emotional_boost = emotional_intensity * 0.1
        
        return min(priority_score + emotional_boost, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from report text."""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced with more sophisticated NLP)
        words = text.lower().split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'through',
            'during', 'before', 'after', 'above', 'below', 'between', 'among'
        }
        
        keywords = [word.strip('.,!?;:"()[]') for word in words 
                   if word.strip('.,!?;:"()[]') not in stop_words and len(word) > 2]
        
        # Return top keywords by frequency
        keyword_counts = Counter(keywords)
        return [keyword for keyword, count in keyword_counts.most_common(10)]
    
    def _generate_recommended_action(self, category: ReportCategory, urgency: UrgencyLevel,
                                   priority_score: float, confidence_score: float) -> str:
        """Generate recommended action based on analysis results."""
        
        # Low confidence - manual review required
        if confidence_score < 0.6:
            return 'manual_review_required'
        
        # Critical urgency - immediate action
        if urgency == UrgencyLevel.CRITICAL:
            return 'immediate_emergency_response'
        
        # High priority and high urgency - fast track
        if priority_score >= 0.8 and urgency == UrgencyLevel.HIGH:
            return 'fast_track_processing'
        
        # Medium-high priority - standard processing
        if priority_score >= 0.6:
            return 'standard_processing'
        
        # Low priority - routine processing
        return 'routine_processing'
    
    def _initialize_fallback_agents(self):
        """Initialize basic fallback agents."""
        self.agents['classifier'] = ReportClassifierAgent()
        self.agents['sentiment'] = SentimentAnalyzerAgent()
        self.agents['chatbot'] = CivicChatbotAgent()  # Use enhanced chatbot even in fallback
        self.use_advanced_agents = False
        logger.info("Initialized with fallback agents using enhanced chatbot")
    
    async def process_chatbot_message(self, user_input: str, context: Dict = None) -> Dict:
        """
        Process a chatbot message using the CivicChatbotAgent.
        
        Args:
            user_input: The citizen's message
            context: Additional context (conversation history, user info, etc.)
            
        Returns:
            Chatbot response with metadata
        """
        if 'chatbot' not in self.agents:
            return {
                'response': "Chatbot service is currently unavailable. Please try again later.",
                'error': 'Chatbot agent not initialized',
                'fallback': True
            }
        
        try:
            built_context = self.context_manager.build(context or {})
            chatbot_data = {'user_input': user_input, 'context': built_context}
            agent = self.agents['chatbot']
            if hasattr(agent, 'process'):
                result = await agent.process(chatbot_data)
            elif hasattr(agent, 'process_message'):
                resp = agent.process_message(user_input)
                result = {
                    'response': resp.message,
                    'confidence': resp.confidence,
                    'intent': {'primary_intent': resp.message_type},
                    'sentiment_analysis': {},
                    'response_metadata': {
                        'model_used': 'rule_based_simple',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                raise RuntimeError('Unsupported chatbot agent interface')
            self.advanced_stats['chatbot_interactions'] += 1
            if hasattr(result, 'predictions'):
                predictions = result.predictions
                response_data = {
                    'response': predictions.get('response', ''),
                    'confidence': result.confidence,
                    'intent': predictions.get('intent', {}),
                    'sentiment_analysis': predictions.get('sentiment', {}),
                    'response_metadata': result.metadata
                }
            else:
                response_data = result
            self.chat_analytics.record_interaction(
                built_context.get('user_id'),
                response_data.get('intent', {}).get('primary_intent'),
                response_data.get('confidence', 0.0),
                len(response_data.get('response', '')),
                False
            )
            return response_data
        except Exception as e:
            logger.error(f"Chatbot processing failed: {e}")
            self.chat_analytics.record_interaction(None, None, 0.0, 0, True)
            return {
                'response': "I'm having trouble processing your message. Please try again.",
                'error': str(e),
                'fallback': True
            }

    def process_chatbot_message_sync(self, user_input: str, context: Dict = None) -> Dict:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.process_chatbot_message(user_input, context))
            return loop.run_until_complete(self.process_chatbot_message(user_input, context))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.process_chatbot_message(user_input, context))
            finally:
                loop.close()
    
    def get_agent_capabilities(self) -> List[Dict[str, Any]]:
        """Get capabilities of all available agents."""
        capabilities = []
        for agent_name, agent in self.agents.items():
            # Check availability based on agent type
            if hasattr(agent, 'model') and agent.model is not None:
                available = True
            elif hasattr(agent, 'sentiment_pipeline') and agent.sentiment_pipeline is not None:
                available = True  # AdvancedSentimentAnalyzer uses pipelines
            elif hasattr(agent, 'llama_model') and agent.llama_model is not None:
                available = True  # LlamaClassifierAgent
            else:
                available = False
            
            agent_info = {
                'name': agent_name,
                'available': available,
                'capabilities': agent.get_capabilities() if hasattr(agent, 'get_capabilities') else ['Basic processing available']
            }
            capabilities.append(agent_info)
        return capabilities
    
    def _update_stats(self, processing_time: float, success: bool):
        """Update processing statistics."""
        self.processing_stats['total_analyses'] += 1
        
        if success:
            self.processing_stats['successful_analyses'] += 1
        else:
            self.processing_stats['failed_analyses'] += 1
        
        # Update average processing time
        current_avg = self.processing_stats['average_processing_time']
        total_analyses = self.processing_stats['total_analyses']
        self.processing_stats['average_processing_time'] = (
            (current_avg * (total_analyses - 1) + processing_time) / total_analyses
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the orchestrator."""
        total = self.processing_stats['total_analyses']
        successful = self.processing_stats['successful_analyses']
        
        metrics = {
            'total_analyses': total,
            'successful_analyses': successful,
            'failed_analyses': self.processing_stats['failed_analyses'],
            'success_rate': successful / total if total > 0 else 0.0,
            'average_processing_time': self.processing_stats['average_processing_time'],
            'agent_performance': {
                agent_name: agent.processing_stats for agent_name, agent in self.agents.items()
            },
            'agent_capabilities': self.get_agent_capabilities(),
            'advanced_agents_enabled': self.use_advanced_agents
        }
        
        # Add advanced metrics if using Llama agents
        if self.use_advanced_agents:
            metrics['advanced_analytics'] = self.advanced_stats
        
        return metrics
