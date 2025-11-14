from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

class ChatAnalyticsTracker:
    def __init__(self):
        self.metrics = defaultdict(int)
        self.last_interaction: Optional[Dict[str, Any]] = None

    def record_interaction(self, user_id: Optional[int], intent: Optional[str], confidence: float, response_length: int, error: bool):
        self.metrics['total'] += 1
        if error:
            self.metrics['errors'] += 1
        if intent:
            self.metrics[f"intent_{intent}"] += 1
        self.metrics['response_chars'] += response_length
        self.metrics['confidence_sum'] += confidence
        self.last_interaction = {
            'user_id': user_id,
            'intent': intent,
            'confidence': confidence,
            'response_length': response_length,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }

    def snapshot(self) -> Dict[str, Any]:
        total = max(self.metrics['total'], 1)
        avg_conf = self.metrics['confidence_sum'] / total
        avg_len = self.metrics['response_chars'] / total
        return {
            'total_interactions': self.metrics['total'],
            'errors': self.metrics['errors'],
            'average_confidence': avg_conf,
            'average_response_length': avg_len,
            'last_interaction': self.last_interaction
        }
