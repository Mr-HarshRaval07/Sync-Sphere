from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ASTVariable(BaseModel):
    """Represents a variable declaration or binding parameter within the Planner PlanAST."""
    name: str
    type: str = "string"  # string, number, boolean, object, array
    value: Optional[Any] = None
    binding_expression: Optional[str] = None

class ASTNode(BaseModel):
    """A single node inside the PlanAST tree representation."""
    node_id: str
    name: str
    type: str = "action"  # action, condition, approval, delay, transform
    connector_id: Optional[str] = None
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[ASTVariable] = Field(default_factory=list)
    outputs: List[ASTVariable] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    condition_left: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_right: Optional[Any] = None

class ASTFlow(BaseModel):
    """Structures execution pathways and sequence branches inside the AST."""
    entry_nodes: List[str] = Field(default_factory=list)
    exit_nodes: List[str] = Field(default_factory=list)
    parallel_paths: List[List[str]] = Field(default_factory=list)

class PlanAST(BaseModel):
    """
    Abstract Syntax Tree representation of the generated plan.
    Internal to the planner context and never exposed directly to the workflow runtime.
    """
    variables: List[ASTVariable] = Field(default_factory=list)
    nodes: List[ASTNode] = Field(default_factory=list)
    flows: ASTFlow = Field(default_factory=ASTFlow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
