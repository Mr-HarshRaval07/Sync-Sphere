import logging
from redis.asyncio import Redis

logger = logging.getLogger("syncsphere.runtime.infrastructure.redis_lock")

class RedisExecutionLock:
    """Production Redis-backed distributed lock manager for execution sessions concurrency control."""
    
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client

    async def acquire_lock(self, lock_key: str, owner_id: str, expire_seconds: int = 60) -> bool:
        """
        Attempts to acquire a distributed lock in Redis.
        Returns True if acquired successfully.
        """
        key = f"syncsphere:locks:{lock_key}"
        # setnx with expiration
        res = await self.redis.set(key, owner_id, ex=expire_seconds, nx=True)
        if res:
            logger.info("Lock acquired successfully: key=%s, owner=%s", lock_key, owner_id)
            return True
        return False

    async def release_lock(self, lock_key: str, owner_id: str) -> bool:
        """
        Releases a distributed lock in Redis if owned by the caller.
        Returns True if released successfully.
        """
        key = f"syncsphere:locks:{lock_key}"
        # Perform atomical release checking owner via Lua script
        lua_script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        else
            return 0
        end
        """
        res = await self.redis.eval(lua_script, 1, key, owner_id)
        if res == 1:
            logger.info("Lock released successfully: key=%s, owner=%s", lock_key, owner_id)
            return True
        return False
