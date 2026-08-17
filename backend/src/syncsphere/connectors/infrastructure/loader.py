import logging
from typing import Dict, Optional
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.value_objects import TransportType
from syncsphere.connectors.infrastructure.mcp.client import MCPClient
from syncsphere.connectors.infrastructure.mcp.transport import StdioTransport, SSETransport

logger = logging.getLogger("syncsphere.connectors.infrastructure.loader")

class ConnectorLoader:
    """
    Manages active, stateful connections to Model Context Protocol (MCP) servers.
    Caches connected clients to prevent duplicate process spawn/handshakes.
    """
    
    def __init__(self) -> None:
        self._active_clients: Dict[str, MCPClient] = {}

    async def get_client(self, connector: Connector) -> MCPClient:
        """
        Retrieves a connected MCPClient for the given connector.
        Establishes a new connection if none exists.
        """
        cid = connector.id
        if cid in self._active_clients:
            client = self._active_clients[cid]
            if client.is_connected:
                return client
            # Cleanup dead client
            await self.close_client(cid)

        # Build Transport based on connection configuration
        transport = None
        if settings_test_mode():
            # If in unit testing, automatically inject InMemoryMCPTransport
            from tests.mocks import InMemoryMCPTransport
            logger.info("Test mode active: injecting InMemoryMCPTransport for %s", connector.name)
            transport = InMemoryMCPTransport(connector_type=connector.name)
        elif connector.transport_type == TransportType.STDIO:
            cmd = connector.connection_config.get("command")
            args = connector.connection_config.get("args", [])
            env = connector.connection_config.get("env", None)
            transport = StdioTransport(command=cmd, args=args, env=env)
        elif connector.transport_type == TransportType.SSE:
            url = connector.connection_config.get("url")
            transport = SSETransport(sse_url=url)
        else:
            raise ValueError(f"Unsupported transport type: {connector.transport_type}")

        # Instantiate and connect client
        client = MCPClient(transport=transport)
        await client.connect()
        
        self._active_clients[cid] = client
        return client

    async def close_client(self, connector_id: str) -> None:
        """Closes connection client and deletes it from cache."""
        if connector_id in self._active_clients:
            client = self._active_clients.pop(connector_id)
            try:
                await client.disconnect()
                logger.info("Closed active MCPClient for connector: %s", connector_id)
            except Exception as e:
                logger.warning("Error disconnecting MCPClient: %s", str(e))

    async def close_all(self) -> None:
        """Tears down all active socket clients."""
        logger.info("Closing all active MCPClient connections...")
        keys = list(self._active_clients.keys())
        for k in keys:
            await self.close_client(k)


def settings_test_mode() -> bool:
    """Helper to detect if application is running in test environment."""
    from syncsphere.core.config.settings import settings, Environment
    return settings.environment == Environment.TEST
