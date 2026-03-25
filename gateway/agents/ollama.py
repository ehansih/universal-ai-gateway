import os
import requests
from .base import BaseAgent, AgentResponse

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


class OllamaAgent(BaseAgent):
    def __init__(self, model: str = "llama3"):
        super().__init__(f"Ollama/{model}", model)

    def check_availability(self) -> bool:
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                self.available = any(self.model in m for m in models)
                return self.available
        except Exception:
            pass
        self.available = False
        return False

    def ask(self, prompt: str) -> AgentResponse:
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120
            )
            r.raise_for_status()
            return AgentResponse(
                agent_name=self.name,
                model=self.model,
                content=r.json().get("response", ""),
                success=True
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                model=self.model,
                content="",
                success=False,
                error=str(e)
            )
