"""
WebSocket Streaming Protocol
Real-time token-by-token streaming from AI agents
"""
import os
import json
from typing import List, Generator
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class WebSocketStreamProtocol(BaseProtocol):
    """
    Streaming protocol — streams tokens in real-time using:
    - Server-Sent Events (SSE) for HTTP streaming
    - WebSocket for bidirectional streaming
    - Anthropic streaming API
    - OpenAI streaming API
    """

    def __init__(self):
        super().__init__("WebSocket-Stream")
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic(self):
        if not self._anthropic_client:
            import anthropic, httpx
            cert = os.environ.get("SSL_CERT_FILE")
            kwargs = {"api_key": os.getenv("ANTHROPIC_API_KEY")}
            if cert:
                kwargs["http_client"] = httpx.Client(verify=cert)
            self._anthropic_client = anthropic.Anthropic(**kwargs)
        return self._anthropic_client

    def _get_openai(self):
        if not self._openai_client:
            from openai import OpenAI
            import httpx
            cert = os.environ.get("SSL_CERT_FILE")
            kwargs = {"api_key": os.getenv("OPENAI_API_KEY")}
            if cert:
                kwargs["http_client"] = httpx.Client(verify=cert)
            self._openai_client = OpenAI(**kwargs)
        return self._openai_client

    def check_availability(self) -> bool:
        has_key = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))
        self.status = ProtocolStatus.AVAILABLE if has_key else ProtocolStatus.NOT_CONFIGURED
        return has_key

    def stream_claude(self, prompt: str) -> Generator[str, None, None]:
        """Stream tokens from Claude"""
        client = self._get_anthropic()
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    def stream_openai(self, prompt: str) -> Generator[str, None, None]:
        """Stream tokens from OpenAI"""
        client = self._get_openai()
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def stream_sse(self, prompt: str, provider: str = "claude") -> Generator[str, None, None]:
        """
        Generator for Server-Sent Events streaming
        Yields SSE-formatted chunks
        """
        try:
            streamer = self.stream_claude if provider == "claude" else self.stream_openai
            for token in streamer(prompt):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        """Non-streaming send (collects full stream)"""
        last_msg = messages[-1].content if messages else ""
        provider = kwargs.get("provider", "claude")
        try:
            streamer = self.stream_claude if provider == "claude" else self.stream_openai
            full = "".join(streamer(last_msg))
            return ProtocolResponse(
                protocol_name=self.name,
                content=full,
                success=True,
                streaming=True,
                metadata={"provider": provider, "protocol": "WebSocket-Stream"}
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
