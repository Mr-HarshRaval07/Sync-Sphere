from datetime import datetime
from typing import Optional
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument

class ApprovalDelegateDocument(BaseTenantDocument):
    id: Optional[str] = Field(default=None, alias="_id")
    from_user_id: str = Field(..., description="User ID delegating their tasks")
    to_user_id: str = Field(..., description="User ID receiving delegated tasks")
    delegation_type: str = Field(..., description="TEMPORARY, PERMANENT, OUT_OF_OFFICE, AUTOMATIC")
    is_active: bool = Field(default=True)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Settings:
        name = "approval_delegates"
        indexes = [
            "org_id",
            "from_user_id",
            "is_active"
        ]
