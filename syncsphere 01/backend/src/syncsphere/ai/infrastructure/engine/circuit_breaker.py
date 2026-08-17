import time
import logging
from typing import Dict, Tuple

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.circuit_breaker")

class CircuitBreaker:
    """
    In-memory CircuitBreaker safeguarding client services from hanging or failing
    when external model providers encounter service disruptions.
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        # State tracking per provider: name -> (state, failure_count, last_state_change)
        # States: "CLOSED", "OPEN", "HALF-OPEN"
        self._registry: Dict[str, dict] = {}

    def _get_provider_state(self, provider_name: str) -> dict:
        if provider_name not in self._registry:
            self._registry[provider_name] = {
                "state": "CLOSED",
                "failures": 0,
                "last_change": time.time()
            }
        return self._registry[provider_name]

    def can_execute(self, provider_name: str) -> bool:
        """Determines if requests can be routed to the specified provider."""
        record = self._get_provider_state(provider_name)
        state = record["state"]
        
        if state == "CLOSED":
            return True
            
        if state == "OPEN":
            # Check if cooldown has elapsed
            elapsed = time.time() - record["last_change"]
            if elapsed >= self.cooldown_seconds:
                # Transition to HALF-OPEN to test recovery
                record["state"] = "HALF-OPEN"
                record["last_change"] = time.time()
                logger.info("Circuit breaker for '%s' transitioned to HALF-OPEN.", provider_name)
                return True
            return False
            
        # HALF-OPEN permits a trial execution
        return True

    def record_success(self, provider_name: str) -> None:
        """Resets failure counts and closes the circuit on successful execution."""
        record = self._get_provider_state(provider_name)
        if record["state"] != "CLOSED":
            logger.info("Circuit breaker for '%s' transitioned back to CLOSED (recovered).", provider_name)
        record["state"] = "CLOSED"
        record["failures"] = 0
        record["last_change"] = time.time()

    def record_failure(self, provider_name: str) -> None:
        """Increments failure counts and trips the circuit if threshold is exceeded."""
        record = self._get_provider_state(provider_name)
        record["failures"] += 1
        record["last_change"] = time.time()
        
        if record["failures"] >= self.failure_threshold:
            if record["state"] != "OPEN":
                logger.warning(
                    "Circuit breaker for '%s' TRIPPED to OPEN due to %d sequential failures.",
                    provider_name,
                    record["failures"]
                )
            record["state"] = "OPEN"
