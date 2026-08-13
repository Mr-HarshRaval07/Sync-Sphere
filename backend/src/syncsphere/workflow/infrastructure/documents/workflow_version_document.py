from pydantic import Field
from typing import List, Dict, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.workflow.domain.value_objects import WorkflowNode, WorkflowEdge

class WorkflowVersionDocument(BaseTenantDocument):
    """Beanie ODM representation of the WorkflowVersion entity snapshot."""
    workflow_id: str = Field(..., description="Parent workflow primary ID reference")
    version: int = Field(..., description="Snapshot version number")
    description: str = Field(default="")
    state: str = Field(default="DRAFT", description="Status of the version snapshot (e.g. DRAFT, PUBLISHED)")
    
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: List[dict] = Field(default_factory=list)

    class Settings:
        name = "workflow_versions"
        indexes = [
            "org_id",
            ("org_id", "workflow_id"),
            ("org_id", "workflow_id", "version")
        ]
