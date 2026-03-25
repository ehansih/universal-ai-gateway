import os
from .base import BaseAgent, AgentResponse


class ClaudeAgent(BaseAgent):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__("Claude", model)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            import httpx
            cert = os.environ.get("SSL_CERT_FILE")
            if cert:
                self._client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    http_client=httpx.Client(verify=cert)
                )
            else:
                self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def check_availability(self) -> bool:
        try:
            if not os.getenv("ANTHROPIC_API_KEY"):
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
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return AgentResponse(
                agent_name=self.name,
                model=self.model,
                content=response.content[0].text,
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
