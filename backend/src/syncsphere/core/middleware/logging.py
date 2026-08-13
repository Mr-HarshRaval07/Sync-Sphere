import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from syncsphere.shared_kernel.infrastructure.logging.logger import get_logger

logger = get_logger("syncsphere.core.middleware.logging")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records HTTP request metrics (method, URL, status code, duration)
    using structured logging. Excludes health checks from logging noise.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        
        if path.endswith("/health") or path.endswith("/health/ready") or path.endswith("/health/live"):
            return await call_next(request)

        method = request.method
        start_time = time.perf_counter()
        
        logger.info(
            "HTTP request started",
            method=method,
            path=path,
            query_params=str(request.query_params)
        )
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            logger.info(
                "HTTP request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
            return response
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.exception(
                "HTTP request failed",
                method=method,
                path=path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
            )
            raise e
