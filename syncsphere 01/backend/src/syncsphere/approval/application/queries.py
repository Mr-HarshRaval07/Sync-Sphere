from pydantic import BaseModel
from typing import Optional

class GetApprovalStatusQuery(BaseModel):
    org_id: str
    approval_id: str

class GetApprovalHistoryQuery(BaseModel):
    org_id: str
    approval_id: str

class GetPendingApprovalsQuery(BaseModel):
    org_id: str
    user_id: str

class GetApprovalStatisticsQuery(BaseModel):
    org_id: str
    workflow_id: Optional[str] = None
