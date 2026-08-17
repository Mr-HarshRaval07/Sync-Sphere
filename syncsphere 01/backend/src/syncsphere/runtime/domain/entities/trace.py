from typing import Dict, Any, List, Optional
from datetime import datetime
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot

class ExecutionTrace(AggregateRoot):
    """
    ExecutionTrace tracks detailed step scheduling, worker dispatches, node executions,
    retries, and saga compensations for observabilities and debugging replays.
    """
    
    def __init__(
        self,
        org_id: str,
        session_id: str,
        phases: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        status: str = "running",  # running, success, failed
        duration_ms: float = 0.0,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.session_id = session_id
        self.phases = phases or {
            "scheduling": [],
            "dispatch": [],
            "node_execution": [],
            "retry": [],
            "timeout": [],
            "approval": [],
            "checkpoint": [],
            "compensation": [],
            "completion": []
        }
        self.status = status
        self.duration_ms = duration_ms

    def log_event(self, phase_name: str, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Appends a tracing event payload to the associated phase list."""
        if phase_name not in self.phases:
            self.phases[phase_name] = []
        self.phases[phase_name].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "details": details or {}
        })

    def complete(self, duration_ms: float) -> None:
        self.status = "success"
        self.duration_ms = duration_ms
        self.log_event("completion", "execution_completed_successfully", {"duration_ms": duration_ms})

    def fail(self, error: str, duration_ms: float) -> None:
        self.status = "failed"
        self.duration_ms = duration_ms
        self.log_event("completion", "execution_failed", {"error": error, "duration_ms": duration_ms})
