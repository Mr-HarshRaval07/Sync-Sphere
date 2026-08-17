from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.workflow.domain.entities.workflow_version import WorkflowVersion

class WorkflowVersionRepository(ABC):
    """Abstract Repository interface defining persistence operations for WorkflowVersion snapshots."""
    
    @abstractmethod
    async def save(self, version: WorkflowVersion) -> None:
        """Saves a workflow version snapshot in database."""
        pass

    @abstractmethod
    async def get_by_version(self, workflow_id: str, version: int) -> Optional[WorkflowVersion]:
        """Retrieves a specific historical version snapshot."""
        pass

    @abstractmethod
    async def list_versions(self, workflow_id: str) -> List[WorkflowVersion]:
        """Lists all snapshots stored for a workflow."""
        pass
