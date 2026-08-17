from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.identity.domain.entities.user import User

class UserRepository(ABC):
    """Abstract Repository interface defining persistence operations for User aggregate."""
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """Saves or updates the user document state in persistence."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user by their unique primary ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieves a user by their unique email address."""
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str, page: int, page_size: int) -> List[User]:
        """Lists users belonging to a specific tenant organization (paginated)."""
        pass

    @abstractmethod
    async def count_by_org(self, org_id: str) -> int:
        """Returns total user count within the tenant organization context."""
        pass
