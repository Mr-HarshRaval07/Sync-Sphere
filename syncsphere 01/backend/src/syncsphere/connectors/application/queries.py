from typing import Dict, Any
from syncsphere.shared_kernel.types.contracts import BaseQuery

class ListConnectorsQuery(BaseQuery):
    """Query to list registered connectors within organization."""
    org_id: str


class GetConnectorQuery(BaseQuery):
    """Query to retrieve a single connector profile details."""
    org_id: str
    connector_id: str


class CallToolQuery(BaseQuery):
    """Query to execute an MCP tool invocation command."""
    org_id: str
    connector_id: str
    tool_name: str
    arguments: Dict[str, Any]
