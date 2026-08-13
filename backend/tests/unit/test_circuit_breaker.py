import time
import pytest
from syncsphere.ai.infrastructure.engine.circuit_breaker import CircuitBreaker


def test_circuit_breaker_state_machine_flow():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=0.2)
    provider = "openrouter"

    # Initial state must be CLOSED
    assert cb.can_execute(provider) is True
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0

    # Record 2 failures (below threshold of 3)
    cb.record_failure(provider, reason="HTTP 500 Server Error")
    cb.record_failure(provider, reason="HTTP 500 Server Error")

    # Should still be CLOSED because threshold is 3
    assert cb.can_execute(provider) is True
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 2

    # Record 3rd failure (trips to OPEN)
    cb.record_failure(provider, reason="HTTP 503 Service Unavailable")
    status = cb.get_status(provider)
    assert status["state"] == "OPEN"
    assert status["failure_count"] == 3

    # Immediately checking can_execute should return False (cooldown not elapsed)
    assert cb.can_execute(provider) is False

    # Wait for cooldown of 0.2 seconds to elapse
    time.sleep(0.25)

    # Next check should transition to HALF_OPEN and permit trial request
    assert cb.can_execute(provider) is True
    status = cb.get_status(provider)
    assert status["state"] == "HALF_OPEN"

    # Successful trial request resets state back to CLOSED
    cb.record_success(provider)
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0
    assert status["success_count"] == 1
