from datetime import datetime
from typing import Any, Optional
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.approval.domain.value_objects import DelegationType

class ApprovalDelegate(AggregateRoot):
    def __init__(
        self,
        org_id: str,
        from_user_id: str,
        to_user_id: str,
        delegation_type: DelegationType,
        is_active: bool = True,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.delegation_type = delegation_type
        self.is_active = is_active
        self.start_date = start_date
        self.end_date = end_date

    def is_currently_active(self) -> bool:
        """Checks if current timestamp falls within the delegation window and active flag is set."""
        if not self.is_active:
            return False
            
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
                
        return True
