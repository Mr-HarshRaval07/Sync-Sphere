from typing import List, Dict, Any, Optional
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.observability.domain.value_objects import TimelineEvent

class ExecutionReplayDocument(BaseTenantDocument):
    session_id: str
    timeline_events: List[TimelineEvent] = Field(default_factory=list)

    class Settings:
        name = "observability_execution_replays"
        indexes = ["org_id", "session_id"]

class WorkflowReplayDocument(BaseTenantDocument):
    workflow_id: str
    reconstruct_steps: List[Dict[str, Any]] = Field(default_factory=list)

    class Settings:
        name = "observability_workflow_replays"
        indexes = ["org_id", "workflow_id"]

class PlannerReplayDocument(BaseTenantDocument):
    planner_session_id: str
    reasoning_cycles: List[Dict[str, Any]] = Field(default_factory=list)

    class Settings:
        name = "observability_planner_replays"
        indexes = ["org_id", "planner_session_id"]
