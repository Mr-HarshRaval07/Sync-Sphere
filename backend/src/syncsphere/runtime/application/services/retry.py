import random
import logging
from datetime import datetime, timedelta
from syncsphere.workflow.domain.value_objects import RetryPolicy

logger = logging.getLogger("syncsphere.runtime.application.services.retry")

class RetryEngine:
    """Calculates backoff intervals using exponential growth and random jitter values."""
    
    @staticmethod
    def calculate_next_backoff(policy: RetryPolicy, attempt: int) -> float:
        """Returns delay seconds before the next retry attempt."""
        if attempt >= policy.max_attempts:
            return -1.0  # Retry budget exhausted
            
        interval = policy.initial_interval_seconds * (policy.backoff_factor ** attempt)
        
        # Apply random Jitter (+/- 15% deviation) to avoid herd behavior
        jitter = random.uniform(0.85, 1.15)
        backoff_seconds = max(interval * jitter, 1.0)
        
        logger.info(
            "Retry attempt %d calculated backoff delay: %.2f seconds (base: %.2f)",
            attempt + 1, backoff_seconds, interval
        )
        return backoff_seconds
