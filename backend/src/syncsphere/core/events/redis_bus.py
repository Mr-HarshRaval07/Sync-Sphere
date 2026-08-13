import json
import logging
import asyncio
from typing import Optional
from redis.asyncio import Redis
from .base import BaseEvent
from .interfaces import EventPublisher, EventSubscriber, EventHandler
from .registry import EventRegistry

logger = logging.getLogger("syncsphere.core.events.redis_bus")

class RedisEventBus(EventPublisher, EventSubscriber):
    """
    Production event bus implementing EventPublisher and EventSubscriber.
    Uses Redis Pub/Sub for distributed event broadcast across processes.
    """
    
    def __init__(self, redis_client: Redis, registry: Optional[EventRegistry] = None) -> None:
        self.redis = redis_client
        self.registry = registry or EventRegistry()
        self.pubsub_task: Optional[asyncio.Task] = None
        self._listener_running = False

    async def publish(self, event: BaseEvent) -> None:
        """Serializes and publishes the event to Redis channel corresponding to event_type."""
        channel = f"syncsphere:events:{event.event_type}"
        event_json = event.model_dump_json()
        logger.debug("Publishing event to channel: %s", channel)
        await self.redis.publish(channel, event_json)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Registers a local handler and starts the Redis listener task if not running."""
        self.registry.register(event_type, handler)
        
        # Start background listener if we haven't already
        if not self._listener_running:
            self._listener_running = True
            self.pubsub_task = asyncio.create_task(self._listen_to_redis())

    async def _listen_to_redis(self) -> None:
        """Worker loop listening to subscribed Redis channels and dispatching locally."""
        pubsub = self.redis.pubsub()
        channel_pattern = "syncsphere:events:*"
        logger.info("Starting Redis Pub/Sub pattern listener on: %s", channel_pattern)
        await pubsub.psubscribe(channel_pattern)
        
        try:
            while self._listener_running:
                # Poll for messages with a timeout to allow loop exit checks
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    continue
                
                channel = message["channel"]
                data = message["data"]
                # Extract event type from channel name
                event_type = channel.replace("syncsphere:events:", "")
                
                logger.debug("Received event: %s on channel: %s", event_type, channel)
                
                # Retrieve handlers
                handlers = self.registry.get_handlers(event_type)
                if not handlers:
                    continue
                
                try:
                    payload = json.loads(data)
                    # Resolve handler callbacks in parallel
                    # (In a real system, we wrap them in BaseEvent instances using registry mappings)
                    # For core foundation, we propagate raw payload / reconstructed base event.
                    event_obj = BaseEvent.model_validate(payload)
                    await asyncio.gather(*(h(event_obj) for h in handlers), return_exceptions=True)
                except Exception as e:
                    logger.error("Error dispatching event %s: %s", event_type, str(e), exc_info=True)
        except asyncio.CancelledError:
            logger.info("Event bus listener task was cancelled.")
        finally:
            await pubsub.punsubscribe(channel_pattern)
            await pubsub.close()
            self._listener_running = False

    async def stop(self) -> None:
        """Tears down background listener tasks."""
        self._listener_running = False
        if self.pubsub_task:
            self.pubsub_task.cancel()
            try:
                await self.pubsub_task
            except asyncio.CancelledError:
                pass
