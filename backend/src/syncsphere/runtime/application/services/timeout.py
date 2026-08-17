import logging
from datetime import datetime
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.value_objects import ExecutionState
from syncsphere.workflow.domain.value_objects import TimeoutPolicy

logger = logging.getLogger("syncsphere.runtime.application.services.timeout")

class TimeoutManager:
    """Monitors step execution durations against defined TimeoutPolicies."""
    
    @staticmethod
    def verify_timeout(session: ExecutionSession, node_id: str, policy: TimeoutPolicy) -> bool:
        """
        Checks if the step execution has timed out.
        Returns True if a timeout violation occurred.
        """
        step = session.steps.get(node_id)
        if not step or step.status != ExecutionState.RUNNING or not step.started_at:
            return False
            
        elapsed = (datetime.utcnow() - step.started_at).total_seconds()
        if elapsed > policy.timeout_seconds:
            logger.warning("Step '%s' execution timed out after %.2f seconds (limit: %d).", 
                           node_id, elapsed, policy.timeout_seconds)
            return True
            
        return False
