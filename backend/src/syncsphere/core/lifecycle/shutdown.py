import logging
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.shared_kernel.infrastructure.redis.connection import redis_manager

logger = logging.getLogger("syncsphere.core.lifecycle.shutdown")

async def run_shutdown() -> None:
    """
    Executes all platform shutdown operations:
    1. Closes Beanie/MongoDB connections.
    2. Tears down the Redis client connections pool.
    """
    logger.info("Stopping system core components...")

    from syncsphere.core.scheduler import shutdown_scheduler
    await shutdown_scheduler()
    
    # 1. MongoDB Disconnect
    await mongodb_manager.disconnect()
    
    # 2. Redis Disconnect
    await redis_manager.disconnect()
    
    logger.info("All core components successfully stopped.")
