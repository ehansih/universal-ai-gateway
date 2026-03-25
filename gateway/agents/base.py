from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentResponse:
    agent_name: str
    model: str
    content: str
    success: bool
    error: Optional[str] = None
    confidence: float = 1.0


class BaseAgent(ABC):
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.available = False

    @abstractmethod
    def ask(self, prompt: str) -> AgentResponse:
        pass

    @abstractmethod
    def check_availability(self) -> bool:
        pass

    def __repr__(self):
        status = "✓" if self.available else "✗"
        return f"[{status}] {self.name} ({self.model})"
