from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from syncsphere.workflow.domain.value_objects import (
    WorkflowStatus,
    WorkflowNode,
    WorkflowEdge,
    Variable,
    ExecutionNode
)

class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = ""
    variables: List[Variable] = Field(default_factory=list)

class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[Dict[str, WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    variables: Optional[List[Variable]] = None

class CloneWorkflowRequest(BaseModel):
    new_name: str = Field(..., min_length=2)

class PublishWorkflowRequest(BaseModel):
    version_description: Optional[str] = ""

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    status: WorkflowStatus
    # `state` mirrors `status` — the frontend WorkflowCard checks `workflow.state`
    state: WorkflowStatus
    nodes: Dict[str, WorkflowNode]
    edges: List[WorkflowEdge]
    variables: List[Variable]
    active_version: Optional[int]
    latest_version: int

class WorkflowVersionResponse(BaseModel):
    id: str
    workflow_id: str
    version: int
    description: str
    state: str
    nodes: Dict[str, WorkflowNode]
    edges: List[WorkflowEdge]
    variables: List[Variable]

class ExecutionNodeSchema(BaseModel):
    node_id: str
    name: str
    type: str
    dependencies: List[str]

class ExecutionPlanResponse(BaseModel):
    workflow_id: str
    version: int
    topological_order: List[str]
    execution_nodes: Dict[str, ExecutionNodeSchema]
