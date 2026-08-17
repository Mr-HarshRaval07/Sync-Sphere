from pydantic import BaseModel, Field
from typing import Optional

class GenerateWorkflowCommand(BaseModel):
    org_id: str
    user_id: str
    prompt: str
    strategy: str = "simple"  # simple, reasoning, reflection, tree_of_thought
    correlation_id: Optional[str] = None

class ImproveWorkflowCommand(BaseModel):
    org_id: str
    session_id: str
    feedback: str
    correlation_id: Optional[str] = None

class ValidateWorkflowPromptCommand(BaseModel):
    org_id: str
    prompt: str
    correlation_id: Optional[str] = None

class ExplainWorkflowCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None

class OptimizeWorkflowCommand(BaseModel):
    org_id: str
    session_id: str
    correlation_id: Optional[str] = None
