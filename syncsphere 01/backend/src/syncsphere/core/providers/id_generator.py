from abc import ABC, abstractmethod

class IDGenerator(ABC):
    """Abstract interface defining unique identifier generation."""
    
    @abstractmethod
    def generate(self, prefix: str = "") -> str:
        """Generates a structured unique identifier string, optionally containing a prefix."""
        pass
