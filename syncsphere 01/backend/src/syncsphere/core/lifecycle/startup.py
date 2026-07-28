import logging
from typing import List, Any
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.shared_kernel.infrastructure.redis.connection import redis_manager

logger = logging.getLogger("syncsphere.core.lifecycle.startup")

async def run_startup(document_models: List[Any]) -> None:
    """
    Executes all foundation startup operations:
    1. Establishes connection to MongoDB and initializes Beanie models.
    2. Initializes Redis connection pool.
    """
    logger.info("Starting system core components...")
    
    # 1. MongoDB Connection (dev-friendly: may be non-fatal)
    try:
        await mongodb_manager.connect(document_models)
    except Exception:
        # If Mongo is required this will already have raised from connection.py
        # Otherwise, connection.py will have returned without raising.
        logger.exception("MongoDB startup failed.")
        raise

    
    # 2. Redis Connection
    redis_manager.connect()
    redis_alive = await redis_manager.ping()
    if redis_alive:
        logger.info("Redis server is online and reachable.")
    else:
        logger.warning("Redis ping failed. Caching and rate limits may degrade.")
        
    # 3. Wire Container Dependency Graph
    from syncsphere.core.dependency_injection.container import container
    container.wire_dependencies()
        
    logger.info("All core components successfully started.")
