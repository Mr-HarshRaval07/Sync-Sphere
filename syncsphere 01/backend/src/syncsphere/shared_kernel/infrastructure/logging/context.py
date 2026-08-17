from contextvars import ContextVar
from typing import Optional

# Thread and coroutine-safe context variables
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
org_id_ctx: ContextVar[Optional[str]] = ContextVar("org_id", default=None)

def get_correlation_id() -> Optional[str]:
    """Retrieves the current request's correlation ID."""
    return correlation_id_ctx.get()

def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Sets the current request's correlation ID."""
    correlation_id_ctx.set(correlation_id)

def get_org_id() -> Optional[str]:
    """Retrieves the current request's tenant organization ID."""
    return org_id_ctx.get()

def set_org_id(org_id: Optional[str]) -> None:
    """Sets the current request's tenant organization ID."""
    org_id_ctx.set(org_id)

def clear_context() -> None:
    """Resets the context variables to None."""
    correlation_id_ctx.set(None)
    org_id_ctx.set(None)
