from typing import Optional
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.approval.domain.value_objects import ApprovalChain

class ApprovalTemplateDocument(BaseTenantDocument):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., description="Workflow template name")
    chain: ApprovalChain = Field(..., description="Approval stages flow layout")
    description: Optional[str] = None
    version: int = 1

    class Settings:
        name = "approval_templates"
        indexes = [
            "org_id",
            "name",
            "version"
        ]
