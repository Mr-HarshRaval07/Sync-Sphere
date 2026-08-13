from typing import List, Optional, Dict, Any
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.connectors.domain.value_objects import (
    TransportType,
    ToolDefinition,
    ConnectorLimits,
    ConnectorPermissions,
    ConnectorHealth,
)

class Connector(AggregateRoot):
    """
    Connector aggregate root representing a registered Model Context Protocol (MCP) server.
    """
    
    def __init__(
        self,
        org_id: str,
        name: str,
        transport_type: TransportType,
        connection_config: Dict[str, Any],
        status: str = "ENABLED",
        tools: Optional[List[ToolDefinition]] = None,
        limits: Optional[ConnectorLimits] = None,
        permissions: Optional[ConnectorPermissions] = None,
        health: Optional[ConnectorHealth] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.name = name.lower().strip()
        self.transport_type = transport_type
        
        # connection_config: for stdio, {"command": "node", "args": ["server.js"], "env": {}};
        # for sse, {"url": "http://localhost:8080/sse"}
        self.connection_config = connection_config
        self.status = status
        self.tools: List[ToolDefinition] = tools or []
        self.limits = limits or ConnectorLimits()
        self.permissions = permissions or ConnectorPermissions()
        self.health = health or ConnectorHealth()

    def enable(self) -> None:
        """Enables the connector for workflow orchestrations."""
        self.status = "ENABLED"

    def disable(self) -> None:
        """Disables the connector, blocking active workflow execution requests."""
        self.status = "DISABLED"

    @property
    def is_enabled(self) -> bool:
        """Returns True if the connector is currently active."""
        return self.status == "ENABLED"

    def update_tools(self, tools: List[ToolDefinition]) -> None:
        """Updates the list of advertised tools from an MCP tools/list response."""
        self.tools = tools

    def update_health(self, health: ConnectorHealth) -> None:
        """Updates health status and performance latencies."""
        self.health = health
