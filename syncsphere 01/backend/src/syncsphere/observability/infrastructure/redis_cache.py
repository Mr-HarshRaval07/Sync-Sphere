from typing import Optional, Dict
from redis.asyncio import Redis
import json
import logging

logger = logging.getLogger("syncsphere.observability.redis_cache")

class RedisMetricCache:
    """Caching layer for hot metrics in Redis to optimize dashboard speeds."""
    def __init__(self, redis_client: Optional[Redis] = None) -> None:
        self.redis = redis_client

    async def cache_metric(self, org_id: str, name: str, value: float) -> None:
        if not self.redis:
            return
        key = f"syncsphere:metrics:{org_id}:{name}"
        try:
            await self.redis.set(key, str(value), ex=3600)  # TTL of 1 hour
        except Exception as e:
            logger.warning(f"Failed to cache metric {name} in Redis: {e}")

    async def get_cached_metric(self, org_id: str, name: str) -> Optional[float]:
        if not self.redis:
            return None
        key = f"syncsphere:metrics:{org_id}:{name}"
        try:
            val = await self.redis.get(key)
            return float(val) if val else None
        except Exception as e:
            logger.warning(f"Failed to fetch cached metric {name} from Redis: {e}")
            return None
