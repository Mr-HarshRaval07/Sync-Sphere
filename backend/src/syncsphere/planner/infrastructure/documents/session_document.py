from pydantic import Field
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class PlanningSessionDocument(BaseTenantDocument):
    """Beanie ODM representation of the PlanningSession aggregate root."""
    user_id: str
    prompt_history: List[str] = Field(default_factory=list)
    current_intent: Optional[Dict[str, Any]] = None
    current_ast: Optional[Dict[str, Any]] = None
    generated_workflow_id: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)

    class Settings:
        name = "planning_sessions"
        indexes = [
            "org_id",
            "user_id"
        ]
