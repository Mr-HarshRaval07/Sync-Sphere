from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List, Dict, Any

class BaseDTO(BaseModel):
    """Base Data Transfer Object. All API inputs and outputs inherit from this."""
    pass


class BaseCommand(BaseModel):
    """Base Command (Write pipeline representation in CQRS)."""
    pass


class BaseQuery(BaseModel):
    """Base Query (Read pipeline representation in CQRS)."""
    pass


class BaseResponse(BaseModel):
    """Base payload model returned by routers."""
    pass


# Generic Types for reusability
T = TypeVar("T")

# Standard type aliases
JSON = Dict[str, Any]
Metadata = Dict[str, Any]
Headers = Dict[str, str]
