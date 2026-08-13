import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.circuit_breaker")


class CircuitBreaker:
    """
    In-memory CircuitBreaker safeguarding client services from hanging or failing
    when external model providers encounter service disruptions.

    State Transitions:
      CLOSED    -> OPEN      (after failure_threshold consecutive failures)
      OPEN      -> HALF_OPEN (after cooldown_seconds has elapsed)
      HALF_OPEN -> CLOSED    (upon a single successful request)
      HALF_OPEN -> OPEN      (upon trial request failure)
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 15.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        # State tracking per provider: name -> dict
        self._registry: Dict[str, dict] = {}

    def _get_provider_state(self, provider_name: str) -> dict:
        if provider_name not in self._registry:
            self._registry[provider_name] = {
                "state": "CLOSED",
                "failures": 0,
                "successes": 0,
                "last_change": time.time(),
                "last_failure_reason": None,
            }
        return self._registry[provider_name]

    def get_status(self, provider_name: str) -> dict:
        record = self._get_provider_state(provider_name)
        state = record["state"]
        now = time.time()
        elapsed = now - record["last_change"]
        remaining = max(0.0, self.cooldown_seconds - elapsed) if state == "OPEN" else 0.0

        return {
            "provider": provider_name,
            "state": state,
            "failure_count": record["failures"],
            "success_count": record["successes"],
            "last_failure_reason": record["last_failure_reason"] or "None",
            "remaining_cooldown_seconds": round(remaining, 2),
        }

    def can_execute(self, provider_name: str) -> bool:
        """
        Determines if requests can be routed to the specified provider.
        Automatically transitions from OPEN to HALF_OPEN after cooldown_seconds.
        """
        record = self._get_provider_state(provider_name)
        state = record["state"]
        now = time.time()
        elapsed = now - record["last_change"]
        remaining = max(0.0, self.cooldown_seconds - elapsed)

        if state == "CLOSED":
            logger.info(
                "[CIRCUIT BREAKER] Check '%s' | State: CLOSED | Failures: %d/%d | Successes: %d | Last Reason: '%s' | Remaining Cooldown: 0.0s",
                provider_name, record["failures"], self.failure_threshold, record["successes"],
                record["last_failure_reason"] or "None"
            )
            return True

        if state == "OPEN":
            if elapsed >= self.cooldown_seconds:
                # Transition OPEN -> HALF_OPEN after recovery timeout
                record["state"] = "HALF_OPEN"
                record["last_change"] = now
                logger.info(
                    "[CIRCUIT BREAKER] '%s' OPEN -> HALF_OPEN (cooldown of %.1fs elapsed). Trial request permitted.",
                    provider_name, self.cooldown_seconds
                )
                return True
            else:
                logger.warning(
                    "[CIRCUIT BREAKER] Check '%s' | State: OPEN (BLOCKED) | Failures: %d/%d | Successes: %d | Last Reason: '%s' | Remaining Cooldown: %.1fs",
                    provider_name, record["failures"], self.failure_threshold, record["successes"],
                    record["last_failure_reason"] or "None", remaining
                )
                return False

        if state == "HALF_OPEN":
            logger.info(
                "[CIRCUIT BREAKER] Check '%s' | State: HALF_OPEN (TRIAL) | Failures: %d/%d | Successes: %d | Last Reason: '%s' | Remaining Cooldown: 0.0s",
                provider_name, record["failures"], self.failure_threshold, record["successes"],
                record["last_failure_reason"] or "None"
            )
            return True

        return True

    def record_success(self, provider_name: str) -> None:
        """Resets failure counts and closes the circuit on successful execution."""
        record = self._get_provider_state(provider_name)
        old_state = record["state"]
        record["state"] = "CLOSED"
        record["failures"] = 0
        record["successes"] += 1
        record["last_change"] = time.time()

        logger.info(
            "[CIRCUIT BREAKER] SUCCESS '%s' | State: %s -> CLOSED | Failures: 0 (reset) | Successes: %d | Last Reason: '%s'",
            provider_name, old_state, record["successes"], record["last_failure_reason"] or "None"
        )

    def record_failure(self, provider_name: str, reason: Optional[str] = None) -> None:
        """Increments failure counts and trips the circuit if threshold is exceeded."""
        record = self._get_provider_state(provider_name)
        
        # CRITICAL FIX: If state is already OPEN, do not update last_change or reset cooldown!
        if record["state"] == "OPEN":
            logger.debug(
                "[CIRCUIT BREAKER] '%s' is already OPEN. Preserving cooldown timer (last_change unchanged).",
                provider_name
            )
            return

        old_state = record["state"]
        record["failures"] += 1
        record["last_change"] = time.time()
        if reason:
            record["last_failure_reason"] = str(reason)

        failures = record["failures"]
        remaining = self.cooldown_seconds

        if failures >= self.failure_threshold or old_state == "HALF_OPEN":
            record["state"] = "OPEN"
            logger.warning(
                "[CIRCUIT BREAKER] TRIPPED! '%s' | State: %s -> OPEN | Failures: %d/%d | Successes: %d | Last Reason: '%s' | Cooldown: %.1fs",
                provider_name, old_state, failures, self.failure_threshold, record["successes"],
                record["last_failure_reason"] or "None", remaining
            )
        else:
            logger.info(
                "[CIRCUIT BREAKER] FAILURE RECORDED '%s' | State: %s | Failures: %d/%d | Successes: %d | Last Reason: '%s'",
                provider_name, old_state, failures, self.failure_threshold, record["successes"],
                record["last_failure_reason"] or "None"
            )

    def reset(self, provider_name: Optional[str] = None) -> None:
        """Force resets the circuit breaker to CLOSED state."""
        if provider_name:
            if provider_name in self._registry:
                self._registry[provider_name] = {
                    "state": "CLOSED",
                    "failures": 0,
                    "successes": 0,
                    "last_change": time.time(),
                    "last_failure_reason": None,
                }
        else:
            self._registry.clear()
        logger.info("[CIRCUIT BREAKER] Reset executed for provider='%s'", provider_name or "ALL")
