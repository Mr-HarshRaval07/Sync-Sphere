class HTTPHeaders:
    """Standard HTTP header names used in SyncSphere AI."""
    CORRELATION_ID = "X-Request-ID"
    TENANT_ID = "X-Org-ID"
    API_KEY = "X-API-Key"
    AUTHORIZATION = "Authorization"
    SUNSET = "Sunset"
    DEPRECATION = "Deprecation"
    SUNSET_LINK = "Link"


class SystemDefaults:
    """Global system constants and defaults."""
    CHARSET = "utf-8"
    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    CURSOR_LIMIT = 50
    MAX_CURSOR_LIMIT = 200


class LogKeys:
    """Predefined keys for structured logging context."""
    CORRELATION_ID = "correlation_id"
    ORG_ID = "org_id"
    ELAPSED_MS = "duration_ms"
    STATUS_CODE = "status_code"
    METHOD = "method"
    PATH = "path"
