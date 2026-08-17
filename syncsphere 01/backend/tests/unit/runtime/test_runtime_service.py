import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from syncsphere.shared_kernel.types.result import Result
from syncsphere.core.dependency_injection.container import container
from syncsphere.runtime.application.commands import (
    StartExecutionCommand,
    PauseExecutionCommand,
    ResumeExecutionCommand,
    CancelExecutionCommand,
    ApproveExecutionCommand,
    RetryExecutionCommand
)
from syncsphere.runtime.domain.value_objects import ExecutionState, ExecutionPolicy
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion
from syncsphere.workflow.domain.value_objects import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowStepType,
    ExecutionNode,
    ExecutionPlan,
    RetryPolicy,
    CompensationPolicy,
    WorkflowEdge
)

@pytest.mark.asyncio
async def test_execution_engine_lifecycle_commands():
    org_id = "org_test"
    
    # 1. Setup mock workflow and version aggregates in repo
    wf = Workflow(org_id=org_id, name="Test Lifecycle", description="")
    wf.active_version = 1
    await container.workflow_repo.save(wf)
    
    # Prepare Execution Plan: Step A -> Step B
    nodes = {
        "step_a": WorkflowNode(id="step_a", name="Step A", type=WorkflowStepType.TOOL_CALL),
        "step_b": WorkflowNode(id="step_b", name="Step B", type=WorkflowStepType.TOOL_CALL)
    }
    wf.graph.nodes = nodes
    await container.workflow_repo.save(wf)
    
    plan_nodes = {
        "step_a": ExecutionNode(node_id="step_a", name="Step A", type=WorkflowStepType.TOOL_CALL, dependencies=[]),
        "step_b": ExecutionNode(node_id="step_b", name="Step B", type=WorkflowStepType.TOOL_CALL, dependencies=["step_a"])
    }
    plan = ExecutionPlan(
        workflow_id=wf.id,
        version=1,
        topological_order=["step_a", "step_b"],
        execution_nodes=plan_nodes
    )
    
    version = WorkflowVersion(
        workflow_id=wf.id,
        version=1,
        description="Version 1",
        graph=wf.graph
    )
    await container.workflow_version_repo.save(version)
    
    # 2. Mock StepExecutor execution output
    async def mock_execute(session, node_id):
        if node_id == "step_a":
            return {"outputs": {"var_a": "val_a"}, "status": "completed"}
        elif node_id == "step_b":
            return {"outputs": {"var_b": "val_b"}, "status": "completed"}
        return {"outputs": {}, "status": "completed"}
        
    container.step_executor.execute = mock_execute
    
    # 3. Start Execution
    cmd_start = StartExecutionCommand(
        org_id=org_id,
        workflow_id=wf.id,
        inputs={"initial_var": "val_init"}
    )
    
    res_start = await container.execution_engine.start_execution(cmd_start)
    assert res_start.is_ok
    session = res_start.value()
    assert session.status in (ExecutionState.QUEUED, ExecutionState.RUNNING)
    
    # Wait briefly for background execution pipeline task to progress
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.COMPLETED:
            break
        await asyncio.sleep(0.01)
    
    # Reload session from repository to inspect state updates
    session = await container.execution_session_repo.get_by_id(session.id)
    assert session.status == ExecutionState.COMPLETED
    assert session.variables["var_a"] == "val_a"
    assert session.variables["var_b"] == "val_b"
    assert session.steps["step_a"].status == ExecutionState.COMPLETED
    assert session.steps["step_b"].status == ExecutionState.COMPLETED

