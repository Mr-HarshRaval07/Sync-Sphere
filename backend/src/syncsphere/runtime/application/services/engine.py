import logging
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import ConflictException, EntityNotFoundException, ValidationException
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.entities.trace import ExecutionTrace
from syncsphere.runtime.domain.value_objects import (
    ExecutionState,
    ExecutionPolicy,
    ExecutionStep,
    ExecutionCheckpoint,
    ASTNode,
    ExecutionAST
)
from syncsphere.runtime.domain.repositories import ExecutionSessionRepository, ExecutionTraceRepository
from syncsphere.runtime.domain.exceptions import ExecutionSessionNotFoundException
from syncsphere.runtime.domain.events import (
    ExecutionStarted,
    ExecutionPaused,
    ExecutionResumed,
    ExecutionCompleted,
    ExecutionFailed,
    ExecutionCancelled,
    ApprovalRequested,
    ApprovalReceived,
    CheckpointCreated
)
from syncsphere.runtime.application.commands import (
    StartExecutionCommand,
    PauseExecutionCommand,
    ResumeExecutionCommand,
    CancelExecutionCommand,
    RetryExecutionCommand,
    ApproveExecutionCommand
)
from syncsphere.runtime.application.pipeline.base import ExecutionPipeline
from syncsphere.runtime.application.services.scheduler import ExecutionScheduler
from syncsphere.runtime.application.services.resource import ResourceManager
from syncsphere.runtime.application.services.approval import ApprovalCoordinator

from syncsphere.workflow.domain.repositories.workflow_repository import WorkflowRepository
from syncsphere.workflow.domain.repositories.workflow_version_repository import WorkflowVersionRepository
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.workflow.domain.value_objects import WorkflowStepType, ExecutionPlan
from syncsphere.connectors.application.services.connector_service import ConnectorApplicationService
from syncsphere.core.events.interfaces import EventPublisher

logger = logging.getLogger("syncsphere.runtime.application.services.engine")

