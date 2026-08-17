from typing import Any, List, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.approval.domain.value_objects import ApprovalRule, ApprovalChain

class ApprovalPolicy(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        name: str,
        rules: List[ApprovalRule],
        target_chain: ApprovalChain,
        id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.rules = rules
        self.target_chain = target_chain
