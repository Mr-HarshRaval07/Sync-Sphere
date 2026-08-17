from abc import ABC, abstractmethod
from typing import Optional

class PlannerPromptRepository(ABC):
    """Abstract interface defining storage operations for reasoning library prompts."""
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[str]:
        """Retrieves template content by name key."""
        pass

    @abstractmethod
    async def save(self, name: str, content: str) -> None:
        """Persists or overrides template content."""
        pass
