from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from syncsphere.connectors.domain.value_objects import TransportType, HealthStatus

class RegisterConnectorRequest(BaseModel):
    name: str = Field(..., min_length=2)
    transport_type: TransportType
    connection_config: Dict[str, Any]
    max_requests_per_minute: int = 60
    required_scopes: List[str] = Field(default_factory=list)

class ToolDefinitionSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class ConnectorHealthSchema(BaseModel):
    status: HealthStatus
    latency_ms: float
    last_checked: datetime
    error_message: Optional[str] = None

class ConnectorResponse(BaseModel):
    id: str
    name: str
    transport_type: TransportType
    connection_config: Dict[str, Any]
    status: str
    tools: List[ToolDefinitionSchema]
    max_requests_per_minute: int
    health: ConnectorHealthSchema

class UpdateCredentialRequest(BaseModel):
    secrets: Dict[str, str]

class CallToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolResultResponse(BaseModel):
    content: List[Dict[str, Any]]
    is_error: bool
