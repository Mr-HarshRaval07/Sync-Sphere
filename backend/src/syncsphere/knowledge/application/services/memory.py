import logging
from typing import Optional, Dict, Any

from syncsphere.knowledge.domain.repositories.memory_repository import MemoryRepository

logger = logging.getLogger("syncsphere.knowledge.application.services.memory")

class MemoryService:
    """
    MemoryService provides clean interface facades to query, save, and delete
    long-term context memories across Conversation, Planner, and Runtime boundaries.
    """
    
    def __init__(self, repo: MemoryRepository) -> None:
        self.repo = repo

    async def get_conversation_memory(self, org_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "conversation", session_id)

    async def save_conversation_memory(self, org_id: str, session_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "conversation", session_id, payload)

    async def get_planner_memory(self, org_id: str, planner_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "planner", planner_id)

    async def save_planner_memory(self, org_id: str, planner_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "planner", planner_id, payload)

    async def get_execution_memory(self, org_id: str, execution_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "execution", execution_id)

    async def save_execution_memory(self, org_id: str, execution_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "execution", execution_id, payload)

    async def get_workflow_memory(self, org_id: str, workflow_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "workflow", workflow_id)

    async def save_workflow_memory(self, org_id: str, workflow_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "workflow", workflow_id, payload)

    async def get_organization_memory(self, org_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "organization", org_id)

    async def save_organization_memory(self, org_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "organization", org_id, payload)

    async def get_connector_memory(self, org_id: str, connector_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "connector", connector_id)

    async def save_connector_memory(self, org_id: str, connector_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "connector", connector_id, payload)

    async def get_session_memory(self, org_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "session", session_id)

    async def save_session_memory(self, org_id: str, session_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "session", session_id, payload)

    async def get_user_memory(self, org_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.repo.get_memory(org_id, "user", user_id)

    async def save_user_memory(self, org_id: str, user_id: str, payload: Dict[str, Any]) -> None:
        await self.repo.save_memory(org_id, "user", user_id, payload)
