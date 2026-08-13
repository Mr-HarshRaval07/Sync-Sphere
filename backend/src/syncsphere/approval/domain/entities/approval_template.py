from typing import Any, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.approval.domain.value_objects import ApprovalChain

class ApprovalTemplate(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        name: str,
        chain: ApprovalChain,
        description: Optional[str] = None,
        version: int = 1,
        id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name
        self.chain = chain
        self.description = description
        self.version = version