@pytest.mark.asyncio
async def test_execution_engine_pause_and_resume():
    org_id = "org_test"
    wf = Workflow(org_id=org_id, name="Test Pause", description="")
    wf.active_version = 1
    await container.workflow_repo.save(wf)
    
    plan_nodes = {
        "step_delay": ExecutionNode(node_id="step_delay", name="Delay", type=WorkflowStepType.DELAY, dependencies=[])
    }
    wf.graph.nodes = {"step_delay": WorkflowNode(id="step_delay", name="Delay", type=WorkflowStepType.DELAY, delay_seconds=2)}
    await container.workflow_repo.save(wf)
    
    plan = ExecutionPlan(workflow_id=wf.id, version=1, topological_order=["step_delay"], execution_nodes=plan_nodes)
    version = WorkflowVersion(workflow_id=wf.id, version=1, description="v1", graph=wf.graph)
    await container.workflow_version_repo.save(version)
    
    # Start execution
    cmd_start = StartExecutionCommand(org_id=org_id, workflow_id=wf.id)
    res_start = await container.execution_engine.start_execution(cmd_start)
    assert res_start.is_ok
    session = res_start.value()
    
    # Pause execution
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.RUNNING:
            break
        await asyncio.sleep(0.01)
    res_pause = await container.execution_engine.pause_execution(PauseExecutionCommand(org_id=org_id, session_id=session.id))
    assert res_pause.is_ok
    
    session = await container.execution_session_repo.get_by_id(session.id)
    assert session.status == ExecutionState.PAUSED
    
    # Resume execution
    res_resume = await container.execution_engine.resume_execution(ResumeExecutionCommand(org_id=org_id, session_id=session.id))
    assert res_resume.is_ok
    
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status in (ExecutionState.RUNNING, ExecutionState.COMPLETED):
            break
        await asyncio.sleep(0.01)
    session = await container.execution_session_repo.get_by_id(session.id)
    assert session.status in (ExecutionState.RUNNING, ExecutionState.COMPLETED)

@pytest.mark.asyncio
async def test_execution_engine_approval_gate():
    org_id = "org_test"
    wf = Workflow(org_id=org_id, name="Test Approval", description="")
    wf.active_version = 1
    await container.workflow_repo.save(wf)
    
    wf.graph.nodes = {
        "step_approval": WorkflowNode(id="step_approval", name="Gate", type=WorkflowStepType.APPROVAL)
    }
    await container.workflow_repo.save(wf)
    
    plan_nodes = {
        "step_approval": ExecutionNode(node_id="step_approval", name="Gate", type=WorkflowStepType.APPROVAL, dependencies=[])
    }
    plan = ExecutionPlan(workflow_id=wf.id, version=1, topological_order=["step_approval"], execution_nodes=plan_nodes)
    version = WorkflowVersion(workflow_id=wf.id, version=1, description="v1", graph=wf.graph)
    await container.workflow_version_repo.save(version)
    
    # Start Execution
    cmd_start = StartExecutionCommand(org_id=org_id, workflow_id=wf.id)
    res_start = await container.execution_engine.start_execution(cmd_start)
    assert res_start.is_ok
    session = res_start.value()
    
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.AWAITING_APPROVAL:
            break
        await asyncio.sleep(0.01)
    
    # Session must be paused awaiting approval
    session = await container.execution_session_repo.get_by_id(session.id)
    assert session.status == ExecutionState.AWAITING_APPROVAL
    assert session.steps["step_approval"].status == ExecutionState.AWAITING_APPROVAL
    
    # Approve
    res_app = await container.execution_engine.approve_execution(
        ApproveExecutionCommand(org_id=org_id, session_id=session.id, node_id="step_approval", approved=True)
    )
    assert res_app.is_ok
    
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.COMPLETED:
            break
        await asyncio.sleep(0.01)
    session = await container.execution_session_repo.get_by_id(session.id)
    assert session.status == ExecutionState.COMPLETED
    assert session.steps["step_approval"].status == ExecutionState.COMPLETED

@pytest.mark.asyncio
async def test_execution_engine_retry_fallback():
    org_id = "org_test"
    wf = Workflow(org_id=org_id, name="Test Retry", description="")
    wf.active_version = 1
    await container.workflow_repo.save(wf)
    
    # Step has a RetryPolicy
    wf.graph.nodes = {
        "step_fail": WorkflowNode(
            id="step_fail",
            name="Fail Step",
            type=WorkflowStepType.TOOL_CALL,
            retry_policy=RetryPolicy(max_attempts=2, backoff_factor=1.0, initial_interval_seconds=1)
        )
    }
    await container.workflow_repo.save(wf)
    
    plan_nodes = {
        "step_fail": ExecutionNode(node_id="step_fail", name="Fail Step", type=WorkflowStepType.TOOL_CALL, dependencies=[])
    }
    plan = ExecutionPlan(workflow_id=wf.id, version=1, topological_order=["step_fail"], execution_nodes=plan_nodes)
    version = WorkflowVersion(workflow_id=wf.id, version=1, description="v1", graph=wf.graph)
    await container.workflow_version_repo.save(version)
    
    # Step execution mock always throws an error
    async def mock_execute_fail(session, node_id):
        raise ValueError("Simulated network outage.")
    container.step_executor.execute = mock_execute_fail
    
    cmd_start = StartExecutionCommand(org_id=org_id, workflow_id=wf.id)
    res_start = await container.execution_engine.start_execution(cmd_start)
    assert res_start.is_ok
    session = res_start.value()
    
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.RETRYING:
            break
        await asyncio.sleep(0.01)
    session = await container.execution_session_repo.get_by_id(session.id)
    
    # Should be in RETRYING state
    assert session.status == ExecutionState.RETRYING
    assert session.steps["step_fail"].status == ExecutionState.RETRYING
    assert session.steps["step_fail"].retries_attempted == 1

    # Clean up background retry task by cancelling the session
    await container.execution_engine.cancel_execution(CancelExecutionCommand(org_id=org_id, session_id=session.id))

