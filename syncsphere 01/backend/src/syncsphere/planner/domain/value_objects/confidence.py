from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RiskAssessment(BaseModel):
    """Calculated safety assessment profiling potential data loss or security overruns."""
    safety_score: float = Field(1.0, ge=0.0, le=1.0)
    risk_level: str = "low"  # low, medium, high
    identified_risks: List[str] = Field(default_factory=list)
    has_destructive_actions: bool = False

class ConfidenceScore(BaseModel):
    """Component confidence score report calculated by the ConfidenceEngine."""
    intent_confidence: float = Field(1.0, ge=0.0, le=1.0)
    connector_confidence: float = Field(1.0, ge=0.0, le=1.0)
    tool_confidence: float = Field(1.0, ge=0.0, le=1.0)
    step_confidence: float = Field(1.0, ge=0.0, le=1.0)
    overall_confidence: float = Field(1.0, ge=0.0, le=1.0)

class PlannerFeedback(BaseModel):
    """Saves human modifications and directions to refine generated plans."""
    adjustment_instruction: str
    approved: bool = False
    notes: Optional[str] = None
