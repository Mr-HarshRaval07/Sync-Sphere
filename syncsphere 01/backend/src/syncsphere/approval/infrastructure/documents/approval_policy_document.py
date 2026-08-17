from typing import List
from pydantic import Field
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
from syncsphere.approval.domain.value_objects import ApprovalRule, ApprovalChain

class ApprovalPolicyDocument(BaseTenantDocument):
    name: str = Field(..., description="Approval policy name")
    rules: List[ApprovalRule] = Field(default_factory=list, description="Rules determining trigger condition")
    target_chain: ApprovalChain = Field(..., description="Chain schema mapping if rule passes")

    class Settings:
        name = "approval_policies"
        indexes = [
            "org_id",
            "name"
        ]
