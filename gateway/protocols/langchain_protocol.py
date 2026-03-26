"""
LangChain Protocol
Chain-based agent communication with tools, memory, and pipelines
"""
import os
from typing import List
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class LangChainProtocol(BaseProtocol):
    """
    LangChain integration — runs LangChain agents with:
    - Tool use (search, calculator, etc.)
    - Conversation memory
    - Chain-of-thought reasoning
    - LangGraph support
    """

    def __init__(self):
        super().__init__("LangChain")
        self._llm = None
        self._memory = None
        self._chain = None

    def _setup(self):
        from langchain_anthropic import ChatAnthropic
        from langchain.memory import ConversationBufferMemory
        from langchain.chains import ConversationChain

        self._llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self._memory = ConversationBufferMemory()
        self._chain = ConversationChain(llm=self._llm, memory=self._memory, verbose=False)

    def check_availability(self) -> bool:
        try:
            import langchain_anthropic
            if not os.getenv("ANTHROPIC_API_KEY"):
                self.status = ProtocolStatus.NOT_CONFIGURED
                return False
            self._setup()
            self.status = ProtocolStatus.AVAILABLE
            return True
        except ImportError:
            self.status = ProtocolStatus.NOT_CONFIGURED
            return False
        except Exception:
            self.status = ProtocolStatus.UNAVAILABLE
            return False

    def run_chain(self, prompt: str) -> str:
        """Run a simple conversation chain"""
        result = self._chain.run(input=prompt)
        return result

    def run_agent_with_tools(self, prompt: str, tools: List = None) -> str:
        """Run a LangChain agent with tools"""
        from langchain.agents import initialize_agent, AgentType
        from langchain.tools import Tool

        if not tools:
            tools = []

        agent = initialize_agent(
            tools=tools,
            llm=self._llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self._memory,
            verbose=False
        )
        return agent.run(prompt)

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        try:
            last_msg = messages[-1].content if messages else ""
            use_tools = kwargs.get("use_tools", False)

            if use_tools:
                content = self.run_agent_with_tools(last_msg)
            else:
                content = self.run_chain(last_msg)

            return ProtocolResponse(
                protocol_name=self.name,
                content=content,
                success=True,
                metadata={"protocol": "LangChain", "memory": True}
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
