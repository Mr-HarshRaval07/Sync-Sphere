import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from syncsphere.shared_kernel.infrastructure.logging.context import set_org_id

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve the tenant context (org_id) from the request.
    Decodes the JWT payload to extract the 'org' claim, setting the thread-safe context variable.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        org_id = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                org_id = payload.get("org")
            except Exception:
                pass
                
        if not org_id and request.headers.get("X-Org-ID"):
            org_id = request.headers.get("X-Org-ID")

        request.state.org_id = org_id
        set_org_id(org_id)
        
        try:
            response = await call_next(request)
            return response
        finally:
            set_org_id(None)
