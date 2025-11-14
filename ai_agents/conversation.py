from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import uuid
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    turn_id: str
    user_input: str
    assistant_response: str
    intent: Dict[str, Any]
    sentiment: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class UserProfile:
    """User profile for personalization."""
    user_id: str
    preferred_language: str = 'en'
    communication_style: str = 'formal'  # formal, casual, technical
    frequent_topics: List[str] = None
    satisfaction_history: List[float] = None
    last_interaction: datetime = None
    total_interactions: int = 0
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.frequent_topics is None:
            self.frequent_topics = []
        if self.satisfaction_history is None:
            self.satisfaction_history = []
        if self.last_interaction is None:
            self.last_interaction = datetime.now()
        if self.preferences is None:
            self.preferences = {}

@dataclass
class ConversationSession:
    """Represents a conversation session."""
    session_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    turns: List[ConversationTurn]
    session_context: Dict[str, Any]
    goals: List[str]  # User goals for this session
    completed_goals: List[str]
    active: bool

class ContextManager:
    """
    Enhanced context manager with advanced conversation management capabilities.
    
    Features:
    - Multi-level memory management (short, medium, long-term)
    - User profile tracking and personalization
    - Session management with goal tracking
    - Context-aware conversation flow
    """
    
    def __init__(self, max_short_term_turns: int = 10, session_timeout_minutes: int = 30):
        """
        Initialize the enhanced context manager.
        
        Args:
            max_short_term_turns: Maximum turns to keep in short-term memory
            session_timeout_minutes: Minutes before session expires
        """
        self.defaults = {}
        self.max_short_term_turns = max_short_term_turns
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
        # Memory storage
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.conversation_history: Dict[str, List[ConversationTurn]] = defaultdict(list)
        
        # Context tracking
        self.global_context = {}
        self.topic_transitions = defaultdict(list)
        
        # Analytics
        self.interaction_stats = {
            'total_conversations': 0,
            'average_turns_per_conversation': 0.0,
            'most_common_intents': defaultdict(int),
            'satisfaction_trends': deque(maxlen=1000)
        }

    def build(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build enhanced context with conversation management.
        
        Args:
            context: Input context dictionary
            
        Returns:
            Enhanced context with conversation history and user profile
        """
        base = {}
        base.update(self.defaults)
        base.update(context or {})
        base['timestamp'] = datetime.utcnow().isoformat()
        
        # Handle conversation history
        history: List[Dict[str, str]] = base.get('conversation_history') or []
        base['conversation_history'] = history[-10:]
        
        # Add session context if available
        session_id = context.get('session_id')
        if session_id and session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            base['session_context'] = session.session_context
            base['active_goals'] = session.goals
            base['completed_goals'] = session.completed_goals
            base['turn_count'] = len(session.turns)
        
        # Add user profile context
        user_id = context.get('user_id')
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            base['user_profile'] = {
                'preferred_language': profile.preferred_language,
                'communication_style': profile.communication_style,
                'frequent_topics': profile.frequent_topics,
                'total_interactions': profile.total_interactions,
                'preferences': profile.preferences
            }
        
        return base
    
    def start_session(self, user_id: str, initial_context: Dict[str, Any] = None) -> str:
        """Start a new conversation session."""
        session_id = str(uuid.uuid4())
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        # Create new session
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            turns=[],
            session_context=initial_context or {},
            goals=[],
            completed_goals=[],
            active=True
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize user profile if not exists
        if user_id not in self.user_profiles:
            self._initialize_user_profile(user_id)
        
        logger.info(f"Started new session {session_id} for user {user_id}")
        return session_id
    
    def add_turn(self, session_id: str, user_input: str, assistant_response: str,
                 intent: Dict[str, Any], sentiment: Dict[str, Any],
                 additional_context: Dict[str, Any] = None) -> ConversationTurn:
        """Add a conversation turn to the session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or expired")
        
        session = self.active_sessions[session_id]
        turn_id = str(uuid.uuid4())
        
        # Create conversation turn
        turn = ConversationTurn(
            turn_id=turn_id,
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            sentiment=sentiment,
            timestamp=datetime.now(),
            context=self._build_turn_context(session, additional_context),
            metadata=self._extract_turn_metadata(user_input, assistant_response, intent)
        )
        
        # Add to session
        session.turns.append(turn)
        session.last_activity = datetime.now()
        
        # Maintain short-term memory limit
        if len(session.turns) > self.max_short_term_turns:
            # Move older turns to long-term storage
            old_turn = session.turns.pop(0)
            self.conversation_history[session.user_id].append(old_turn)
        
        # Update user profile
        self._update_user_profile(session.user_id, turn)
        
        # Update analytics
        self._update_analytics(turn)
        
        logger.debug(f"Added turn {turn_id} to session {session_id}")
        return turn
    
    def get_conversation_context(self, session_id: str, context_depth: str = "full") -> Dict[str, Any]:
        """Get comprehensive conversation context."""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        user_profile = self.user_profiles.get(session.user_id)
        
        context = {
            'session_id': session_id,
            'user_id': session.user_id,
            'session_start': session.start_time.isoformat(),
            'turn_count': len(session.turns),
            'session_context': session.session_context,
            'active_goals': session.goals,
            'completed_goals': session.completed_goals
        }
        
        # Add conversation history based on depth
        if context_depth in ["short", "medium", "full"]:
            recent_turns = session.turns[-5:] if len(session.turns) > 5 else session.turns
            context['recent_conversation'] = [
                {
                    'user': turn.user_input,
                    'assistant': turn.assistant_response,
                    'intent': turn.intent,
                    'sentiment': turn.sentiment,
                    'timestamp': turn.timestamp.isoformat()
                }
                for turn in recent_turns
            ]
        
        # Add user profile for medium and full context
        if context_depth in ["medium", "full"] and user_profile:
            context['user_profile'] = {
                'preferred_language': user_profile.preferred_language,
                'communication_style': user_profile.communication_style,
                'frequent_topics': user_profile.frequent_topics,
                'total_interactions': user_profile.total_interactions,
                'preferences': user_profile.preferences
            }
        
        return context
    
    def update_session_goals(self, session_id: str, goals: List[str]) -> None:
        """Update session goals."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].goals = goals
    
    def mark_goal_completed(self, session_id: str, goal: str) -> None:
        """Mark a session goal as completed."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if goal in session.goals:
                session.goals.remove(goal)
                session.completed_goals.append(goal)
    
    def end_session(self, session_id: str, satisfaction_score: Optional[float] = None) -> None:
        """End a conversation session."""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session.active = False
        
        # Store satisfaction score
        if satisfaction_score is not None:
            user_profile = self.user_profiles.get(session.user_id)
            if user_profile:
                user_profile.satisfaction_history.append(satisfaction_score)
                self.interaction_stats['satisfaction_trends'].append(satisfaction_score)
        
        # Move all turns to long-term storage
        self.conversation_history[session.user_id].extend(session.turns)
        
        # Update analytics
        self.interaction_stats['total_conversations'] += 1
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Ended session {session_id} with {len(session.turns)} turns")
    
    def _initialize_user_profile(self, user_id: str) -> None:
        """Initialize a new user profile."""
        self.user_profiles[user_id] = UserProfile(user_id=user_id)
    
    def _build_turn_context(self, session: ConversationSession, additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build context for a conversation turn."""
        context = {
            'session_context': session.session_context,
            'turn_number': len(session.turns) + 1,
            'session_duration_minutes': (datetime.now() - session.start_time).total_seconds() / 60,
            'active_goals': session.goals,
            'completed_goals': session.completed_goals
        }
        
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _extract_turn_metadata(self, user_input: str, assistant_response: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from a conversation turn."""
        return {
            'user_input_length': len(user_input),
            'assistant_response_length': len(assistant_response),
            'primary_intent': intent.get('primary_intent', 'unknown'),
            'intent_confidence': intent.get('confidence', 0.0),
            'contains_question': '?' in user_input,
            'contains_gratitude': any(word in user_input.lower() for word in ['thank', 'thanks', 'appreciate']),
            'contains_frustration': any(word in user_input.lower() for word in ['frustrated', 'angry', 'annoyed'])
        }
    
    def _update_user_profile(self, user_id: str, turn: ConversationTurn) -> None:
        """Update user profile based on conversation turn."""
        if user_id not in self.user_profiles:
            return
        
        profile = self.user_profiles[user_id]
        profile.last_interaction = turn.timestamp
        profile.total_interactions += 1
        
        # Update frequent topics
        primary_intent = turn.intent.get('primary_intent')
        if primary_intent and primary_intent not in profile.frequent_topics:
            profile.frequent_topics.append(primary_intent)
            if len(profile.frequent_topics) > 10:
                profile.frequent_topics = profile.frequent_topics[-10:]
    
    def _update_analytics(self, turn: ConversationTurn) -> None:
        """Update analytics based on conversation turn."""
        primary_intent = turn.intent.get('primary_intent', 'unknown')
        self.interaction_stats['most_common_intents'][primary_intent] += 1
    
    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.end_session(session_id)
