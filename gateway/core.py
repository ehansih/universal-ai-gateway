"""
Universal AI Gateway — core
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

from .agents import ClaudeAgent, OpenAIAgent, GeminiAgent, OllamaAgent, BaseAgent
from .protocols import (
    MCPProtocol, A2AProtocol, ACPProtocol, OpenAIAssistantsProtocol,
    LangChainProtocol, AutoGenProtocol, WebSocketStreamProtocol,
    GRPCProtocol, MQTTProtocol, GraphQLProtocol, PROTOCOL_DESCRIPTIONS
)
from .router import pick_best_agent, detect_task_type
from .collaborator import collaborate
from .memory import ConversationMemory
from .tools import ToolRegistry

load_dotenv()

# SSL cert for Zscaler/corporate proxies
cert = os.path.join(os.path.dirname(os.path.dirname(__file__)), "combined-certs.pem")
if os.path.exists(cert):
    os.environ["SSL_CERT_FILE"] = cert
    os.environ["REQUESTS_CA_BUNDLE"] = cert


class UniversalAIGateway:
    def __init__(self):
        # AI Agents
        self.agents: List[BaseAgent] = [
            ClaudeAgent(),
            OpenAIAgent(),
            GeminiAgent(),
            OllamaAgent("llama3"),
        ]

        # Protocols
        self.protocols = {
            "mcp":        MCPProtocol(),
            "a2a":        A2AProtocol(),
            "acp":        ACPProtocol(),
            "assistants": OpenAIAssistantsProtocol(),
            "langchain":  LangChainProtocol(),
            "autogen":    AutoGenProtocol(),
            "stream":     WebSocketStreamProtocol(),
            "grpc":       GRPCProtocol(),
            "mqtt":       MQTTProtocol(),
            "graphql":    GraphQLProtocol(),
        }

        # Memory & Tools
        self.memory   = ConversationMemory()
        self.tools     = ToolRegistry()

        self._check_agents()
        self._check_protocols()

    def _check_agents(self):
        print("Checking agents...")
        for agent in self.agents:
            agent.check_availability()
            print(f"  {agent}")

    def _check_protocols(self):
        print("Checking protocols...")
        for name, proto in self.protocols.items():
            proto.check_availability()
            print(f"  {proto}")

    @property
    def available_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents if a.available]

    def ask(self, question: str, mode: str = "auto", session_id: str = "default") -> dict:
        """
        Modes:
          auto        — smart route to best agent
          collaborate — MACP multi-agent debate
          all         — ask all agents
          stream      — streaming response
          mcp/a2a/acp/assistants/langchain/autogen/grpc/mqtt/graphql — specific protocol
          claude/chatgpt/gemini/ollama — specific agent
        """
        available = self.available_agents

        if not available and mode not in self.protocols:
            return {"error": "No AI agents available. Check your API keys."}

        task_type = detect_task_type(question)

        # Add tool results to context if relevant
        tool_results = self.tools.detect_and_run(question)
        if tool_results:
            tool_context = "\n".join(f"[{k}]: {v}" for k, v in tool_results.items())
            question = f"{question}\n\nTool results:\n{tool_context}"

        # Save to memory
        self.memory.add(session_id, "user", question)

        result = {}

        # Protocol mode
        if mode in self.protocols:
            proto = self.protocols[mode]
            from .protocols.base_protocol import ProtocolMessage, ProtocolStatus
            msgs = [ProtocolMessage(role="user", content=question)]
            resp = proto.send(msgs)
            result = {
                "mode": f"protocol:{mode}",
                "protocol": mode,
                "answer": resp.content,
                "success": resp.success,
                "error": resp.error,
                "metadata": resp.metadata
            }

        elif mode == "auto":
            best = pick_best_agent(question, available)
            resp = best.ask(question)
            result = {
                "mode": "auto",
                "task_type": task_type,
                "agent": best.name,
                "answer": resp.content,
                "success": resp.success,
                "error": resp.error,
                "tools_used": list(tool_results.keys()) if tool_results else []
            }

        elif mode == "collaborate":
            r = collaborate(question, available)
            r["task_type"] = task_type
            r["tools_used"] = list(tool_results.keys()) if tool_results else []
            result = r

        elif mode == "all":
            responses = []
            for agent in available:
                resp = agent.ask(question)
                responses.append({
                    "agent": agent.name,
                    "model": agent.model,
                    "answer": resp.content,
                    "success": resp.success
                })
            result = {"mode": "all", "task_type": task_type, "responses": responses}

        else:
            # Specific agent by name
            target = next((a for a in available if mode.lower() in a.name.lower()), None)
            if not target:
                return {"error": f"Agent '{mode}' not found or unavailable"}
            resp = target.ask(question)
            result = {
                "mode": "specific",
                "agent": target.name,
                "answer": resp.content,
                "success": resp.success
            }

        # Save answer to memory
        answer = result.get("answer") or result.get("final", "")
        self.memory.add(session_id, "assistant", answer, agent=result.get("agent", ""), protocol=mode)

        return result

    def status(self) -> dict:
        return {
            "agents": [
                {"name": a.name, "model": a.model, "available": a.available}
                for a in self.agents
            ],
            "protocols": [
                {
                    "name": p.name,
                    "key": k,
                    "status": p.status.value,
                    "description": PROTOCOL_DESCRIPTIONS.get(p.name, "")
                }
                for k, p in self.protocols.items()
            ],
            "tools": self.tools.list_tools(),
            "total_agents": len(self.agents),
            "available_agents": len(self.available_agents),
            "total_protocols": len(self.protocols),
        }
