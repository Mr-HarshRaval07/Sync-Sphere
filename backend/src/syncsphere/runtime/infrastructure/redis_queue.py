import logging
from typing import Optional
from redis.asyncio import Redis

logger = logging.getLogger("syncsphere.runtime.infrastructure.redis_queue")

class RedisExecutionQueue:
    """Production Redis-backed execution queue manager using lists."""
    
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
        self.queue_key = "syncsphere:queues:sessions"

    async def push_session(self, session_id: str) -> None:
        """Pushes a session ID onto the execution queue."""
        logger.debug("Pushing session '%s' onto queue.", session_id)
        await self.redis.lpush(self.queue_key, session_id)

    async def pop_session(self) -> Optional[str]:
        """Pops a session ID off the execution queue (non-blocking)."""
        session_id = await self.redis.rpop(self.queue_key)
        if session_id:
            logger.debug("Popped session '%s' from queue.", session_id)
            return str(session_id)
        return None

    async def get_length(self) -> int:
        """Returns the current queue length count."""
        return await self.redis.llen(self.queue_key)
