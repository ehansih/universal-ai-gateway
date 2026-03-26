"""
AutoGen Protocol (Microsoft)
Multi-agent conversations where agents autonomously collaborate
"""
import os
from typing import List, Dict
from .base_protocol import BaseProtocol, ProtocolMessage, ProtocolResponse, ProtocolStatus


class AutoGenProtocol(BaseProtocol):
    """
    AutoGen integration — runs multi-agent conversations with:
    - AssistantAgent: AI-powered agents
    - UserProxyAgent: Executes code and acts as human proxy
    - GroupChat: Multiple agents discussing in rounds
    """

    def __init__(self):
        super().__init__("AutoGen")
        self._config = None

    def _get_config(self) -> List[Dict]:
        return [{
            "model": "claude-sonnet-4-6",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "api_type": "anthropic"
        }]

    def check_availability(self) -> bool:
        try:
            import autogen
            if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
                self.status = ProtocolStatus.NOT_CONFIGURED
                return False
            self._config = self._get_config()
            self.status = ProtocolStatus.AVAILABLE
            return True
        except ImportError:
            self.status = ProtocolStatus.NOT_CONFIGURED
            return False
        except Exception:
            self.status = ProtocolStatus.UNAVAILABLE
            return False

    def run_two_agent_chat(self, task: str) -> str:
        """Run a two-agent chat: Assistant + UserProxy"""
        import autogen

        assistant = autogen.AssistantAgent(
            name="assistant",
            llm_config={"config_list": self._config},
            system_message="You are a helpful AI assistant. Be concise."
        )

        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
            code_execution_config=False
        )

        user_proxy.initiate_chat(assistant, message=task)

        # Extract last assistant message
        messages = assistant.chat_messages.get(user_proxy, [])
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return "No response generated"

    def run_group_chat(self, task: str, num_agents: int = 3) -> str:
        """Run a group chat with multiple specialized agents"""
        import autogen

        agents = []
        roles = ["Researcher", "Critic", "Synthesizer"][:num_agents]

        for role in roles:
            agent = autogen.AssistantAgent(
                name=role,
                llm_config={"config_list": self._config},
                system_message=f"You are a {role}. {role}-specific instructions here."
            )
            agents.append(agent)

        user_proxy = autogen.UserProxyAgent(
            name="user",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )

        group_chat = autogen.GroupChat(agents=agents + [user_proxy], messages=[], max_round=6)
        manager = autogen.GroupChatManager(groupchat=group_chat, llm_config={"config_list": self._config})

        user_proxy.initiate_chat(manager, message=task)

        last_msgs = group_chat.messages[-3:]
        return "\n\n".join(f"[{m.get('name')}]: {m.get('content', '')}" for m in last_msgs)

    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        try:
            last_msg = messages[-1].content if messages else ""
            mode = kwargs.get("autogen_mode", "two_agent")

            if mode == "group":
                content = self.run_group_chat(last_msg)
            else:
                content = self.run_two_agent_chat(last_msg)

            return ProtocolResponse(
                protocol_name=self.name,
                content=content,
                success=True,
                metadata={"protocol": "AutoGen", "mode": mode}
            )
        except Exception as e:
            return ProtocolResponse(
                protocol_name=self.name,
                content="",
                success=False,
                error=str(e)
            )
