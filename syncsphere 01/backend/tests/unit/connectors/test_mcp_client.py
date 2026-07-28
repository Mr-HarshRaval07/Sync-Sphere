import pytest
from syncsphere.connectors.infrastructure.mcp.client import MCPClient
from tests.mocks import InMemoryMCPTransport

@pytest.mark.anyio
async def test_mcp_client_handshake_and_list_tools():
    """Tests that the MCPClient initializes and successfully retrieves tools from Mock server."""
    transport = InMemoryMCPTransport(connector_type="slack")
    client = MCPClient(transport=transport)
    
    await client.connect()
    assert client.is_connected is True
    
    tools = await client.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "slack_post_message"
    assert tools[0].description == "Posts a message to a Slack channel"
    
    await client.disconnect()
    assert client.is_connected is False

@pytest.mark.anyio
async def test_mcp_client_call_tool():
    """Tests invoking a tool on the mock server via JSON-RPC."""
    transport = InMemoryMCPTransport(connector_type="jira")
    client = MCPClient(transport=transport)
    
    await client.connect()
    
    res = await client.call_tool(
        tool_name="jira_create_issue",
        arguments={"project": "PROJ", "summary": "Test issue"}
    )
    
    assert res.is_error is False
    assert len(res.content) == 1
    assert "jira_create_issue" in res.content[0]["text"]
    
    await client.disconnect()
