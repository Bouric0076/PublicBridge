import logging
import traceback
from functools import wraps
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AIAgentException(Exception):
    """Base exception for AI agent operations."""
    pass

class ModelInitializationError(AIAgentException):
    """Exception raised when model initialization fails."""
    pass

class InferenceError(AIAgentException):
    """Exception raised during model inference."""
    pass

class APIError(AIAgentException):
    """Exception raised during API calls."""
    pass

def safe_ai_operation(fallback_response: Optional[Dict[str, Any]] = None, 
                     log_errors: bool = True,
                     user_friendly_message: str = "I apologize, but I'm experiencing technical difficulties. Please try again later."):
    """
    Decorator for safe AI operations with comprehensive error handling.
    
    Args:
        fallback_response: Default response to return on error
        log_errors: Whether to log errors
        user_friendly_message: User-friendly error message
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"AI operation failed in {func.__name__}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Return user-friendly fallback response
                if fallback_response:
                    return fallback_response
                
                return {
                    'response': user_friendly_message,
                    'confidence': 0.0,
                    'intent': {'primary_intent': 'error', 'confidence': 0.0},
                    'sentiment_analysis': {'sentiment': 'neutral', 'intensity': 'low'},
                    'response_metadata': {
                        'model_used': 'error_handler',
                        'response_length': len(user_friendly_message),
                        'processing_time': 0.0,
                        'timestamp': datetime.now().isoformat(),
                        'confidence_score': 0.0,
                        'error': str(e),
                        'function': func.__name__
                    }
                }
        return wrapper
    return decorator

def safe_classification_operation(fallback_category: str = 'INFRASTRUCTURE'):
    """
    Decorator for safe classification operations.
    
    Args:
        fallback_category: Default category to return on error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Classification operation failed in {func.__name__}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                return {
                    'category': fallback_category,
                    'confidence': 0.1,
                    'reasoning': 'Classification failed due to technical error',
                    'urgency_level': 'MEDIUM',
                    'keywords_found': [],
                    'model_used': 'error_handler',
                    'processing_time': 0.0,
                    'text_length': len(args[1]) if len(args) > 1 else 0,
                    'language_detected': 'unknown',
                    'error': str(e),
                    'function': func.__name__
                }
        return wrapper
    return decorator

def safe_sentiment_operation():
    """Decorator for safe sentiment analysis operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Sentiment analysis failed in {func.__name__}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
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
                        'recommendation': 'Unable to analyze due to technical error'
                    },
                    'processing_metadata': {
                        'text_length': len(args[1]) if len(args) > 1 else 0,
                        'models_used': ['error_fallback'],
                        'processing_timestamp': datetime.now().isoformat(),
                        'error': str(e),
                        'function': func.__name__
                    }
                }
        return wrapper
    return decorator

class ErrorLogger:
    """Centralized error logging for AI operations."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self.error_counts = {}
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context information."""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'error_count': self.error_counts[error_type],
            'context': context or {},
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"AI Error: {json.dumps(error_info, indent=2)}")
        
        # Write to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(error_info) + '\n')
            except Exception as file_error:
                logger.error(f"Failed to write error to file: {file_error}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of logged errors."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': self.error_counts.copy(),
            'timestamp': datetime.now().isoformat()
        }

# Global error logger instance
error_logger = ErrorLogger()

def handle_api_error(func: Callable) -> Callable:
    """Handle API-specific errors with retry logic."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except APIError as e:
                retry_count += 1
                logger.warning(f"API error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    error_logger.log_error(e, {
                        'function': func.__name__,
                        'retry_count': retry_count,
                        'args': str(args)[:100],  # Truncate for logging
                        'kwargs': str(kwargs)[:100]
                    })
                    raise
            except Exception as e:
                error_logger.log_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                })
                raise
        
        return None
    return wrapper

def create_user_friendly_response(error: Exception, operation_type: str = "AI operation") -> Dict[str, Any]:
    """Create a user-friendly response for errors."""
    
    # Map error types to user-friendly messages
    error_messages = {
        'ModelInitializationError': "I'm currently setting up my AI capabilities. Please try again in a moment.",
        'InferenceError': "I'm having trouble processing your request right now. Please try rephrasing or try again later.",
        'APIError': "I'm experiencing connectivity issues. Please try again in a few moments.",
        'TimeoutError': "Your request is taking longer than expected. Please try again.",
        'MemoryError': "I'm currently handling high demand. Please try again shortly.",
        'ConnectionError': "I'm having trouble connecting to my services. Please check your connection and try again.",
        'ValueError': "I had trouble understanding your input. Could you please rephrase your request?",
        'KeyError': "I'm missing some information needed to process your request. Please try again.",
        'AttributeError': "I'm experiencing a technical issue. Please try again later."
    }
    
    error_type = type(error).__name__
    user_message = error_messages.get(error_type, 
        f"I apologize, but I'm experiencing technical difficulties with {operation_type}. Please try again later.")
    
    return {
        'response': user_message,
        'confidence': 0.0,
        'intent': {'primary_intent': 'error', 'confidence': 0.0},
        'sentiment_analysis': {'sentiment': 'neutral', 'intensity': 'low'},
        'response_metadata': {
            'model_used': 'error_handler',
            'response_length': len(user_message),
            'processing_time': 0.0,
            'timestamp': datetime.now().isoformat(),
            'confidence_score': 0.0,
            'error_type': error_type,
            'operation_type': operation_type
        }
    }

def monitor_performance(func: Callable) -> Callable:
    """Monitor performance and log slow operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Log slow operations
            if processing_time > 5.0:  # More than 5 seconds
                logger.warning(f"Slow operation detected: {func.__name__} took {processing_time:.2f}s")
            
            # Add performance metadata if result is a dict
            if isinstance(result, dict) and 'response_metadata' in result:
                result['response_metadata']['actual_processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Operation {func.__name__} failed after {processing_time:.2f}s: {e}")
            raise
    
    return wrapper

# Convenience function for Django views
def safe_ai_view_response(operation_func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Safe wrapper for AI operations in Django views.
    
    Args:
        operation_func: The AI operation function to call
        *args, **kwargs: Arguments to pass to the operation function
    
    Returns:
        Safe response dictionary
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        error_logger.log_error(e, {
            'operation': operation_func.__name__,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        })
        
        return create_user_friendly_response(e, operation_func.__name__)

# Health check utilities
def check_ai_agent_health(agent) -> Dict[str, Any]:
    """Check the health of an AI agent."""
    try:
        if hasattr(agent, 'health_check'):
            return agent.health_check()
        else:
            # Basic health check
            test_result = agent.generate_response("Hello") if hasattr(agent, 'generate_response') else None
            return {
                'status': 'healthy' if test_result else 'unknown',
                'agent_type': type(agent).__name__,
                'has_health_check': False,
                'test_response': test_result is not None
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'agent_type': type(agent).__name__
        }
