import os
from .base import BaseAgent, AgentResponse


class OpenAIAgent(BaseAgent):
    def __init__(self, model: str = "gpt-4o"):
        super().__init__("ChatGPT", model)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            import httpx
            cert = os.environ.get("SSL_CERT_FILE")
            if cert:
                self._client = OpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    http_client=httpx.Client(verify=cert)
                )
            else:
                self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    def check_availability(self) -> bool:
        try:
            if not os.getenv("OPENAI_API_KEY"):
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
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024
            )
            return AgentResponse(
                agent_name=self.name,
                model=self.model,
                content=response.choices[0].message.content,
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
