from pydantic import Field, BaseModel
from typing import List, Dict, Any, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.workflow.domain.value_objects import WorkflowStatus, WorkflowNode, WorkflowEdge

class WorkflowDocument(BaseTenantDocument):
    """Beanie ODM representation of the Workflow aggregate root."""
    name: str = Field(..., description="Unique workflow naming")
    description: str = Field(default="")
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    
    # Store Pydantic models directly using Beanie's pydantic parser
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: List[dict] = Field(default_factory=list) # List of serialized variables
    
    active_version: Optional[int] = None
    latest_version: int = Field(default=0)

    class Settings:
        name = "workflows"
        indexes = [
            "org_id",
            ("org_id", "name")
        ]
