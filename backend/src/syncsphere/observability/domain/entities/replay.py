from typing import List, Optional, Dict, Any
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.observability.domain.value_objects import TimelineEvent

class ExecutionReplay(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        session_id: str,
        timeline_events: Optional[List[TimelineEvent]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.session_id = session_id
        self.timeline_events = timeline_events or []

class WorkflowReplay(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        workflow_id: str,
        reconstruct_steps: Optional[List[Dict[str, Any]]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.workflow_id = workflow_id
        self.reconstruct_steps = reconstruct_steps or []

class PlannerReplay(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        planner_session_id: str,
        reasoning_cycles: Optional[List[Dict[str, Any]]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.planner_session_id = planner_session_id
        self.reasoning_cycles = reasoning_cycles or []
