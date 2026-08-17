from beanie import Document
from pydantic import Field
from typing import List, Dict, Optional
from syncsphere.workflow.domain.value_objects import WorkflowNode, WorkflowEdge

class WorkflowTemplateDocument(Document):
    """Beanie ODM representation of the WorkflowTemplate entity blueprint."""
    name: str = Field(..., description="Template display name key")
    description: str = Field(default="")
    category: str = Field(default="general")
    
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    variables: List[dict] = Field(default_factory=list)

    class Settings:
        name = "workflow_templates"
        indexes = [
            "name",
            "category"
        ]
