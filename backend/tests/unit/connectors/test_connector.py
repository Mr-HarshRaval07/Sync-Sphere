import pytest
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.value_objects import TransportType, ToolDefinition

def test_connector_creation():
    """Tests that a Connector is initialized with correct default fields."""
    conn = Connector(
        org_id="org_123",
        name="jira",
        transport_type=TransportType.STDIO,
        connection_config={"command": "npx", "args": ["mcp-server-jira"]}
    )
    assert conn.org_id == "org_123"
    assert conn.name == "jira"
    assert conn.transport_type == TransportType.STDIO
    assert conn.is_enabled is True
    assert conn.tools == []
    assert conn.limits.max_requests_per_minute == 60

def test_connector_enable_disable():
    """Tests that a Connector status transitions properly between enabled and disabled."""
    conn = Connector(
        org_id="org_123",
        name="jira",
        transport_type=TransportType.STDIO,
        connection_config={"command": "npx"}
    )
    conn.disable()
    assert conn.status == "DISABLED"
    assert conn.is_enabled is False
    
    conn.enable()
    assert conn.status == "ENABLED"
    assert conn.is_enabled is True

def test_connector_tools_update():
    """Tests that updating a Connector's tool advertisements updates its domain state."""
    conn = Connector(
        org_id="org_123",
        name="jira",
        transport_type=TransportType.STDIO,
        connection_config={"command": "npx"}
    )
    new_tools = [
        ToolDefinition(name="jira_create_issue", description="Create tickets", input_schema={})
    ]
    conn.update_tools(new_tools)
    assert len(conn.tools) == 1
    assert conn.tools[0].name == "jira_create_issue"
