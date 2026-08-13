from abc import ABC, abstractmethod
from typing import Optional, List
from syncsphere.connectors.domain.entities.connector import Connector

class ConnectorRepository(ABC):
    """Abstract Repository interface defining persistence operations for Connector aggregate."""
    
    @abstractmethod
    async def save(self, connector: Connector) -> None:
        """Saves or updates the connector document in database."""
        pass

    @abstractmethod
    async def get_by_id(self, connector_id: str) -> Optional[Connector]:
        """Retrieves a connector by its primary ID."""
        pass

    @abstractmethod
    async def get_by_name(self, org_id: str, name: str) -> Optional[Connector]:
        """Retrieves a connector within an organization context by its unique name."""
        pass

    @abstractmethod
    async def list_by_org(self, org_id: str) -> List[Connector]:
        """Lists all registered MCP connectors in the tenant context."""
        pass

    @abstractmethod
    async def delete(self, connector_id: str) -> None:
        """Deletes a connector configuration from database."""
        pass
