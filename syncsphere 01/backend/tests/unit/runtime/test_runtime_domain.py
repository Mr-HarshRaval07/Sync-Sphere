import pytest
from datetime import datetime
from syncsphere.shared_kernel.domain.domain_exception import ValidationException
from syncsphere.runtime.domain.value_objects import (
    ExecutionState,
    ExecutionPolicy,
    ExecutionStep,
    ExecutionCheckpoint,
    ASTNode,
    ExecutionAST
)
from syncsphere.runtime.domain.entities import ExecutionSession, ExecutionTrace, ExecutionSaga
from syncsphere.runtime.application.services.retry import RetryEngine
from syncsphere.runtime.application.services.timeout import TimeoutManager
from syncsphere.workflow.domain.value_objects import RetryPolicy, TimeoutPolicy

def test_execution_session_state_transitions():
    session = ExecutionSession(
        org_id="org_1",
        workflow_id="wf_1",
        version=1,
        status=ExecutionState.CREATED
    )
    
    # Valid transition
    session.transition_to(ExecutionState.QUEUED)
    assert session.status == ExecutionState.QUEUED
    
    session.transition_to(ExecutionState.RUNNING)
    assert session.status == ExecutionState.RUNNING
    
    # Invalid transition (RUNNING directly to CREATED)
    with pytest.raises(ValidationException) as exc:
        session.transition_to(ExecutionState.CREATED)
    assert exc.value.code == "INVALID_STATE_TRANSITION"

def test_execution_session_step_record():
    step = ExecutionStep(node_id="node_1", name="Step 1", type="tool_call")
    session = ExecutionSession(
        org_id="org_1",
        workflow_id="wf_1",
        version=1,
        status=ExecutionState.RUNNING,
        steps={"node_1": step}
    )
    
    session.record_step_completion("node_1", {"output_key": "output_val"})
    assert session.steps["node_1"].status == ExecutionState.COMPLETED
    assert session.variables["output_key"] == "output_val"
    assert session.metrics.steps_completed == 1
    
    # Invalid step completion
    with pytest.raises(ValidationException):
        session.record_step_completion("unknown_node", {})

def test_execution_trace_logging():
    trace = ExecutionTrace(org_id="org_1", session_id="session_1")
    trace.log_event("scheduling", "node_queued", {"node_id": "node_1"})
    trace.log_event("retry", "backoff_applied", {"node_id": "node_1", "attempt": 2})
    
    assert len(trace.phases["scheduling"]) == 1
    assert trace.phases["scheduling"][0]["event"] == "node_queued"
    assert len(trace.phases["retry"]) == 1
    assert trace.phases["retry"][0]["event"] == "backoff_applied"

def test_retry_engine_backoff_calculation():
    policy = RetryPolicy(max_attempts=3, backoff_factor=2.0, initial_interval_seconds=3)
    
    # Attempt 0 (first retry)
    delay_0 = RetryEngine.calculate_next_backoff(policy, 0)
    assert 3 * 0.85 <= delay_0 <= 3 * 1.15
    
    # Attempt 1
    delay_1 = RetryEngine.calculate_next_backoff(policy, 1)
    assert 6 * 0.85 <= delay_1 <= 6 * 1.15
    
    # Attempt 3 (exhausted)
    delay_ex = RetryEngine.calculate_next_backoff(policy, 3)
    assert delay_ex == -1.0

def test_timeout_manager_checks():
    policy = TimeoutPolicy(timeout_seconds=2)
    step = ExecutionStep(
        node_id="node_1",
        name="Step 1",
        type="tool_call",
        status=ExecutionState.RUNNING,
        started_at=datetime.utcnow()
    )
    session = ExecutionSession(
        org_id="org_1",
        workflow_id="wf_1",
        version=1,
        steps={"node_1": step}
    )
    
    # Not timed out yet
    assert not TimeoutManager.verify_timeout(session, "node_1", policy)
    
    # Artificially set started_at in the past
    import time
    step.started_at = datetime.fromtimestamp(datetime.utcnow().timestamp() - 5)
    assert TimeoutManager.verify_timeout(session, "node_1", policy)
