from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus
from .mcp_protocol import MCPProtocol
from .a2a_protocol import A2AProtocol
from .acp_protocol import ACPProtocol
from .openai_assistants import OpenAIAssistantsProtocol
from .langchain_protocol import LangChainProtocol
from .autogen_protocol import AutoGenProtocol
from .websocket_protocol import WebSocketStreamProtocol
from .grpc_protocol import GRPCProtocol
from .mqtt_protocol import MQTTProtocol
from .graphql_protocol import GraphQLProtocol

ALL_PROTOCOLS = [
    MCPProtocol,
    A2AProtocol,
    ACPProtocol,
    OpenAIAssistantsProtocol,
    LangChainProtocol,
    AutoGenProtocol,
    WebSocketStreamProtocol,
    GRPCProtocol,
    MQTTProtocol,
    GraphQLProtocol,
]

PROTOCOL_DESCRIPTIONS = {
    "MCP":                "Model Context Protocol — connect AI to tools/files/databases (Anthropic)",
    "A2A":                "Agent-to-Agent — agent discovery and delegation (Google 2025)",
    "ACP":                "Agent Communication Protocol — REST-based agent communication (IBM/Linux Foundation)",
    "OpenAI-Assistants":  "Stateful agents with memory, file access, code execution (OpenAI)",
    "LangChain":          "Chain-based agents with tools and memory pipelines",
    "AutoGen":            "Multi-agent group conversations (Microsoft)",
    "WebSocket-Stream":   "Real-time token streaming via SSE/WebSocket",
    "gRPC":               "High-performance binary protocol for production AI systems",
    "MQTT":               "Lightweight pub/sub for IoT and edge AI agents",
    "GraphQL":            "Flexible query API — ask for exactly what you need",
}
