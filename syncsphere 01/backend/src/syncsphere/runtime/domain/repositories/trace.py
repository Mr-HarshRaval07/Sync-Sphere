from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.runtime.domain.entities.trace import ExecutionTrace

class ExecutionTraceRepository(ABC):
    """Abstract interface defining persistence operations for ExecutionTrace telemetry records."""
    
    @abstractmethod
    async def save(self, trace: ExecutionTrace) -> None:
        """Persists or updates trace document in DB."""
        pass

    @abstractmethod
    async def get_by_id(self, trace_id: str) -> Optional[ExecutionTrace]:
        """Retrieves a single trace by primary key."""
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> Optional[ExecutionTrace]:
        """Retrieves execution trace mapped to a session id."""
        pass
