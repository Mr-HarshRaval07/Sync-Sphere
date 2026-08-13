from pydantic import BaseModel

class PreviewWorkflowQuery(BaseModel):
    org_id: str
    session_id: str

class PreviewExecutionGraphQuery(BaseModel):
    org_id: str
    session_id: str

class ExplainPlanQuery(BaseModel):
    org_id: str
    session_id: str

class EstimateExecutionCostQuery(BaseModel):
    org_id: str
    session_id: str

class EstimateExecutionTimeQuery(BaseModel):
    org_id: str
    session_id: str
