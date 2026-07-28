from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """Abstract interface defining the execution contract for LLM routers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Sends prompt to routing provider and returns the completed text response."""
        pass