class StepExecutor:
    """Evaluates and executes individual workflow nodes according to node type (tools, delays, conditions)."""
    
    def __init__(self, connector_service: ConnectorApplicationService) -> None:
        self.connector_service = connector_service

    async def execute(self, session: ExecutionSession, node_id: str) -> Dict[str, Any]:
        """Resolves inputs and executes dynamic operations based on step configuration."""
        # Find step meta configuration in ExecutionAST
        if not session.execution_ast or node_id not in session.execution_ast.nodes:
            raise ValueError(f"Node '{node_id}' configuration not found in ExecutionAST.")
            
        step = session.steps.get(node_id)
        if not step:
            raise ValueError(f"Step '{node_id}' not initialized in session.")
            
        step.status = ExecutionState.RUNNING
        step.started_at = datetime.utcnow()
        session.record_timeline_event(f"Step {node_id} execution started")
        
        # We need the full WorkflowNode specs to parse input bindings.
        # Since WorkflowNode lives inside Workflow aggregate, we resolve it dynamically.
        # However, for testing or mock purposes, we can fallback gracefully.
        workflow_repo = None
        from syncsphere.core.dependency_injection.container import container
        try:
            workflow_repo = container.workflow_repo
        except Exception:
            pass
            
        workflow = None
        if workflow_repo:
            workflow = await workflow_repo.get_by_id(session.workflow_id)
            
        node = None
        if workflow and node_id in workflow.graph.nodes:
            node = workflow.graph.nodes[node_id]
            
        # 1. Resolve arguments mapping
        arguments = {}
        if node and node.tool_invocation:
            arguments.update(node.tool_invocation.arguments_map)
            
        # Resolve Input Bindings
        if node:
            for binding in node.input_bindings:
                source_val = None
                # Check source step output
                source_step = session.steps.get(binding.source_node_id)
                if source_step and binding.source_field in source_step.outputs:
                    source_val = source_step.outputs[binding.source_field]
                elif binding.source_field in session.variables:
                    source_val = session.variables[binding.source_field]
                    
                arguments[binding.target_field] = source_val

        # 2. Route Execution based on Node Type
        node_type = node.type if node else step.type
        
        if node_type == "delay" or node_type == WorkflowStepType.DELAY:
            delay = node.delay_seconds if node else 1
            logger.info("Step '%s' delay execution: sleeping for %d seconds", node_id, delay)
            await asyncio.sleep(delay)
            return {"outputs": {}, "status": "completed"}
            
        elif node_type == "condition" or node_type == WorkflowStepType.CONDITION:
            if not node or not node.condition:
                return {"outputs": {"result": True}, "status": "completed"}
                
            cond = node.condition
            left = session.variables.get(cond.left_operand, cond.left_operand)
            right = cond.right_operand
            op = cond.operator
            
            result = False
            if op == "EQUAL":
                result = (str(left) == str(right))
            elif op == "NOT_EQUAL":
                result = (str(left) != str(right))
            elif op == "CONTAINS":
                result = (str(right) in str(left))
            elif op == "GREATER_THAN":
                try:
                    result = (float(left) > float(right))
                except Exception:
                    result = False
            elif op == "LESS_THAN":
                try:
                    result = (float(left) < float(right))
                except Exception:
                    result = False
                    
            logger.info("Step '%s' condition evaluated: %s (left: %s, right: %s)", node_id, result, left, right)
            return {"outputs": {"result": result}, "status": "completed"}
            
        elif node_type == "approval" or node_type == WorkflowStepType.APPROVAL:
            # Trigger manual approval pause
            await ApprovalCoordinator.request_approval(session, node_id)
            return {"outputs": {}, "status": "awaiting_approval"}
            
        elif node_type == "transform" or node_type == WorkflowStepType.TRANSFORM:
            # Simple inputs mapping copy
            return {"outputs": arguments, "status": "completed"}
            
        else:
            # Default Tool Call Execution
            if not node or not node.tool_invocation:
                # Return dummy mock payload for default/test cases
                return {"outputs": {"result": "success"}, "status": "completed"}
                
            tool_inv = node.tool_invocation
            connector_id = tool_inv.connector_binding.connector_id
            tool_name = tool_inv.tool_name
            
            logger.info("Executing connector tool '%s' via connector '%s'", tool_name, connector_id)
            res = await self.connector_service.execute_tool(
                org_id=session.org_id,
                connector_id=connector_id,
                tool_name=tool_name,
                arguments=arguments
            )
            if res.is_fail:
                raise res.error()
                
            tool_res = res.value()
            outputs = {}
            for block in tool_res.content:
                if block.get("type") == "text":
                    text = block.get("text", "")
                    outputs["raw_text"] = text
                    try:
                        import json
                        parsed = json.loads(text)
                        if isinstance(parsed, dict):
                            outputs.update(parsed)
                    except Exception:
                        pass
                        
            return {"outputs": outputs, "status": "completed"}

