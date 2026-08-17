import logging
from typing import Dict, List
from .interfaces import EventHandler

logger = logging.getLogger("syncsphere.core.events.registry")

class EventRegistry:
    """
    Registry that keeps track of the correlation mapping between event types
    and their subscribed asynchronous handler functions.
    """
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler) -> None:
        """Registers a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info("Registered event handler for type: %s", event_type)

    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """Retrieves all registered handlers for a specific event type."""
        return self._handlers.get(event_type, [])
