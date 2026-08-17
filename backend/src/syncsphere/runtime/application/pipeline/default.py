import time
import logging
import asyncio
import uuid
from typing import Dict, Any, List
from datetime import datetime

from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.entities.trace import ExecutionTrace
from syncsphere.runtime.domain.value_objects import (
    ExecutionState,
    ExecutionCheckpoint,
    ExecutionStep
)
from syncsphere.runtime.domain.repositories import ExecutionSessionRepository, ExecutionTraceRepository
from syncsphere.runtime.application.pipeline.base import ExecutionPipeline
from syncsphere.runtime.application.services.scheduler import DependencyResolver, ExecutionScheduler
from syncsphere.runtime.application.services.retry import RetryEngine
from syncsphere.runtime.application.services.saga import SagaCoordinator
from syncsphere.runtime.application.services.timeout import TimeoutManager
from syncsphere.runtime.application.strategies.worker import ExecutionDispatcher
from syncsphere.runtime.application.services.engine import StepExecutor

from syncsphere.workflow.domain.repositories.workflow_repository import WorkflowRepository
from syncsphere.core.events.interfaces import EventPublisher
from syncsphere.runtime.domain.events import (
    CheckpointCreated,
    ExecutionCompleted,
    ExecutionFailed,
    ExecutionRetried,
    ApprovalRequested
)

logger = logging.getLogger("syncsphere.runtime.application.pipeline.default")

