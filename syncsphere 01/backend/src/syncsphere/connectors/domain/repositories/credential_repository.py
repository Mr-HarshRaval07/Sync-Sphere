from abc import ABC, abstractmethod
from typing import Optional
from syncsphere.connectors.domain.entities.credential import ConnectorCredential

class CredentialRepository(ABC):
    """Abstract Repository interface defining persistence operations for ConnectorCredential entity."""
    
    @abstractmethod
    async def save(self, credential: ConnectorCredential) -> None:
        """Saves or updates credential details in database."""
        pass

    @abstractmethod
    async def get_by_connector(self, org_id: str, connector_id: str) -> Optional[ConnectorCredential]:
        """Retrieves credential details for a specific connector inside the tenant."""
        pass

    @abstractmethod
    async def delete(self, org_id: str, connector_id: str) -> None:
        """Deletes credentials linked to a connector."""
        pass
