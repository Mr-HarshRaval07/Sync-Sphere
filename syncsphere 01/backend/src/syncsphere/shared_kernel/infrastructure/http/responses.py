from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from datetime import datetime

T = TypeVar("T")

class ResponseMeta(BaseModel):
    """Metadata block containing correlation identifiers and timestamps."""
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class PaginationInfo(BaseModel):
    """Pagination details for list-based collection endpoints."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard top-level envelope for single-resource responses."""
    data: T
    meta: ResponseMeta

class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    """Standard top-level envelope for paginated collection responses."""
    data: List[T]
    pagination: PaginationInfo
    meta: ResponseMeta

class ActionResponseEnvelope(BaseModel, Generic[T]):
    """Standard envelope for RPC/action operations that return results and a status message."""
    data: T
    message: str
    meta: ResponseMeta
