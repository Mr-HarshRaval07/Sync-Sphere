import logging
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.value_objects import ExecutionState

logger = logging.getLogger("syncsphere.runtime.application.services.approval")

class ApprovalCoordinator:
    """Manages manual approval gates, pausing execution loops and resuming them upon decision."""
    
    @staticmethod
    async def request_approval(session: ExecutionSession, node_id: str) -> None:
        """Pauses execution session, shifting it into AWAITING_APPROVAL state."""
        logger.info("Manual approval gate reached at step '%s' for session '%s'. Pausing.", node_id, session.id)
        session.transition_to(ExecutionState.AWAITING_APPROVAL)
        
        step = session.steps.get(node_id)
        if step:
            step.status = ExecutionState.AWAITING_APPROVAL
            
        session.record_timeline_event(f"Awaiting manual approval at step: {node_id}")

    @staticmethod
    async def handle_approval_response(
        session: ExecutionSession,
        node_id: str,
        approved: bool
    ) -> None:
        """Resumes execution or fails the session based on the human decision."""
        logger.info("Approval response received for node '%s': approved=%s", node_id, approved)
        
        step = session.steps.get(node_id)
        if not step or step.status != ExecutionState.AWAITING_APPROVAL:
            raise ValueError(f"Step '{node_id}' is not currently awaiting manual approval.")
            
        if approved:
            step.status = ExecutionState.COMPLETED
            session.transition_to(ExecutionState.RUNNING)
            session.record_step_completion(node_id, {"approved": True})
        else:
            step.status = ExecutionState.FAILED
            step.error = "Manual approval rejected by user."
            session.transition_to(ExecutionState.FAILED)
            session.record_step_failure(node_id, "Manual approval rejected by user.")
