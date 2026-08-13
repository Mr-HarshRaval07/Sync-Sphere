import asyncio
import logging
from typing import Dict, Any, List, Optional
from .transport import MCPTransport
from syncsphere.connectors.domain.value_objects import ToolDefinition, ToolResult

logger = logging.getLogger("syncsphere.connectors.infrastructure.mcp.client")

class MCPClient:
    """
    An asynchronous client implementing the Model Context Protocol (MCP) specification.
    Coordinates JSON-RPC 2.0 communication over STDIO or SSE transports.
    """
    
    def __init__(self, transport: MCPTransport) -> None:
        self.transport = transport
        self.request_id = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self.listener_task: Optional[asyncio.Task] = None
        self.is_connected = False

    async def connect(self) -> None:
        """Starts transport and spawns background packet listener task."""
        await self.transport.start()
        self.is_connected = True
        self.listener_task = asyncio.create_task(self._listen())
        
        # Perform MCP Handshake
        logger.info("Performing MCP handshake...")
        init_res = await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "SyncSphere Client", "version": "1.0.0"}
            }
        )
        logger.info("MCP Handshake complete. Protocol: %s", init_res.get("protocolVersion"))

    async def list_tools(self) -> List[ToolDefinition]:
        """Queries the MCP server for advertised tools."""
        res = await self._send_request("tools/list", {})
        tools_payload = res.get("tools", [])
        
        tools = []
        for t in tools_payload:
            tools.append(
                ToolDefinition(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {})
                )
            )
        return tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Invokes a tool on the MCP server."""
        res = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments
            }
        )
        content = res.get("content", [])
        is_error = res.get("isError", False)
        return ToolResult(content=content, is_error=is_error)

    async def disconnect(self) -> None:
        """Closes transport channel and listener loop."""
        self.is_connected = False
        if self.listener_task:
            self.listener_task.cancel()
        await self.transport.close()

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a JSON-RPC request and suspends until response is received."""
        self.request_id += 1
        rid = self.request_id
        
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[rid] = future

        request_payload = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": params
        }

        await self.transport.send_message(request_payload)
        
        # Await future resolution with a timeout (e.g. 30 seconds)
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            self.pending_requests.pop(rid, None)
            raise TimeoutError(f"MCP request to method '{method}' timed out after 30 seconds.")

    async def _listen(self) -> None:
        """Background loop reading JSON-RPC packets from transport."""
        try:
            while self.is_connected:
                msg = await self.transport.receive_message()
                if msg is None:
                    break
                
                # Check JSON-RPC 2.0 response format
                rid = msg.get("id")
                if rid is not None and rid in self.pending_requests:
                    future = self.pending_requests.pop(rid)
                    if "error" in msg:
                        future.set_exception(
                            IOError(f"MCP Server error: {msg['error']}")
                        )
                    else:
                        future.set_result(msg.get("result", {}))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("Error in MCP Client read listener: %s", str(e))
        finally:
            self.is_connected = False
