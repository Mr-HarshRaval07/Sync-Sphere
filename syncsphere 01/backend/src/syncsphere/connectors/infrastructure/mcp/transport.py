import asyncio
import json
import logging
import httpx
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any, List

logger = logging.getLogger("syncsphere.connectors.infrastructure.mcp.transport")

class MCPTransport(ABC):
    """Abstract interface defining the execution transport for MCP communications."""

    @abstractmethod
    async def start(self) -> None:
        """Starts the transport connection stream."""
        pass

    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Sends a JSON-RPC 2.0 message payload to the server."""
        pass

    @abstractmethod
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Awaits and returns a single JSON-RPC 2.0 message from the server."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Tears down the transport channel."""
        pass


class StdioTransport(MCPTransport):
    """
    Local transport that spawns an MCP server subprocess.
    Communicates via standard I/O (stdin/stdout) using newline-delimited JSON-RPC.
    """
    
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> None:
        self.command = command
        self.args = args
        self.env = env
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        logger.info("Spawning local MCP server process: %s %s", self.command, self.args)
        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.env
            )
            # Spawn task to dump stderr logs to prevent deadlock
            asyncio.create_task(self._read_stderr())
            logger.info("MCP server process started with PID: %d", self.process.pid)
        except Exception as e:
            logger.error("Failed to spawn MCP server process: %s", str(e))
            raise e

    async def _read_stderr(self) -> None:
        if not self.process or not self.process.stderr:
            return
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                logger.debug("[MCP Server Stderr] %s", line.decode().strip())
        except Exception:
            pass

    async def send_message(self, message: Dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise IOError("Transport process standard input is closed/offline.")
        payload = json.dumps(message) + "\n"
        self.process.stdin.write(payload.encode())
        await self.process.stdin.drain()

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        if not self.process or not self.process.stdout:
            raise IOError("Transport process standard output is closed/offline.")
        line = await self.process.stdout.readline()
        if not line:
            return None
        try:
            return json.loads(line.decode())
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON-RPC line from MCP server: %s", str(e))
            return None

    async def close(self) -> None:
        if self.process:
            logger.info("Terminating local MCP server process (PID: %d)", self.process.pid)
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass
            self.process = None


class SSETransport(MCPTransport):
    """
    Remote HTTP transport connecting to an MCP Server-Sent Events (SSE) stream endpoint.
    Sends messages via POST and receives streams via GET.
    """
    
    def __init__(self, sse_url: str) -> None:
        self.sse_url = sse_url
        self.client: Optional[httpx.AsyncClient] = None
        self.queue: asyncio.Queue = asyncio.Queue()
        self.stream_task: Optional[asyncio.Task] = None
        self.endpoint_url: Optional[str] = None # Received on initialization handshake

    async def start(self) -> None:
        logger.info("Connecting to remote SSE MCP Server at: %s", self.sse_url)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.stream_task = asyncio.create_task(self._read_sse_stream())

    async def _read_sse_stream(self) -> None:
        try:
            async with self.client.stream("GET", self.sse_url) as response:
                if response.status_code != 200:
                    logger.error("SSE stream connection failed with status: %d", response.status_code)
                    return
                
                # Read SSE event stream line-by-line
                async for line in response.iter_lines():
                    if line.startswith("event: endpoint"):
                        # Parse dynamic post url if supplied
                        pass
                    elif line.startswith("data:"):
                        data_payload = line[5:].strip()
                        try:
                            msg = json.loads(data_payload)
                            await self.queue.put(msg)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.error("Error reading remote SSE stream: %s", str(e))

    async def send_message(self, message: Dict[str, Any]) -> None:
        if not self.client:
            raise IOError("SSE Transport is offline.")
        # Post JSON-RPC messages back to the server
        url = self.endpoint_url or self.sse_url
        resp = await self.client.post(url, json=message)
        if resp.status_code not in (200, 202, 204):
            raise IOError(f"Failed to post JSON-RPC to SSE endpoint. HTTP status: {resp.status_code}")

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        # Await message from SSE stream queue
        return await self.queue.get()

    async def close(self) -> None:
        self.queue = asyncio.Queue()
        if self.stream_task:
            self.stream_task.cancel()
        if self.client:
            await self.client.aclose()
            self.client = None
