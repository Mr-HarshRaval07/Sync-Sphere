from typing import Dict, Any, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot

class PlannerTrace(AggregateRoot):
    """
    PlannerTrace is an audit entity logging execution outputs across all planning phases.
    Powers observability, explainability, debugging, and offline analytics.
    """
    
    def __init__(
        self,
        org_id: str,
        session_id: str,
        phases: Optional[Dict[str, Any]] = None,
        status: str = "running",  # running, success, failed
        error_message: Optional[str] = None,
        duration_ms: float = 0.0,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.session_id = session_id
        self.phases = phases or {
            "intent_recognition": None,
            "entity_extraction": None,
            "goal_extraction": None,
            "connector_discovery": None,
            "capability_matching": None,
            "tool_selection": None,
            "reasoning": None,
            "workflow_compilation": None,
            "optimization": None,
            "validation": None
        }
        self.status = status
        self.error_message = error_message
        self.duration_ms = duration_ms

    def record_phase(self, phase_name: str, payload: Any) -> None:
        """Saves telemetry payload for a specific planning phase."""
        if phase_name in self.phases:
            self.phases[phase_name] = payload
        else:
            self.phases[phase_name] = payload

    def complete(self, duration_ms: float) -> None:
        """Marks the execution trace as completed successfully."""
        self.status = "success"
        self.duration_ms = duration_ms

    def fail(self, error: str, duration_ms: float) -> None:
        """Marks the execution trace as failed with an associated message."""
        self.status = "failed"
        self.error_message = error
        self.duration_ms = duration_ms
