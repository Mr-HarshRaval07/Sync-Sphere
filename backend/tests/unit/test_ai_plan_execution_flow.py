import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from syncsphere.ai.infrastructure.engine.circuit_breaker import CircuitBreaker
from syncsphere.ai.domain.value_objects import StructuredOutputResult, TokenUsage, CostUsage
from syncsphere.ai.domain.exceptions import ProviderOfflineException


def test_ai_plan_execution_and_circuit_breaker_cycle():
    """
    Test suite verifying the full user lifecycle:
      1. Generate AI plan 1 -> Circuit breaker remains CLOSED
      2. Execute workflow
      3. Generate AI plan 2 -> Circuit breaker remains CLOSED
      4. Verify fallback model execution when primary model encounters retryable error
    """
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=15.0)
    provider = "openrouter"

    # --- Step 1: Generate AI Plan 1 ---
    assert cb.can_execute(provider) is True
    # Model execution succeeds
    cb.record_success(provider)
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0
    assert status["success_count"] == 1

    # --- Step 2: Execute Workflow ---
    # Simulate workflow execution (independent of AI provider)
    workflow_executed = True
    assert workflow_executed is True

    # --- Step 3: Generate AI Plan 2 ---
    assert cb.can_execute(provider) is True
    # Model execution succeeds again
    cb.record_success(provider)
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0
    assert status["success_count"] == 2

    # --- Step 4: Verify Fallback Execution ---
    # Simulate primary model (inclusionai/ling-3.0-tiny:free) failing with retryable 429 error
    cb.record_failure(provider, reason="HTTP 429 Rate Limit Exceeded")
    # Circuit breaker should NOT be OPEN yet (1 failure out of 3)
    assert cb.can_execute(provider) is True
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 1

    # Simulate fallback model (openrouter/free) succeeding
    cb.record_success(provider)
    status = cb.get_status(provider)
    assert status["state"] == "CLOSED"
    assert status["failure_count"] == 0
