from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class WorkflowGoal(BaseModel):
    """Represents a decomposed atomic target goal derived from user intent."""
    goal_id: str
    description: str
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)

class WorkflowConstraint(BaseModel):
    """Represents safety, transactional, or resource constraints (e.g., budget, approval gate)."""
    constraint_type: str = Field(..., description="E.g., budget, retry, approval, timeout.")
    value: Any
    target_node_id: Optional[str] = None
    severity: str = "critical"  # critical, advisory

class PlanningStep(BaseModel):
    """Represents a single step resolved by the decomposer in the planning sequence."""
    step_id: str
    name: str
    description: str
    capability_required: str = Field(..., description="Semantic representation of tool capability required.")
    depends_on_steps: List[str] = Field(default_factory=list)
    suggested_tool: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ReasoningStep(BaseModel):
    """Models a single chain-of-thought step logged during the reasoning loop."""
    step_index: int
    thought: str
    action: str
    observation: Optional[str] = None
    confidence: float = 1.0

class ExecutionHint(BaseModel):
    """Execution suggestions compiled for the runtime engine (e.g. timeout settings)."""
    parallel_execution_permitted: bool = True
    estimated_latency_ms: float = 0.0
    notes: Optional[str] = None

class PlanningContext(BaseModel):
    """Execution context containing current models, connectors, and session settings."""
    org_id: str
    available_connectors: List[Any] = Field(default_factory=list)
    available_models: List[Any] = Field(default_factory=list)
    history: List[str] = Field(default_factory=list)
