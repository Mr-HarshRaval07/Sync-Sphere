from pydantic import Field
from syncsphere.core.events.base import BaseEvent

class PlanningStarted(BaseEvent):
    """Fired when a planning session begins processing user prompt."""
    event_type: str = "planner.planning_started"
    session_id: str

class IntentRecognized(BaseEvent):
    """Fired when the planner classifier resolves user prompt intent."""
    event_type: str = "planner.intent_recognized"
    session_id: str
    category: str
    confidence_score: float

class WorkflowGenerated(BaseEvent):
    """Fired when the planner reasoning and compilation synthesizes the draft workflow."""
    event_type: str = "planner.workflow_generated"
    session_id: str
    workflow_id: str

class WorkflowOptimized(BaseEvent):
    """Fired when graph parallelization or cost optimizations are completed."""
    event_type: str = "planner.workflow_optimized"
    session_id: str
    workflow_id: str
    nodes_parallelized: int
    redundancy_removed: int

class WorkflowValidated(BaseEvent):
    """Fired when the validator completes structural and safety evaluation checks."""
    event_type: str = "planner.workflow_validated"
    session_id: str
    workflow_id: str
    is_valid: bool

class PlanningCompleted(BaseEvent):
    """Fired when a session successfully completes compilation and registers objects."""
    event_type: str = "planner.planning_completed"
    session_id: str
    workflow_id: str
    active_version: int

class PlanningRejected(BaseEvent):
    """Fired when a request is blocked by safety violations or low confidence thresholds."""
    event_type: str = "planner.planning_rejected"
    session_id: str
    rejection_reason: str
