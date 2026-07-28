from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.domain.entity import Entity

class ExecutionSaga(Entity):
    """
    Coordinates compensation sagas, keeping lists of executed steps
    and executing compensating steps in reverse topological order upon failure.
    """
    
    def __init__(
        self,
        completed_steps: Optional[List[str]] = None,
        compensated_steps: Optional[List[str]] = None,
        status: str = "active",  # active, compensating, completed, failed
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.completed_steps = completed_steps or []
        self.compensated_steps = compensated_steps or []
        self.status = status

    def record_step_completed(self, node_id: str) -> None:
        if node_id not in self.completed_steps:
            self.completed_steps.append(node_id)

    def record_compensation_executed(self, node_id: str) -> None:
        if node_id not in self.compensated_steps:
            self.compensated_steps.append(node_id)

    def start_compensation(self) -> None:
        self.status = "compensating"

    def complete_compensation(self) -> None:
        self.status = "completed"

    def fail_compensation(self) -> None:
        self.status = "failed"
