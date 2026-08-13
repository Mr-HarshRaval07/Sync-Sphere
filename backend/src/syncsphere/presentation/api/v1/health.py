import time
import logging
from fastapi import APIRouter, Request
from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.mongodb.connection import mongodb_manager
from syncsphere.shared_kernel.infrastructure.redis.connection import redis_manager

logger = logging.getLogger("syncsphere.presentation.api.v1.health")

router = APIRouter(prefix="/health", tags=["Health"])

@router.get(
    "",
    response_model=ResponseEnvelope[dict],
    summary="Basic Liveness/Health Check"
)
async def health_check(request: Request) -> dict:
    """Returns basic status of the API instance."""
    correlation_id = getattr(request.state, "correlation_id", None)
    return {
        "data": {
            "status": "healthy",
            "timestamp": time.time()
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/ready",
    response_model=ResponseEnvelope[dict],
    summary="Readiness Probe"
)
async def readiness_check(request: Request) -> dict:
    """Checks database and cache client connectivity status."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    redis_alive = await redis_manager.ping()
    mongo_alive = False
    
    if mongodb_manager.client:
        try:
            await mongodb_manager.client.admin.command("ping")
            mongo_alive = True
        except Exception as e:
            logger.warning("MongoDB readiness check failed: %s", str(e))

    status = "ready" if (redis_alive and mongo_alive) else "degraded"
    
    return {
        "data": {
            "status": status,
            "checks": {
                "mongodb": "connected" if mongo_alive else "disconnected",
                "redis": "connected" if redis_alive else "disconnected"
            }
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }

@router.get(
    "/live",
    response_model=ResponseEnvelope[dict],
    summary="Liveness Probe"
)
async def liveness_check(request: Request) -> dict:
    """Checks if the API process is alive and responsive."""
    correlation_id = getattr(request.state, "correlation_id", None)
    return {
        "data": {
            "status": "alive"
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }
