from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.identity.domain.entities.api_key import ApiKey

class ApiKeyRepository(ABC):
    """Abstract Repository interface defining persistence operations for ApiKey entity."""
    
    @abstractmethod
    async def save(self, api_key: ApiKey) -> None:
        """Saves or updates API Key state in persistence."""
        pass

    @abstractmethod
    async def get_by_id(self, key_id: str) -> Optional[ApiKey]:
        """Retrieves an API Key by its unique ID."""
        pass

    @abstractmethod
    async def get_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Retrieves an API Key using its secure SHA-256 hash."""
        pass

    @abstractmethod
    async def list_by_user(self, org_id: str, user_id: str) -> List[ApiKey]:
        """Lists active API Keys configured for a user within the tenant."""
        pass
