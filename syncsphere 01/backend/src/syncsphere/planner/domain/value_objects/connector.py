from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ConnectorCandidate(BaseModel):
    """Represents a potential connector matching the required domain action."""
    connector_id: str
    name: str
    score: float = Field(1.0, ge=0.0, le=1.0)
    visibility_permitted: bool = True

class ToolCandidate(BaseModel):
    """Represents a potential tool matching the required planning step capability."""
    tool_name: str
    connector_id: str
    score: float = Field(1.0, ge=0.0, le=1.0)
    description_match_score: float = 1.0

class CapabilityMatch(BaseModel):
    """Encapsulates capability evaluation and ranking for a planning step."""
    step_id: str
    best_connector: Optional[ConnectorCandidate] = None
    best_tool: Optional[ToolCandidate] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    match_explanation: str = ""
