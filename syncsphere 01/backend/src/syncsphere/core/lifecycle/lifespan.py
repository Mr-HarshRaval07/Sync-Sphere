import logging
from contextlib import asynccontextmanager
from typing import List, Any
from fastapi import FastAPI
from syncsphere.core.lifecycle.startup import run_startup
from syncsphere.core.lifecycle.shutdown import run_shutdown

logger = logging.getLogger("syncsphere.core.lifecycle.lifespan")

def get_lifespan(document_models: List[Any]):
    """
    Returns an asynccontextmanager suitable for FastAPI's lifespan configuration.
    Initializes/cleans up database models and connection managers.
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("FastAPI lifespan: executing startup tasks...")
        await run_startup(document_models)
        
        yield
        
        logger.info("FastAPI lifespan: executing shutdown tasks...")
        await run_shutdown()
        
    return lifespan
