from pydantic import Field, BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from syncsphere.shared_kernel.infrastructure.mongodb.base_document import (
    BaseTenantDocument,
)

from syncsphere.connectors.domain.value_objects import (
    TransportType,
    HealthStatus,
)


class ToolDefinitionEmbed(BaseModel):
    """Embedded representation of ToolDefinition inside Connector Document."""

    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)


class ConnectorLimitsEmbed(BaseModel):
    max_requests_per_minute: int = 60
    max_concurrency: int = 10
    timeout_seconds: int = 30


class ConnectorPermissionsEmbed(BaseModel):
    required_scopes: List[str] = Field(
        default_factory=list
    )

    user_roles_allowed: List[str] = Field(
        default_factory=lambda: [
            "ADMIN",
            "DEVELOPER",
        ]
    )


class ConnectorHealthEmbed(BaseModel):
    status: HealthStatus = HealthStatus.OFFLINE

    latency_ms: float = 0.0

    last_checked: datetime = Field(
        default_factory=datetime.utcnow
    )

    error_message: Optional[str] = None


class ConnectorDocument(BaseTenantDocument):
    """
    Beanie ODM representation of the Connector aggregate root.

    Supports:
    - MCP STDIO connectors
    - MCP SSE connectors
    - OAuth integrations such as Google
    """

    name: str = Field(
        ...,
        description="Unique connector name key",
    )

    transport_type: TransportType = Field(
        ...,
        description="Connector type: stdio, sse, or oauth",
    )

    connection_config: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Connector or OAuth integration configuration"
        ),
    )

    status: str = Field(
        default="ENABLED",
        description="ENABLED or DISABLED",
    )

    tools: List[ToolDefinitionEmbed] = Field(
        default_factory=list,
        description="Advertised MCP tools",
    )

    limits: ConnectorLimitsEmbed = Field(
        default_factory=ConnectorLimitsEmbed
    )

    permissions: ConnectorPermissionsEmbed = Field(
        default_factory=ConnectorPermissionsEmbed
    )

    health: ConnectorHealthEmbed = Field(
        default_factory=ConnectorHealthEmbed
    )

    class Settings:
        name = "connectors"

        indexes = [
            "org_id",
            ("org_id", "name"),
        ]