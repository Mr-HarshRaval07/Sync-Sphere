from typing import List, Any
from syncsphere.core.config.settings import settings
from syncsphere.shared_kernel.infrastructure.logging.logger import configure_logging, get_logger
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.shared_kernel.infrastructure.redis.connection import redis_manager

logger = get_logger("syncsphere.core.dependency_injection.bootstrap")

class AppContainer:
    """
    Registry for resolved dependencies and infrastructure connection singletons.
    """
    def __init__(self) -> None:
        self.settings = settings
        self.mongodb = mongodb_manager
        self.redis = redis_manager

async def bootstrap_application(document_models: List[Any]) -> AppContainer:
    """
    Performs initialization of logging configurations, connects to MongoDB,
    initializes Beanie document schemas, and establishes Redis client pools.
    """
    # 1. Initialize Structured Logging
    configure_logging()
    logger.info("Initializing bootstrap sequence...", env=settings.environment)

    # 2. Connect to MongoDB and configure Beanie ODM
    await mongodb_manager.connect(document_models)

    # 3. Connect to Redis pool
    redis_manager.connect()

    # Verify Redis connection
    redis_alive = await redis_manager.ping()
    if redis_alive:
        logger.info("Redis connectivity check PASSED.")
    else:
        logger.warning("Redis connectivity check FAILED. Services using Redis may degrade.")

    logger.info("Application bootstrap sequence completed successfully.")
    
    return AppContainer()
