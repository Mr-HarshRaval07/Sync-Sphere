import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.shared_kernel.domain.domain_exception import ValidationException
from syncsphere.runtime.domain.value_objects import (
    ExecutionState,
    ExecutionPolicy,
    ExecutionContext,
    ExecutionStep,
    ExecutionMetrics,
    ExecutionCheckpoint,
    ExecutionHistory,
    ExecutionAST
)

logger = logging.getLogger("syncsphere.runtime.domain.entities.session")

class ExecutionSession(AggregateRoot):
    """
    ExecutionSession represents a running workflow instance, maintaining state variables,
    topological execution steps progress, checkpoints, and saga compensation tasks.
    """
    
    def __init__(
        self,
        org_id: str,
        workflow_id: str,
        version: int,
        status: ExecutionState = ExecutionState.CREATED,
        policy: ExecutionPolicy = ExecutionPolicy.BALANCED,
        variables: Optional[Dict[str, Any]] = None,
        steps: Optional[Dict[str, ExecutionStep]] = None,
        checkpoints: Optional[List[ExecutionCheckpoint]] = None,
        metrics: Optional[ExecutionMetrics] = None,
        history: Optional[ExecutionHistory] = None,
        execution_ast: Optional[ExecutionAST] = None,
        error_message: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.workflow_id = workflow_id
        self.version = version
        self.status = status
        self.policy = policy
        self.variables = variables or {}
        self.steps = steps or {}
        self.checkpoints = checkpoints or []
        self.metrics = metrics or ExecutionMetrics()
        self.history = history or ExecutionHistory(history_id=self.id or "default", events=[])
        self.execution_ast = execution_ast
        self.error_message = error_message

    def transition_to(self, target_state: ExecutionState) -> None:
        """Validates and executes transitions in the execution state machine."""
        allowed = {
            ExecutionState.CREATED: [ExecutionState.QUEUED, ExecutionState.CANCELLED],
            ExecutionState.QUEUED: [ExecutionState.RUNNING, ExecutionState.CANCELLED],
            ExecutionState.RUNNING: [
                ExecutionState.COMPLETED,
                ExecutionState.FAILED,
                ExecutionState.CANCELLED,
                ExecutionState.PAUSED,
                ExecutionState.AWAITING_APPROVAL,
                ExecutionState.RETRYING,
                ExecutionState.COMPENSATING
            ],
            ExecutionState.PAUSED: [ExecutionState.RUNNING, ExecutionState.CANCELLED],
            ExecutionState.AWAITING_APPROVAL: [ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED],
            ExecutionState.RETRYING: [ExecutionState.RUNNING, ExecutionState.FAILED, ExecutionState.CANCELLED],
            ExecutionState.COMPENSATING: [ExecutionState.FAILED, ExecutionState.COMPLETED, ExecutionState.CANCELLED]
        }
        
        current = self.status
        if current == target_state:
            return
            
        allowed_targets = allowed.get(current, [])
        if target_state not in allowed_targets:
            raise ValidationException(
                "INVALID_STATE_TRANSITION",
                f"Cannot transition execution session from state '{current}' to target state '{target_state}'"
            )
            
        self.status = target_state
        self.record_timeline_event(f"Transitioned to {target_state.value}")

    def record_timeline_event(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Logs an action to the internal execution timeline audit trail."""
        self.history.events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details or {}
        })

    def start(self) -> None:
        self.transition_to(ExecutionState.QUEUED)

    def pause(self) -> None:
        self.transition_to(ExecutionState.PAUSED)

    def resume(self) -> None:
        self.transition_to(ExecutionState.RUNNING)

    def cancel(self) -> None:
        self.transition_to(ExecutionState.CANCELLED)

    def complete(self) -> None:
        self.transition_to(ExecutionState.COMPLETED)

    def fail(self, error: str) -> None:
        self.error_message = error
        self.transition_to(ExecutionState.FAILED)

    def record_step_completion(self, node_id: str, outputs: Dict[str, Any]) -> None:
        """Marks a topological step completed, merging outputs into state variables."""
        if node_id not in self.steps:
            raise ValidationException("STEP_NOT_FOUND", f"Topological execution node '{node_id}' is not initialized.")
            
        step = self.steps[node_id]
        step.status = ExecutionState.COMPLETED
        step.outputs = outputs
        step.completed_at = datetime.utcnow()
        
        # Merge outputs into global state variables
        self.variables.update(outputs)
        self.metrics.steps_completed += 1
        self.record_timeline_event(f"Step {node_id} completed successfully", {"outputs": outputs})

    def record_step_failure(self, node_id: str, error: str) -> None:
        """Logs a step invocation failure."""
        if node_id not in self.steps:
            raise ValidationException("STEP_NOT_FOUND", f"Topological execution node '{node_id}' is not initialized.")
            
        step = self.steps[node_id]
        step.status = ExecutionState.FAILED
        step.error = error
        step.completed_at = datetime.utcnow()
        self.metrics.steps_failed += 1
        self.record_timeline_event(f"Step {node_id} failed", {"error": error})

    def add_checkpoint(self, checkpoint: ExecutionCheckpoint) -> None:
        """Saves a checkpoint state snapshot for crash recovery."""
        self.checkpoints.append(checkpoint)
        self.record_timeline_event(f"Checkpoint created: {checkpoint.checkpoint_id}")
