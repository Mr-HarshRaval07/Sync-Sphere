from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class WorkflowDraft(BaseModel):
    """Initial draft representation of the generated workflow aggregate state."""
    name: str
    description: Optional[str] = ""
    graph: Dict[str, Any] = Field(default_factory=dict, description="Draft WorkflowGraph structure.")
    variables: List[Dict[str, Any]] = Field(default_factory=list, description="Draft Variable list.")

class ExecutionBlueprint(BaseModel):
    """Compiled execution schema containing topological tiers and bindings mapping to the execution plan."""
    workflow_id: str
    version: int
    topological_order: List[str] = Field(default_factory=list)
    execution_nodes: Dict[str, Any] = Field(default_factory=dict)

class PlanningMetrics(BaseModel):
    """Auditing metrics tracking tokens, cost, and latency duration for the planning run."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    planning_time_ms: float = 0.0

class PlanningExplanation(BaseModel):
    """Detailed human-readable reasoning backing selector choices, safety gates, and rejections."""
    tool_selections: Dict[str, str] = Field(default_factory=dict, description="Explanation for each tool selection.")
    approval_gate_reasons: Dict[str, str] = Field(default_factory=dict, description="Explanation for each approval gate.")
    risk_rationales: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None

class OptimizationHint(BaseModel):
    """Optimization recommendations executed on the draft graph."""
    nodes_parallelized: List[str] = Field(default_factory=list)
    redundant_nodes_removed: List[str] = Field(default_factory=list)
    cost_saving: float = 0.0
    latency_reduction_ms: float = 0.0