class ExecutionEngine:
    """Coordinates execution session setups, commands triggers, and background pipeline loops."""
    
    def __init__(
        self,
        session_repo: ExecutionSessionRepository,
        trace_repo: ExecutionTraceRepository,
        workflow_repo: WorkflowRepository,
        version_repo: WorkflowVersionRepository,
        resource_manager: ResourceManager,
        pipeline: ExecutionPipeline,
        event_bus: EventPublisher
    ) -> None:
        self.session_repo = session_repo
        self.trace_repo = trace_repo
        self.workflow_repo = workflow_repo
        self.version_repo = version_repo
        self.resource_manager = resource_manager
        self.pipeline = pipeline
        self.event_bus = event_bus

    async def start_execution(self, cmd: StartExecutionCommand) -> Result[ExecutionSession, Exception]:
        """Spawns an execution session, builds the ExecutionAST and starts pipeline runner tasks."""
        # 1. Verify workflow version exists
        workflow = await self.workflow_repo.get_by_id(cmd.workflow_id)
        if not workflow or workflow.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Workflow not found."))
            
        version_num = cmd.version or workflow.active_version
        if not version_num:
            # Workflow exists but has never been versioned (created but not yet saved with nodes).
            # Auto-create a draft version snapshot from the live graph so execution can proceed,
            # identical to the behaviour of update_workflow -> save_draft().
            draft_version = workflow.save_draft(version_description="Auto-snapshot for execution")
            await self.version_repo.save(draft_version)
            await self.workflow_repo.save(workflow)
            version_num = workflow.active_version
            version = draft_version
        else:
            version = await self.version_repo.get_by_version(cmd.workflow_id, version_num)
            if not version:
                return Result.fail(EntityNotFoundException("VERSION_NOT_FOUND", "Workflow version not found."))
            
        # 2. Build session and compile ExecutionAST
        session_id = str(uuid.uuid4())
        
        # Compile execution plan dynamically using version's graph structure
        from syncsphere.workflow.infrastructure.dag.compiler import WorkflowCompiler as SharedCompiler
        # Construct temporary workflow wrapper to feed DAG compiler
        temp_wf = Workflow(
            org_id=cmd.org_id,
            name=workflow.name,
            description=workflow.description,
            variables=version.variables,
            id=workflow.id
        )
        temp_wf.graph = version.graph
        execution_plan = SharedCompiler.compile(temp_wf)
        
        # Build initial step definitions
        steps = {}
        for node_id, node in execution_plan.execution_nodes.items():
            steps[node_id] = ExecutionStep(
                node_id=node_id,
                name=node.name,
                type=node.type.value
            )
            
        ast = ExecutionScheduler.build_ast(execution_plan)
        
        session = ExecutionSession(
            org_id=cmd.org_id,
            workflow_id=cmd.workflow_id,
            version=version_num,
            status=ExecutionState.CREATED,
            policy=ExecutionPolicy(cmd.policy),
            variables=cmd.inputs.copy(),
            steps=steps,
            execution_ast=ast,
            id=session_id
        )
        
        trace = ExecutionTrace(
            org_id=cmd.org_id,
            session_id=session_id,
            id=str(uuid.uuid4())
        )
        
        # 3. Transition to QUEUED and save
        session.start()
        await self.session_repo.save(session)
        await self.trace_repo.save(trace)
        
        # Publish Event
        corr_id = cmd.correlation_id or str(uuid.uuid4())
        if self.event_bus:

            await self.event_bus.publish(ExecutionStarted(correlation_id=corr_id, session_id=session_id, org_id=cmd.org_id))
        
        # 4. Trigger background runner pipeline task
        asyncio.create_task(self._run_pipeline_task(session, trace, corr_id))
        
        return Result.ok(session)

    async def pause_execution(self, cmd: PauseExecutionCommand) -> Result[bool, Exception]:
        """Pauses a running execution session."""
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(ExecutionSessionNotFoundException(cmd.session_id))
            
        try:
            session.pause()
            await self.session_repo.save(session)
            if self.event_bus:

                await self.event_bus.publish(ExecutionPaused(correlation_id=cmd.correlation_id or str(uuid.uuid4()), session_id=session.id, org_id=cmd.org_id))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def resume_execution(self, cmd: ResumeExecutionCommand) -> Result[bool, Exception]:
        """Resumes a paused execution session, launching background pipeline tasks."""
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(ExecutionSessionNotFoundException(cmd.session_id))
            
        trace = await self.trace_repo.get_by_session(session.id)
        if not trace:
            trace = ExecutionTrace(org_id=cmd.org_id, session_id=session.id, id=str(uuid.uuid4()))
            
        try:
            session.resume()
            await self.session_repo.save(session)
            
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            if self.event_bus:

                await self.event_bus.publish(ExecutionResumed(correlation_id=corr_id, session_id=session.id, org_id=cmd.org_id))
            
            # Start background pipeline loop
            asyncio.create_task(self._run_pipeline_task(session, trace, corr_id))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def cancel_execution(self, cmd: CancelExecutionCommand) -> Result[bool, Exception]:
        """Cancels a running execution session."""
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(ExecutionSessionNotFoundException(cmd.session_id))
            
        try:
            session.cancel()
            await self.session_repo.save(session)
            if self.event_bus:

                await self.event_bus.publish(ExecutionCancelled(correlation_id=cmd.correlation_id or str(uuid.uuid4()), session_id=session.id, org_id=cmd.org_id))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def retry_execution(self, cmd: RetryExecutionCommand) -> Result[bool, Exception]:
        """Resets failed steps and attempts execution retry."""
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(ExecutionSessionNotFoundException(cmd.session_id))
            
        # Reset any failed nodes back to CREATED
        for step in session.steps.values():
            if step.status == ExecutionState.FAILED:
                step.status = ExecutionState.CREATED
                step.error = None
                
        trace = await self.trace_repo.get_by_session(session.id)
        if not trace:
            trace = ExecutionTrace(org_id=cmd.org_id, session_id=session.id, id=str(uuid.uuid4()))
            
        try:
            session.status = ExecutionState.RUNNING
            await self.session_repo.save(session)
            
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            asyncio.create_task(self._run_pipeline_task(session, trace, corr_id))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def approve_execution(self, cmd: ApproveExecutionCommand) -> Result[bool, Exception]:
        """Submits human approval decision and resumes pipeline execution if approved."""
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(ExecutionSessionNotFoundException(cmd.session_id))
            
        trace = await self.trace_repo.get_by_session(session.id)
        if not trace:
            trace = ExecutionTrace(org_id=cmd.org_id, session_id=session.id, id=str(uuid.uuid4()))
            
        try:
            await ApprovalCoordinator.handle_approval_response(session, cmd.node_id, cmd.approved)
            await self.session_repo.save(session)
            
            corr_id = cmd.correlation_id or str(uuid.uuid4())
            if self.event_bus:

                await self.event_bus.publish(ApprovalReceived(
                correlation_id=corr_id,
                session_id=session.id,
                node_id=cmd.node_id,
                approved=cmd.approved,
                org_id=cmd.org_id
            ))
            
            # If approved, resume the pipeline task!
            if cmd.approved:
                asyncio.create_task(self._run_pipeline_task(session, trace, corr_id))
            return Result.ok(True)
        except Exception as e:
            return Result.fail(e)

    async def _run_pipeline_task(self, session: ExecutionSession, trace: ExecutionTrace, correlation_id: str) -> None:
        """Background task running the execution pipeline loop to completion."""
        # Claims concurrency resource slot
        has_slot = await self.resource_manager.acquire_slot(session.org_id)
        if not has_slot:
            logger.error("Unable to start execution session '%s' due to concurrency capacity limits.", session.id)
            session.fail("Throttled due to resource concurrency limits.")
            await self.session_repo.save(session)
            if self.event_bus:

                await self.event_bus.publish(ExecutionFailed(
                correlation_id=correlation_id,
                session_id=session.id,
                error_message="Resource limits exceeded.",
                org_id=session.org_id
            ))
            return
            
        try:
            await self.pipeline.execute(session, trace)
        except Exception as e:
            logger.exception("ExecutionPipeline threw unhandled exception for session %s", session.id)
            session.fail(str(e))
            await self.session_repo.save(session)
            if self.event_bus:

                await self.event_bus.publish(ExecutionFailed(
                correlation_id=correlation_id,
                session_id=session.id,
                error_message=str(e),
                org_id=session.org_id
            ))
        finally:
            await self.resource_manager.release_slot(session.org_id)
