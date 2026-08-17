from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.value_objects import ExecutionState

class ExecutionSessionRepository(ABC):
    """Abstract interface defining persistence operations for ExecutionSession aggregate root."""
    
    @abstractmethod
    async def save(self, session: ExecutionSession) -> None:
        """Persists or updates session document in DB."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[ExecutionSession]:
        """Retrieves a single session by primary key."""
        pass

    @abstractmethod
    async def list_active(self) -> List[ExecutionSession]:
        """Lists all running or interrupted session documents."""
        pass
