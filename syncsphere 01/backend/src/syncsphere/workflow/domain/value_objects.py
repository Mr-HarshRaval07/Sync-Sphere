from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class VariableType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

class RetryPolicy(BaseModel):
    max_attempts: int = Field(default=3, ge=0)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    initial_interval_seconds: int = Field(default=2, ge=1)

class TimeoutPolicy(BaseModel):
    timeout_seconds: int = Field(default=300, ge=1)

class CompensationPolicy(BaseModel):
    compensation_node_id: Optional[str] = None
    parameters_mapping: Dict[str, str] = Field(default_factory=dict)

class InputBinding(BaseModel):
    source_node_id: str
    source_field: str
    target_field: str
    transform_expression: Optional[str] = None

class OutputBinding(BaseModel):
    source_field: str
    target_field: str

class Variable(BaseModel):
    name: str = Field(..., min_length=1)
    type: VariableType
    default_val: Optional[Any] = None

class Expression(BaseModel):
    expression_str: str = Field(..., min_length=1)

class Condition(BaseModel):
    left_operand: str
    operator: str = "EQUAL"  # EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, CONTAINS
    right_operand: Any

class ConnectorBinding(BaseModel):
    connector_id: str
    scopes_override: List[str] = Field(default_factory=list)

class ToolInvocation(BaseModel):
    connector_binding: ConnectorBinding
    tool_name: str
    arguments_map: Dict[str, Any] = Field(default_factory=dict)

class ApprovalGate(BaseModel):
    approver_role_id: str
    timeout_seconds: int = 86400  # Default 24 hours
    message: Optional[str] = None

class WorkflowStepType(str, Enum):
    TOOL_CALL = "tool_call"
    CONDITION = "condition"
    APPROVAL = "approval"
    DELAY = "delay"
    TRANSFORM = "transform"

class WorkflowNode(BaseModel):
    id: str
    name: str
    type: WorkflowStepType
    
    # Type specific configurations (embedded optionally)
    tool_invocation: Optional[ToolInvocation] = None
    condition: Optional[Condition] = None
    approval_gate: Optional[ApprovalGate] = None
    delay_seconds: int = 0
    
    # Execution policies
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    timeout_policy: TimeoutPolicy = Field(default_factory=TimeoutPolicy)
    compensation_policy: CompensationPolicy = Field(default_factory=CompensationPolicy)
    
    # Mappings
    input_bindings: List[InputBinding] = Field(default_factory=list)
    output_bindings: List[OutputBinding] = Field(default_factory=list)

class WorkflowEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    condition_expression: Optional[str] = None

class WorkflowGraph(BaseModel):
    nodes: Dict[str, WorkflowNode] = Field(default_factory=dict)
    edges: List[WorkflowEdge] = Field(default_factory=list)

class ExecutionNode(BaseModel):
    node_id: str
    name: str
    type: WorkflowStepType
    dependencies: List[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    workflow_id: str
    version: int
    topological_order: List[str] = Field(default_factory=list)
    execution_nodes: Dict[str, ExecutionNode] = Field(default_factory=dict)
