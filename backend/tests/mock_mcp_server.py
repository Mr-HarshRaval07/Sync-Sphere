import asyncio
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger("tests.mock_mcp_server")

class MockMCPServer:
    """
    Mock MCP Server speaking JSON-RPC 2.0.
    Simulates integrations with Slack, Jira, GitHub, Gmail, and Google Sheets.
    """
    
    def __init__(self) -> None:
        self.tools = {
            "slack": [
                {
                    "name": "slack_post_message",
                    "description": "Posts a message to a Slack channel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "channel": {"type": "string"},
                            "message": {"type": "string"}
                        },
                        "required": ["channel", "message"]
                    }
                }
            ],
            "jira": [
                {
                    "name": "jira_create_issue",
                    "description": "Creates a Jira issue ticket",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string"},
                            "summary": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["project", "summary"]
                    }
                }
            ],
            "github": [
                {
                    "name": "github_create_branch",
                    "description": "Creates a branch in a repository",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "repo": {"type": "string"},
                            "branch_name": {"type": "string"}
                        },
                        "required": ["repo", "branch_name"]
                    }
                }
            ]
        }

    def handle_message(self, message: Dict[str, Any], connector_type: str) -> Dict[str, Any]:
        """Processes JSON-RPC 2.0 request and returns a JSON-RPC 2.0 response."""
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "serverInfo": {"name": f"Mock {connector_type} Server", "version": "1.0.0"}
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": self.tools.get(connector_type, [])
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Execute mock tool logic
            logger.info("Executing mock tool: %s with args: %s", tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Successfully executed tool: {tool_name} with params {arguments}"
                        }
                    ],
                    "isError": False
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found."
                }
            }
