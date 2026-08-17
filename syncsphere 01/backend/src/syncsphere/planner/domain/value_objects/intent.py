from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ExtractedEntity(BaseModel):
    """Represents an individual entity extracted from the user natural language prompt."""
    name: str = Field(..., description="Name of the parameter or entity key.")
    value: Any = Field(..., description="Extracted literal value.")
    entity_type: str = Field("string", description="Data type of the entity (string, number, boolean, object, array).")
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class IntentConfidence(BaseModel):
    """Metadata detailing the classification confidence score and rationale."""
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    is_unambiguous: bool = True
    reasoning: Optional[str] = ""

class IntentClassification(BaseModel):
    """Contains classification details mapping the prompt into core intentions."""
    category: str = Field(..., description="Goal category e.g., workflow_generation, workflow_improvement, explanation.")
    confidence: IntentConfidence
    primary_goal: str = Field(..., description="The main intent sentence resolved by the planner.")

class UserIntent(BaseModel):
    """Aggregate value object encapsulating user intent classification and extracted entities."""
    raw_prompt: str
    classification: IntentClassification
    entities: List[ExtractedEntity] = Field(default_factory=list)
