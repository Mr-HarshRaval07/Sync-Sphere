from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Abstract base class for all LLM providers.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        """
        pass