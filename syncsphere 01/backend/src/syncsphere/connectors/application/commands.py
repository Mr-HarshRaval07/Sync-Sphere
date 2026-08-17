from pydantic import Field
from typing import Dict, Any, List, Optional
from syncsphere.shared_kernel.types.contracts import BaseCommand
from syncsphere.connectors.domain.value_objects import TransportType

class RegisterConnectorCommand(BaseCommand):
    """Command to register an MCP connector config."""
    name: str
    transport_type: TransportType
    connection_config: Dict[str, Any]
    max_requests_per_minute: int = 60
    required_scopes: List[str] = Field(default_factory=list)


class EnableConnectorCommand(BaseCommand):
    """Command to enable a connector."""
    connector_id: str


class DisableConnectorCommand(BaseCommand):
    """Command to disable a connector."""
    connector_id: str


class UpdateCredentialCommand(BaseCommand):
    """Command to save/rotate encrypted connector secrets."""
    connector_id: str
    secrets: Dict[str, str]
