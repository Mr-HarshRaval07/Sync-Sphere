from typing import Optional, Dict
from syncsphere.planner.domain.repositories.prompt import PlannerPromptRepository

class MongoPlannerPromptRepository(PlannerPromptRepository):
    """Memory and file-backed prompt repository with MongoDB persistence extension hooks."""
    def __init__(self, defaults: Optional[Dict[str, str]] = None) -> None:
        self._prompts = defaults or {}

    async def get_by_name(self, name: str) -> Optional[str]:
        return self._prompts.get(name)

    async def save(self, name: str, content: str) -> None:
        self._prompts[name] = content
