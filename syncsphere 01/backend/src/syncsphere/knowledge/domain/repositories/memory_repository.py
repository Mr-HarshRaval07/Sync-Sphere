from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class MemoryRepository(ABC):
    @abstractmethod
    async def get_memory(self, org_id: str, memory_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_memory(self, org_id: str, memory_type: str, resource_id: str, payload: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def delete_memory(self, org_id: str, memory_type: str, resource_id: str) -> None:
        pass
