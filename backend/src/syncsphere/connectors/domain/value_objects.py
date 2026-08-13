from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TransportType(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    OAUTH = "oauth"

class HealthStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"

class ToolParameter(BaseModel):
    """Value object representing a single parameter in a tool schema definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False

class ToolDefinition(BaseModel):
    """Value object representing an MCP Tool advertisement schema."""
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Semantic purpose of the tool")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for input parameters validation")

class ToolResult(BaseModel):
    """Value object representing the result of an MCP tool execution call."""
    content: List[Dict[str, Any]] = Field(default_factory=list, description="Array of content blocks (text/image)")
    is_error: bool = Field(default=False, description="Flag representing execution failure status")

class ConnectorHealth(BaseModel):
    """Value object representing connector runtime health checks metrics."""
    status: HealthStatus = HealthStatus.OFFLINE
    latency_ms: float = 0.0
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

class ConnectorLimits(BaseModel):
    """Value object mapping connection throttling limits."""
    max_requests_per_minute: int = 60
    max_concurrency: int = 10
    timeout_seconds: int = 30

class ConnectorPermissions(BaseModel):
    """Value object mapping required OAuth scopes and role constraints."""
    required_scopes: List[str] = Field(default_factory=list)
    user_roles_allowed: List[str] = Field(default_factory=lambda: ["ADMIN", "DEVELOPER"])
