import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from syncsphere.shared_kernel.infrastructure.logging.context import set_correlation_id

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every incoming request has a unique correlation ID (correlation_id).
    Accepts client-provided 'X-Request-ID' headers, otherwise generates a fresh UUID4.
    Exposes the ID in response headers.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
            
        set_correlation_id(request_id)
        request.state.correlation_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
