"""
Universal AI Gateway — core
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
from .agents import ClaudeAgent, OpenAIAgent, GeminiAgent, OllamaAgent, BaseAgent
from .router import pick_best_agent, detect_task_type
from .collaborator import collaborate

load_dotenv()

# Set SSL cert if available
cert = os.path.join(os.path.dirname(os.path.dirname(__file__)), "combined-certs.pem")
if os.path.exists(cert):
    os.environ["SSL_CERT_FILE"] = cert
    os.environ["REQUESTS_CA_BUNDLE"] = cert


class UniversalAIGateway:
    def __init__(self):
        self.agents: List[BaseAgent] = [
            ClaudeAgent(),
            OpenAIAgent(),
            GeminiAgent(),
            OllamaAgent("llama3"),
        ]
        self._check_agents()

    def _check_agents(self):
        print("Checking available agents...")
        for agent in self.agents:
            agent.check_availability()
            print(f"  {agent}")

    @property
    def available_agents(self) -> List[BaseAgent]:
        return [a for a in self.agents if a.available]

    def ask(self, question: str, mode: str = "auto") -> dict:
        """
        Modes:
          auto        — smart route to best agent
          collaborate — all available agents debate (MACP)
          all         — ask all agents, return all answers
          <agent>     — ask specific agent (claude/chatgpt/gemini/ollama)
        """
        available = self.available_agents

        if not available:
            return {"error": "No AI agents are available. Check your API keys."}

        task_type = detect_task_type(question)

        if mode == "auto":
            best = pick_best_agent(question, available)
            resp = best.ask(question)
            return {
                "mode": "auto",
                "task_type": task_type,
                "agent": best.name,
                "answer": resp.content,
                "success": resp.success,
                "error": resp.error
            }

        elif mode == "collaborate":
            result = collaborate(question, available)
            result["task_type"] = task_type
            return result

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
            return {"mode": "all", "task_type": task_type, "responses": responses}

        else:
            # specific agent by name
            target = next((a for a in available if mode.lower() in a.name.lower()), None)
            if not target:
                return {"error": f"Agent '{mode}' not found or not available"}
            resp = target.ask(question)
            return {
                "mode": "specific",
                "agent": target.name,
                "answer": resp.content,
                "success": resp.success
            }

    def status(self) -> dict:
        return {
            "total_agents": len(self.agents),
            "available": len(self.available_agents),
            "agents": [
                {"name": a.name, "model": a.model, "available": a.available}
                for a in self.agents
            ]
        }
