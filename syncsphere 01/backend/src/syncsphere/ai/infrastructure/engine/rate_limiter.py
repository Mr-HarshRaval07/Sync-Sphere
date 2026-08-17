import time
import logging
from typing import Dict, List
from syncsphere.ai.domain.exceptions import InferenceQuotaExceededException

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.rate_limiter")

class TenantRateLimiter:
    """
    Sliding window tenant-based rate limiter validating Requests Per Minute (RPM)
    and Tokens Per Minute (TPM) limits.
    """
    def __init__(self, default_rpm: int = 120, default_tpm: int = 100000) -> None:
        self.default_rpm = default_rpm
        self.default_tpm = default_tpm
        
        # org_id -> list of timestamps for request rates
        self._requests_log: Dict[str, List[float]] = {}
        # org_id -> list of (timestamp, tokens) for token consumption rates
        self._tokens_log: Dict[str, List[tuple]] = {}

    def check_limits(self, org_id: str, estimated_tokens: int = 0) -> None:
        """
        Validates the sliding window limits for the organization.
        Raises InferenceQuotaExceededException if thresholds are crossed.
        """
        now = time.time()
        minute_ago = now - 60.0
        
        # RPM check
        if org_id not in self._requests_log:
            self._requests_log[org_id] = []
        # filter out older than 60s
        self._requests_log[org_id] = [t for t in self._requests_log[org_id] if t > minute_ago]
        
        if len(self._requests_log[org_id]) >= self.default_rpm:
            logger.warning("Org %s exceeded Request-Per-Minute quota.", org_id)
            raise InferenceQuotaExceededException(
                org_id=org_id,
                quota_limit=float(self.default_rpm),
                current_usage=float(len(self._requests_log[org_id]))
            )
            
        # TPM check
        if org_id not in self._tokens_log:
            self._tokens_log[org_id] = []
        self._tokens_log[org_id] = [(t, val) for t, val in self._tokens_log[org_id] if t > minute_ago]
        
        current_tokens_sum = sum(val for t, val in self._tokens_log[org_id])
        if current_tokens_sum + estimated_tokens > self.default_tpm:
            logger.warning("Org %s exceeded Token-Per-Minute quota.", org_id)
            raise InferenceQuotaExceededException(
                org_id=org_id,
                quota_limit=float(self.default_tpm),
                current_usage=float(current_tokens_sum + estimated_tokens)
            )
            
        # Log this consumption
        self._requests_log[org_id].append(now)
        self._tokens_log[org_id].append((now, estimated_tokens))
