"""
ACP — Agent Communication Protocol (IBM / Linux Foundation BeeAI, 2025)
REST-based protocol for agent-to-agent communication
Spec: https://agentcommunicationprotocol.dev
"""
import uuid
import requests
import os
from typing import List, Dict
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class ACPProtocol(BaseProtocol):
    """
    ACP Client — communicates with ACP-compliant agents
    Uses REST + multipart for rich message passing
    """

    def __init__(self, server_url: str = None):
        super().__init__("ACP")
        self.server_url = server_url or os.getenv("ACP_SERVER_URL", "http://localhost:8080")
        self.agent_id = None

    def check_availability(self) -> bool:
        try:
            r = requests.get(f"{self.server_url}/agents", timeout=5)
            if r.status_code == 200:
                agents = r.json()
                if agents:
                    self.agent_id = agents[0].get("agent_id")
                self.status = ProtocolStatus.AVAILABLE
                return True
        except Exception:
            pass
        self.status = ProtocolStatus.UNAVAILABLE
        return False

    def list_agents(self) -> List[Dict]:
        """Discover available ACP agents"""
        try:
            r = requests.get(f"{self.server_url}/agents", timeout=5)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def create_run(self, agent_id: str, message: str) -> Dict:
        """Create a new run (task) on an ACP agent"""
        try:
            r = requests.post(
                f"{self.server_url}/agents/{agent_id}/runs",
                json={
                    "messages": [{
                        "role": "user",
                        "parts": [{"content_type": "text/plain", "content": message}]
                    }]
                },
                timeout=30
            )
            return r.json() if r.status_code in (200, 201) else {"error": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_run_result(self, agent_id: str, run_id: str) -> Dict:
        """Get the result of a completed run"""
        try:
            r = requests.get(
                f"{self.server_url}/agents/{agent_id}/runs/{run_id}",
                timeout=10
            )
            return r.json() if r.status_code == 200 else {"error": r.text}
        except Exception as e:
            return {"error": str(e)}

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        last_msg = messages[-1].content if messages else ""
        agent_id = kwargs.get("agent_id", self.agent_id)

        if not agent_id:
            return ProtocolResponse(
                protocol_name=self.name,
                content="ACP: No agent_id configured. Set ACP_SERVER_URL and ensure agents are registered.",
                success=False,
                error="No agent_id"
            )

        result = self.create_run(agent_id, last_msg)

        if "error" in result:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=result["error"]
            )

        # Extract content from ACP response
        output_msgs = result.get("output", {}).get("messages", [])
        content = ""
        for msg in output_msgs:
            for part in msg.get("parts", []):
                content += part.get("content", "")

        return ProtocolResponse(
            protocol_name=self.name,
            content=content or str(result),
            success=True,
            metadata={"run_id": result.get("run_id"), "protocol": "ACP"}
        )
