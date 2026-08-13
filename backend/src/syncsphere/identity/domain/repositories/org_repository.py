from abc import ABC, abstractmethod
from typing import Optional
from syncsphere.identity.domain.entities.organization import Organization

class OrgRepository(ABC):
    """Abstract Repository interface defining persistence operations for Organization aggregate."""
    
    @abstractmethod
    async def save(self, org: Organization) -> None:
        """Saves or updates organization document state in persistence."""
        pass

    @abstractmethod
    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Retrieves an organization by its unique primary ID."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Retrieves an organization by its URL-safe unique slug name."""
        pass
