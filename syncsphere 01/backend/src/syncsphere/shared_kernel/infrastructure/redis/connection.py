import logging
from redis.asyncio import Redis, ConnectionPool
from typing import Optional
from syncsphere.core.config.settings import settings

logger = logging.getLogger("syncsphere.shared_kernel.infrastructure.redis")

class RedisConnectionManager:
    """
    Manages Redis connection pooling and client sessions.
    Utilizes redis.asyncio for non-blocking I/O.
    """
    
    def __init__(self) -> None:
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None

    def connect(self) -> None:
        """Initializes the Redis connection pool."""
        logger.info("Initializing Redis connection pool...")
        try:
            self.pool = ConnectionPool.from_url(
                settings.redis_uri,
                max_connections=settings.redis_max_connections,
                decode_responses=True
            )
            self.client = Redis(connection_pool=self.pool)
            logger.info("Redis connection pool initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize Redis connection pool: %s", str(e), exc_info=True)
            raise e

    async def ping(self) -> bool:
        """Tests Redis connectivity with a PING command."""
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception as e:
            logger.warning("Redis ping test failed: %s", str(e))
            return False

    async def disconnect(self) -> None:
        """Closes the Redis connection pool."""
        if self.pool:
            logger.info("Closing Redis connection pool...")
            await self.pool.disconnect()
            logger.info("Redis connection pool closed.")

# Singleton instance of Redis connection manager
redis_manager = RedisConnectionManager()
