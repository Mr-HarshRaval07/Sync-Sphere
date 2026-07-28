from abc import ABC, abstractmethod
from typing import List, Optional
from syncsphere.approval.domain.entities.approval_request import ApprovalRequest
from syncsphere.approval.domain.entities.approval_delegate import ApprovalDelegate
from syncsphere.approval.domain.entities.approval_policy import ApprovalPolicy
from syncsphere.approval.domain.entities.approval_template import ApprovalTemplate

class ApprovalRequestRepository(ABC):
    @abstractmethod
    async def get_by_id(self, approval_id: str) -> Optional[ApprovalRequest]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[ApprovalRequest]:
        pass

    @abstractmethod
    async def list_pending_by_user(self, org_id: str, user_id: str) -> List[ApprovalRequest]:
        pass

    @abstractmethod
    async def list_all_pending(self, org_id: str) -> List[ApprovalRequest]:
        pass

    @abstractmethod
    async def save(self, request: ApprovalRequest) -> None:
        pass

    @abstractmethod
    async def delete(self, approval_id: str) -> None:
        pass


class ApprovalDelegateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, delegate_id: str) -> Optional[ApprovalDelegate]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[ApprovalDelegate]:
        pass

    @abstractmethod
    async def list_active_delegates_for_user(self, org_id: str, user_id: str) -> List[ApprovalDelegate]:
        pass

    @abstractmethod
    async def save(self, delegate: ApprovalDelegate) -> None:
        pass

    @abstractmethod
    async def delete(self, delegate_id: str) -> None:
        pass


class ApprovalPolicyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, policy_id: str) -> Optional[ApprovalPolicy]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[ApprovalPolicy]:
        pass

    @abstractmethod
    async def save(self, policy: ApprovalPolicy) -> None:
        pass

    @abstractmethod
    async def delete(self, policy_id: str) -> None:
        pass


class ApprovalTemplateRepository(ABC):
    @abstractmethod
    async def get_by_id(self, template_id: str) -> Optional[ApprovalTemplate]:
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[ApprovalTemplate]:
        pass

    @abstractmethod
    async def save(self, template: ApprovalTemplate) -> None:
        pass

    @abstractmethod
    async def delete(self, template_id: str) -> None:
        pass
