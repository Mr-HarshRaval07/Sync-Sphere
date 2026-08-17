from abc import ABC, abstractmethod
from typing import Optional
from syncsphere.planner.domain.entities.session import PlanningSession

class PlanningSessionRepository(ABC):
    """Abstract interface defining persistence operations for PlanningSession aggregate root."""
    
    @abstractmethod
    async def save(self, session: PlanningSession) -> None:
        """Persists or updates session document in DB."""
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[PlanningSession]:
        """Retrieves a single session by primary key."""
        pass
