from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.workflow.domain.entities.workflow import Workflow

class WorkflowRepository(ABC):
    """Abstract Repository interface defining persistence operations for Workflow aggregate."""
    
    @abstractmethod
    async def save(self, workflow: Workflow) -> None:
        """Saves or updates the workflow state in database."""
        pass

    @abstractmethod
    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Retrieves a workflow by its primary ID."""
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[Workflow]:
        """Retrieves a workflow within an organization context by its name."""
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[Workflow]:
        """Lists active (non-archived) workflows inside the tenant context."""
        pass

    @abstractmethod
    async def count_by_org(self, org_id: str) -> int:
        """Counts active workflows inside the tenant context."""
        pass

    @abstractmethod
    async def delete(self, workflow_id: str) -> None:
        """Permanently deletes a workflow config."""
        pass
