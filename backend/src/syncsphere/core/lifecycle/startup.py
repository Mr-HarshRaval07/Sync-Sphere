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

    # Initialize Global Built-in APScheduler
    try:
        from syncsphere.core.scheduler import init_scheduler
        await init_scheduler()
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")

    
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

    if container.event_bus and hasattr(container.event_bus, "_listen_to_redis"):
        import asyncio
        container.event_bus._listener_running = True
        container.event_bus.pubsub_task = asyncio.create_task(
            container.event_bus._listen_to_redis()
        )
        logger.info("Event_bus background loop initialized and listening.")
        
    # 5. Startup AI Configuration Validation
    import os
    from syncsphere.core.config.settings import settings
    logger.info("Validating AI Configuration during startup...")
    env_keys = ["OPENROUTER_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"]
    for k in env_keys:
        if not os.getenv(k):
            logger.warning(f"Startup Validation: {k} is missing or empty.")
            
    if not settings.ai.llm_provider:
        logger.error("Startup Validation: Provider name (llm_provider) is missing.")
    if not settings.ai.llm_model:
        logger.error("Startup Validation: Default model (llm_model) is missing.")
        
    # Validate Provider Registration
    try:
        gateway = container.ai_gateway
        if settings.ai.llm_provider not in gateway.provider_registry:
            logger.error(f"Startup Validation: Configured AI provider '{settings.ai.llm_provider}' is not registered in the AI gateway.")
            raise ValueError(f"Configured AI provider {settings.ai.llm_provider} is not registered in the AI gateway.")
        else:
            logger.info(f"Startup Validation: Provider '{settings.ai.llm_provider}' and model '{settings.ai.llm_model}' correctly registered.")
    except Exception as e:
        logger.error(f"Startup Validation: Could not verify provider registration: {e}")

    logger.info("All core components successfully started.")
