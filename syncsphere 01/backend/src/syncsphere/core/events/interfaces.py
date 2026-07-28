from abc import ABC, abstractmethod
from typing import Callable, Coroutine, Any
from .base import BaseEvent

# Type signature for asynchronous event handlers
EventHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]

class EventPublisher(ABC):
    """Abstract interface defining operations to publish events to a bus."""
    
    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """Publishes the given event to the event stream."""
        pass


class EventSubscriber(ABC):
    """Abstract interface defining operations to subscribe handlers to event channels."""
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribes an event handler callback to a specific event type."""
        pass


class EventDispatcher(ABC):
    """Abstract interface responsible for routing published events to their registered handlers."""
    
    @abstractmethod
    async def dispatch(self, event: BaseEvent) -> None:
        """Dispatches the event to all registered subscriber callbacks."""
        pass
