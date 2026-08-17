from pydantic import BaseModel, Field
from typing import Optional

class WorkflowGenerateRequest(BaseModel):
    prompt: str = Field(..., example="Create a Jira ticket when a user signs up")
    strategy: Optional[str] = Field("simple", example="simple")

class WorkflowImproveRequest(BaseModel):
    session_id: str = Field(..., example="60c72b2f9b1d8e2b8c8b4567")
    feedback: str = Field(..., example="Insert an approval step before creating the ticket")

class WorkflowExplainRequest(BaseModel):
    session_id: str = Field(..., example="60c72b2f9b1d8e2b8c8b4567")

class WorkflowValidateRequest(BaseModel):
    prompt: str = Field(..., example="Decompose this action prompt")
