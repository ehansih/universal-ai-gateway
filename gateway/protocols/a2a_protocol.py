"""
A2A — Agent-to-Agent Protocol (Google, 2025)
Enables AI agents to discover, communicate, and delegate tasks to each other
Spec: https://google.github.io/A2A
"""
import json
import uuid
import requests
import os
from typing import List, Dict, Optional
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class AgentCard:
    """
    A2A Agent Card — describes an agent's capabilities, skills, and endpoint
    Like a business card for AI agents
    """
    def __init__(self, name: str, url: str, description: str, skills: List[str]):
        self.name = name
        self.url = url
        self.description = description
        self.skills = skills
        self.agent_id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "version": "1.0",
            "capabilities": {
                "streaming": False,
                "pushNotifications": False
            },
            "skills": [
                {"id": s.lower().replace(" ", "_"), "name": s}
                for s in self.skills
            ]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class A2ATask:
    """Represents a task sent between A2A agents"""
    def __init__(self, message: str, session_id: str = None):
        self.task_id = str(uuid.uuid4())
        self.session_id = session_id or str(uuid.uuid4())
        self.message = message
        self.status = "submitted"

    def to_dict(self) -> Dict:
        return {
            "id": self.task_id,
            "sessionId": self.session_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": self.message}]
            }
        }


class A2AProtocol(BaseProtocol):
    """
    A2A Protocol Client
    Discovers remote agents via /.well-known/agent.json
    Sends tasks and receives responses
    """

    def __init__(self):
        super().__init__("A2A")
        self.known_agents: List[AgentCard] = []
        self.my_card = AgentCard(
            name="Universal AI Gateway",
            url=os.getenv("GATEWAY_URL", "http://localhost:5000"),
            description="Universal gateway supporting all AI protocols",
            skills=["general-qa", "code", "math", "creative", "collaboration"]
        )

    def check_availability(self) -> bool:
        # A2A is always available as we host our own agent card
        self.status = ProtocolStatus.AVAILABLE
        return True

    def discover_agent(self, base_url: str) -> Optional[AgentCard]:
        """
        Discover an A2A agent by fetching its agent card
        from /.well-known/agent.json
        """
        try:
            url = f"{base_url.rstrip('/')}/.well-known/agent.json"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            card = AgentCard(
                name=data.get("name", "Unknown"),
                url=base_url,
                description=data.get("description", ""),
                skills=[s.get("name", "") for s in data.get("skills", [])]
            )
            self.known_agents.append(card)
            return card
        except Exception as e:
            return None

    def send_task(self, agent: AgentCard, message: str) -> Dict:
        """Send a task to a remote A2A agent"""
        task = A2ATask(message)
        try:
            r = requests.post(
                f"{agent.url.rstrip('/')}/tasks/send",
                json=task.to_dict(),
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def get_my_agent_card(self) -> str:
        """Returns this gateway's agent card JSON (for /.well-known/agent.json)"""
        return self.my_card.to_json()

    def find_best_agent(self, task: str) -> Optional[AgentCard]:
        """Find the best known agent for a given task"""
        task_lower = task.lower()
        for agent in self.known_agents:
            for skill in agent.skills:
                if skill.lower() in task_lower:
                    return agent
        return self.known_agents[0] if self.known_agents else None

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        last_msg = messages[-1].content if messages else ""
        agent_url = kwargs.get("agent_url")

        if agent_url:
            agent = self.discover_agent(agent_url)
            if agent:
                result = self.send_task(agent, last_msg)
                content = result.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", str(result))
                return ProtocolResponse(
                    protocol_name=self.name,
                    content=content,
                    success="error" not in result,
                    metadata={"agent": agent.name, "protocol": "A2A"}
                )

        best = self.find_best_agent(last_msg)
        if best:
            result = self.send_task(best, last_msg)
            content = result.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", str(result))
            return ProtocolResponse(
                protocol_name=self.name,
                content=content,
                success="error" not in result,
                metadata={"agent": best.name}
            )

        return ProtocolResponse(
            protocol_name=self.name,
            content=f"A2A ready. My agent card:\n{self.get_my_agent_card()}\nNo remote agents discovered yet. Use discover_agent(url) to add agents.",
            success=True,
            metadata={"known_agents": len(self.known_agents)}
        )
