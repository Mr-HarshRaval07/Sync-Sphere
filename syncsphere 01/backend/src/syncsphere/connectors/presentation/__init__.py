from .routes.connector_routes import router as connector_router
from .oauth_routes import router as oauth_router

__all__ = [
    "connector_router",
    "oauth_router",
]