import os
from .base import BaseAgent, AgentResponse


class GeminiAgent(BaseAgent):
    def __init__(self, model: str = "gemini-1.5-pro"):
        super().__init__("Gemini", model)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self._client = genai.GenerativeModel(self.model)
        return self._client

    def check_availability(self) -> bool:
        try:
            if not os.getenv("GEMINI_API_KEY"):
                return False
            self._get_client()
            self.available = True
            return True
        except Exception:
            self.available = False
            return False

    def ask(self, prompt: str) -> AgentResponse:
        try:
            client = self._get_client()
            response = client.generate_content(prompt)
            return AgentResponse(
                agent_name=self.name,
                model=self.model,
                content=response.text,
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
