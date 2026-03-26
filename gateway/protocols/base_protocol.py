"""
Base class for all AI communication protocols
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ProtocolStatus(Enum):
    AVAILABLE    = "available"
    UNAVAILABLE  = "unavailable"
    NOT_CONFIGURED = "not_configured"


@dataclass
class ProtocolMessage:
    role: str           # user / assistant / system / agent
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtocolResponse:
    protocol_name: str
    content: str
    success: bool
    streaming: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseProtocol(ABC):
    def __init__(self, name: str):
        self.name = name
        self.status = ProtocolStatus.UNAVAILABLE

    @abstractmethod
    def check_availability(self) -> bool:
        pass

    @abstractmethod
    def send(self, messages: List[ProtocolMessage], **kwargs) -> ProtocolResponse:
        pass

    def __repr__(self):
        icon = "✓" if self.status == ProtocolStatus.AVAILABLE else "✗"
        return f"[{icon}] Protocol:{self.name} ({self.status.value})"
