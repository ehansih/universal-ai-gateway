"""
MCP — Model Context Protocol (Anthropic)
Allows AI models to connect to external tools, files, databases via JSON-RPC 2.0
Spec: https://modelcontextprotocol.io
"""
import json
import os
import requests
from typing import List, Dict, Any
from .base_protocol import BaseProtocol, BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class MCPTool:
    """Represents a tool exposed by an MCP server"""
    def __init__(self, name: str, description: str, input_schema: Dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


class MCPProtocol(BaseProtocol):
    """
    MCP Client — connects to any MCP server (HTTP/SSE or stdio)
    MCP servers expose tools, resources, and prompts to AI agents
    """

    def __init__(self, server_url: str = None):
        super().__init__("MCP")
        self.server_url = server_url or os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.tools: List[MCPTool] = []
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _jsonrpc(self, method: str, params: Dict = None) -> Dict:
        """Send a JSON-RPC 2.0 request to the MCP server"""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        response = requests.post(
            f"{self.server_url}/mcp",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def check_availability(self) -> bool:
        try:
            result = self._jsonrpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "clientInfo": {"name": "universal-ai-gateway", "version": "1.0"}
            })
            if "result" in result:
                self.status = ProtocolStatus.AVAILABLE
                self._discover_tools()
                return True
        except Exception:
            pass
        self.status = ProtocolStatus.UNAVAILABLE
        return False

    def _discover_tools(self):
        """Auto-discover tools from MCP server"""
        try:
            result = self._jsonrpc("tools/list")
            tools_data = result.get("result", {}).get("tools", [])
            self.tools = [
                MCPTool(t["name"], t.get("description", ""), t.get("inputSchema", {}))
                for t in tools_data
            ]
        except Exception:
            pass

    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a specific tool on the MCP server"""
        result = self._jsonrpc("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return result.get("result", {})

    def read_resource(self, uri: str) -> str:
        """Read a resource from the MCP server (file, DB, etc.)"""
        result = self._jsonrpc("resources/read", {"uri": uri})
        contents = result.get("result", {}).get("contents", [])
        return "\n".join(c.get("text", "") for c in contents)

    def get_tools_description(self) -> str:
        """Returns human-readable list of available tools"""
        if not self.tools:
            return "No tools available"
        return "\n".join(f"- {t.name}: {t.description}" for t in self.tools)

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        """
        Send messages using MCP — executes tools based on last message
        In a real scenario, the AI decides which tool to call
        """
        try:
            last_msg = messages[-1].content if messages else ""

            # Check if any tool matches the request
            for tool in self.tools:
                if tool.name.lower() in last_msg.lower():
                    result = self.call_tool(tool.name, {"query": last_msg})
                    return ProtocolResponse(
                        protocol_name=self.name,
                        content=json.dumps(result, indent=2),
                        success=True,
                        metadata={"tool_used": tool.name, "protocol": "MCP"}
                    )

            return ProtocolResponse(
                protocol_name=self.name,
                content=f"MCP server connected. Available tools: {self.get_tools_description()}",
                success=True
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
