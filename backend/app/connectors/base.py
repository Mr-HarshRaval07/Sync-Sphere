from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """
    Abstract base class for all external service connectors.
    """

    @abstractmethod
    async def connect(self):
        """Establish connection or validate credentials."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close any open resources."""
        pass

    @abstractmethod
    async def execute(self, action: str, payload: dict):
        """
        Execute an action on the external service.
        """
        pass