@pytest.mark.asyncio
async def test_execution_saga_rollback_compensation():
    org_id = "org_test"
    wf = Workflow(org_id=org_id, name="Test Saga", description="")
    wf.active_version = 1
    await container.workflow_repo.save(wf)
    
    # Set step_a as completed, step_b fails. step_a has a compensation step: step_a_comp
    wf.graph.nodes = {
        "step_a": WorkflowNode(
            id="step_a",
            name="Step A",
            type=WorkflowStepType.TOOL_CALL,
            compensation_policy=CompensationPolicy(compensation_node_id="step_a_comp")
        ),
        "step_b": WorkflowNode(
            id="step_b",
            name="Step B",
            type=WorkflowStepType.TOOL_CALL,
            retry_policy=RetryPolicy(max_attempts=0)
        ),
        "step_a_comp": WorkflowNode(
            id="step_a_comp",
            name="Compensate Step A",
            type=WorkflowStepType.TOOL_CALL
        )
    }
    wf.graph.edges = [
        WorkflowEdge(source_node_id="step_a", target_node_id="step_b")
    ]
    await container.workflow_repo.save(wf)
    
    plan_nodes = {
        "step_a": ExecutionNode(node_id="step_a", name="Step A", type=WorkflowStepType.TOOL_CALL, dependencies=[]),
        "step_b": ExecutionNode(node_id="step_b", name="Step B", type=WorkflowStepType.TOOL_CALL, dependencies=["step_a"]),
        "step_a_comp": ExecutionNode(node_id="step_a_comp", name="Compensate Step A", type=WorkflowStepType.TOOL_CALL, dependencies=[])
    }
    plan = ExecutionPlan(
        workflow_id=wf.id,
        version=1,
        topological_order=["step_a", "step_b"], # topological order does not run comp step during normal execution
        execution_nodes=plan_nodes
    )
    version = WorkflowVersion(workflow_id=wf.id, version=1, description="v1", graph=wf.graph)
    await container.workflow_version_repo.save(version)
    
    # step_a passes, step_b fails
    async def mock_execute(session, node_id):
        if node_id == "step_a":
            return {"outputs": {"done_a": True}, "status": "completed"}
        elif node_id == "step_b":
            raise ValueError("Failure triggers saga rollback.")
        elif node_id == "step_a_comp":
            return {"outputs": {"compensated": True}, "status": "completed"}
        return {"outputs": {}, "status": "completed"}
        
    container.step_executor.execute = mock_execute
    
    cmd_start = StartExecutionCommand(org_id=org_id, workflow_id=wf.id)
    res_start = await container.execution_engine.start_execution(cmd_start)
    assert res_start.is_ok
    session = res_start.value()
    
    for _ in range(250):
        session = await container.execution_session_repo.get_by_id(session.id)
        if session.status == ExecutionState.COMPLETED:
            break
        await asyncio.sleep(0.01)
    session = await container.execution_session_repo.get_by_id(session.id)
    
    # Should end in COMPLETED because Saga compensation completed successfully (SagaCoordinator completes session)
    if session.status != ExecutionState.COMPLETED:
        print(f"\nSaga test failed! status={session.status}, error_message={session.error_message}")
        for nid, step in session.steps.items():
            print(f"Step {nid}: status={step.status}, error={step.error}")
    assert session.status == ExecutionState.COMPLETED
    assert session.steps["step_a_comp"].status == ExecutionState.COMPLETED
    assert session.steps["step_b"].status == ExecutionState.FAILED
