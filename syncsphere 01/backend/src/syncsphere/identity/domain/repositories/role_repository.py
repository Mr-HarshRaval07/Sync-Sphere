from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.identity.domain.entities.role import Role

class RoleRepository(ABC):
    """Abstract Repository interface defining persistence operations for Role entity."""
    
    @abstractmethod
    async def save(self, role: Role) -> None:
        """Saves or updates role document state in persistence."""
        pass

    @abstractmethod
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """Retrieves a role by its unique primary ID."""
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[Role]:
        """Retrieves a role within an organization context by its unique name."""
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[Role]:
        """Lists all roles defined within the tenant organization context."""
        pass

    @abstractmethod
    async def delete(self, role_id: str) -> None:
        """Deletes a role from persistence."""
        pass