class DefaultExecutionPipeline(ExecutionPipeline):
    """
    Orchestrates the lifecycle stages of ExecutionSession execution:
    Queue -> Dependency Resolution -> Scheduling -> Dispatch -> Execution -> Checkpoint -> Metrics -> Completion
    """
    
    def __init__(
        self,
        session_repo: ExecutionSessionRepository,
        trace_repo: ExecutionTraceRepository,
        workflow_repo: WorkflowRepository,
        dispatcher: ExecutionDispatcher,
        step_executor: StepExecutor,
        event_bus: EventPublisher
    ) -> None:
        self.session_repo = session_repo
        self.trace_repo = trace_repo
        self.workflow_repo = workflow_repo
        self.dispatcher = dispatcher
        self.step_executor = step_executor
        self.event_bus = event_bus

    async def execute(self, session: ExecutionSession, trace: ExecutionTrace) -> None:
        start_time = time.perf_counter()
        
        # 1. Queue Stage
        trace.log_event("scheduling", "session_queued", {"session_id": session.id})
        session.transition_to(ExecutionState.RUNNING)
        await self.session_repo.save(session)
        
        trace.log_event("dispatch", "session_dispatched_to_workers", {"policy": session.policy.value})
        
        workflow = await self.workflow_repo.get_by_id(session.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{session.workflow_id}' not found.")
            
        ast = session.execution_ast
        if not ast:
            raise ValueError("ExecutionAST not compiled for session.")
            
        # We run the scheduling execution loop
        active_futures = {} # node_id -> Task
        
        while session.status == ExecutionState.RUNNING:
            # Check if session has been cancelled or paused externally in the repository
            fresh_session = await self.session_repo.get_by_id(session.id)
            if fresh_session and fresh_session.status != ExecutionState.RUNNING:
                logger.info("Execution loop detected external state change for session %s: %s", session.id, fresh_session.status)
                session.status = fresh_session.status
                break
                
            # 2. Dependency Resolution Stage
            ready_ids = DependencyResolver.resolve_ready_nodes(session, ast)
            
            # 3. Scheduling Stage
            scheduled_ids = ExecutionScheduler.filter_by_policy(ready_ids, session.policy)
            
            # If no nodes are ready and no active futures are running, check if execution is completed
            if not scheduled_ids and not active_futures:
                all_done = all(step.status == ExecutionState.COMPLETED for step in session.steps.values())
                if all_done:
                    session.complete()
                else:
                    # Stalled or circular dependency fail
                    session.fail("Execution stalled: unresolvable dependencies in execution plan.")
                break
                
            # 4. Dispatch & 5. Execution Stages
            strategy = self.dispatcher.select_strategy(session.policy.value)
            
            # Start execution for scheduled nodes
            for node_id in scheduled_ids:
                step = session.steps.get(node_id)
                if not step:
                    # Default dynamic initialization
                    step = ExecutionStep(
                        node_id=node_id,
                        name=ast.nodes[node_id].name,
                        type=ast.nodes[node_id].type
                    )
                    session.steps[node_id] = step
                    
                step.status = ExecutionState.QUEUED
                trace.log_event("dispatch", "dispatch_node_to_worker", {"node_id": node_id})
                
                # Trigger checkpoint at step start
                await self._create_checkpoint(session, trace)
                
                # Execute using worker strategy
                coro = strategy.execute_node(session, node_id, self.step_executor)
                task = asyncio.create_task(coro)
                active_futures[node_id] = task
                
            # Wait for any task to finish
            if active_futures:
                done, _ = await asyncio.wait(active_futures.values(), return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    # Find completed node ID
                    node_id = None
                    for nid, t in active_futures.items():
                        if t == task:
                            node_id = nid
                            break
                            
                    if not node_id:
                        continue
                        
                    del active_futures[node_id]
                    
                    try:
                        res = task.result()
                        status = res.get("status", "completed")
                        
                        if status == "awaiting_approval":
                            trace.log_event("approval", "approval_requested", {"node_id": node_id})
                            await self.event_bus.publish(ApprovalRequested(
                                correlation_id=str(uuid.uuid4()),
                                session_id=session.id,
                                node_id=node_id,
                                approver_role_id="approver",
                                org_id=session.org_id
                            ))
                            # Approvals pause execution
                            await self.session_repo.save(session)
                            return
                            
                        else:
                            # Step COMPLETED successfully
                            session.record_step_completion(node_id, res.get("outputs", {}))
                            trace.log_event("node_execution", "node_completed", {"node_id": node_id, "outputs": res.get("outputs", {})})
                            
                    except Exception as e:
                        # Step FAILED
                        logger.error("Step execution failed: %s", e)
                        session.record_step_failure(node_id, str(e))
                        trace.log_event("node_execution", "node_failed", {"node_id": node_id, "error": str(e)})
                        
                        # Check retry policy
                        node_meta = workflow.graph.nodes.get(node_id)
                        retry_policy = node_meta.retry_policy if node_meta else None
                        
                        step = session.steps.get(node_id)
                        attempts = step.retries_attempted if step else 0
                        
                        if retry_policy and attempts < retry_policy.max_attempts:
                            backoff = RetryEngine.calculate_next_backoff(retry_policy, attempts)
                            if step:
                                step.retries_attempted = attempts + 1
                                step.status = ExecutionState.RETRYING
                            
                            session.transition_to(ExecutionState.RETRYING)
                            trace.log_event("retry", "retry_scheduled", {"node_id": node_id, "attempt": attempts + 1, "delay_seconds": backoff})
                            await self.event_bus.publish(ExecutionRetried(
                                correlation_id=str(uuid.uuid4()),
                                session_id=session.id,
                                node_id=node_id,
                                attempt=attempts + 1,
                                org_id=session.org_id
                            ))
                            
                            await self.session_repo.save(session)
                            
                            # Asynchronously schedule retry sleep
                            asyncio.create_task(self._delay_retry(session, trace, node_id, backoff))
                            return
                        else:
                            # Compensation Rollback Saga or direct FAILED
                            has_compensation = False
                            for nid, step in session.steps.items():
                                if step.status == ExecutionState.COMPLETED:
                                    node_def = workflow.graph.nodes.get(nid)
                                    if node_def and node_def.compensation_policy and node_def.compensation_policy.compensation_node_id:
                                        has_compensation = True
                                        break
                                        
                            if has_compensation:
                                await self.event_bus.publish(ExecutionFailed(
                                    correlation_id=str(uuid.uuid4()),
                                    session_id=session.id,
                                    error_message=f"Step '{node_id}' failed: {e}. Initiating saga compensation rollback.",
                                    org_id=session.org_id
                                ))
                                await SagaCoordinator.run_compensation(session, workflow, self.step_executor)
                                await self.session_repo.save(session)
                                return
                            else:
                                session.fail(str(e))
                                break
                                
                # 6. Checkpoint Stage
                await self._create_checkpoint(session, trace)
                await self.session_repo.save(session)
                
        # 7. Metrics & 8. Completion Stage
        duration = (time.perf_counter() - start_time) * 1000.0
        session.metrics.total_execution_time_ms = duration
        
        if session.status == ExecutionState.COMPLETED:
            trace.complete(duration)
            await self.event_bus.publish(ExecutionCompleted(correlation_id=str(uuid.uuid4()), session_id=session.id, org_id=session.org_id))
        elif session.status == ExecutionState.FAILED:
            trace.fail(session.error_message or "Execution failed.", duration)
            await self.event_bus.publish(ExecutionFailed(
                correlation_id=str(uuid.uuid4()),
                session_id=session.id,
                error_message=session.error_message or "Execution failed.",
                org_id=session.org_id
            ))
            
        await self.session_repo.save(session)
        await self.trace_repo.save(trace)

    async def _create_checkpoint(self, session: ExecutionSession, trace: ExecutionTrace) -> None:
        """Helper to create execution checkpoints."""
        checkpoint_id = str(uuid.uuid4())
        checkpoint = ExecutionCheckpoint(
            checkpoint_id=checkpoint_id,
            session_id=session.id,
            step_states=session.steps.copy(),
            variables=session.variables.copy()
        )
        session.add_checkpoint(checkpoint)
        trace.log_event("checkpoint", "checkpoint_created", {"checkpoint_id": checkpoint_id})
        await self.event_bus.publish(CheckpointCreated(
            correlation_id=str(uuid.uuid4()),
            session_id=session.id,
            checkpoint_id=checkpoint_id,
            org_id=session.org_id
        ))

    async def _delay_retry(self, session: ExecutionSession, trace: ExecutionTrace, node_id: str, delay: float) -> None:
        """Asynchronous task sleeping for the backoff duration and triggering retry resume."""
        await asyncio.sleep(delay)
        # Load fresh session state from repository to check for cancellation or pause
        fresh_session = await self.session_repo.get_by_id(session.id)
        if not fresh_session or fresh_session.status != ExecutionState.RETRYING:
            logger.info("Retry aborted for session %s: status is no longer RETRYING (current: %s)", session.id, fresh_session.status if fresh_session else "None")
            return
            
        fresh_session.status = ExecutionState.RUNNING
        step = fresh_session.steps.get(node_id)
        if step:
            step.status = ExecutionState.CREATED # Reset to run again
        await self.session_repo.save(fresh_session)
        
        # Resume the pipeline task execution
        asyncio.create_task(self.execute(fresh_session, trace))
