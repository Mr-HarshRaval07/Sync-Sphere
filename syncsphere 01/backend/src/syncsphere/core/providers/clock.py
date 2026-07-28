import datetime
from abc import ABC, abstractmethod

class ClockProvider(ABC):
    """Abstract interface defining date/time access."""
    
    @abstractmethod
    def now(self) -> datetime.datetime:
        """Returns the current date and time (UTC)."""
        pass
