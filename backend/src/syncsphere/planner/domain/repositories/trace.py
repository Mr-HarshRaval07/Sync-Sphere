from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.planner.domain.entities.trace import PlannerTrace

class PlannerTraceRepository(ABC):
    """Abstract interface defining persistence operations for PlannerTrace aggregate."""
    
    @abstractmethod
    async def save(self, trace: PlannerTrace) -> None:
        """Persists or updates trace document in DB."""
        pass

    @abstractmethod
    async def get_by_id(self, trace_id: str) -> Optional[PlannerTrace]:
        """Retrieves a single trace by primary key."""
        pass

    @abstractmethod
    async def list_by_session(self, session_id: str) -> List[PlannerTrace]:
        """Lists all execution traces mapped to a planning session."""
        pass
