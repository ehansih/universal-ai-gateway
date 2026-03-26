"""
OpenAI Assistants API Protocol
Stateful agents with persistent memory, file access, and tool use
"""
import os
import time
from typing import List
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class OpenAIAssistantsProtocol(BaseProtocol):
    """
    OpenAI Assistants API — creates persistent AI agents with:
    - Long-term memory (threads)
    - File reading (file_search)
    - Code execution (code_interpreter)
    - Function calling
    """

    def __init__(self):
        super().__init__("OpenAI-Assistants")
        self._client = None
        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
        self.thread_id = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            import httpx
            cert = os.environ.get("SSL_CERT_FILE")
            kwargs = {"api_key": os.getenv("OPENAI_API_KEY")}
            if cert:
                kwargs["http_client"] = httpx.Client(verify=cert)
            self._client = OpenAI(**kwargs)
        return self._client

    def check_availability(self) -> bool:
        try:
            if not os.getenv("OPENAI_API_KEY"):
                self.status = ProtocolStatus.NOT_CONFIGURED
                return False
            client = self._get_client()
            if not self.assistant_id:
                # Create a default assistant
                assistant = client.beta.assistants.create(
                    name="Universal Gateway Assistant",
                    instructions="You are a helpful AI assistant.",
                    model="gpt-4o",
                    tools=[{"type": "code_interpreter"}, {"type": "file_search"}]
                )
                self.assistant_id = assistant.id
            self.status = ProtocolStatus.AVAILABLE
            return True
        except Exception:
            self.status = ProtocolStatus.UNAVAILABLE
            return False

    def new_thread(self) -> str:
        """Start a new conversation thread"""
        client = self._get_client()
        thread = client.beta.threads.create()
        self.thread_id = thread.id
        return thread.id

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        try:
            client = self._get_client()

            # Create thread if none exists
            if not self.thread_id:
                self.new_thread()

            # Add messages to thread
            for msg in messages:
                if msg.role == "user":
                    client.beta.threads.messages.create(
                        thread_id=self.thread_id,
                        role="user",
                        content=msg.content
                    )

            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )

            # Poll until complete
            max_wait = 60
            waited = 0
            while run.status in ("queued", "in_progress") and waited < max_wait:
                time.sleep(1)
                waited += 1
                run = client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )

            if run.status != "completed":
                return ProtocolResponse(
                    protocol_name=self.name,
                    content="",
                    success=False,
                    error=f"Run ended with status: {run.status}"
                )

            # Get latest message
            msgs = client.beta.threads.messages.list(thread_id=self.thread_id)
            latest = msgs.data[0].content[0].text.value

            return ProtocolResponse(
                protocol_name=self.name,
                content=latest,
                success=True,
                metadata={
                    "thread_id": self.thread_id,
                    "run_id": run.id,
                    "protocol": "OpenAI-Assistants"
                }
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
