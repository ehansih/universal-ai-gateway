"""
Conversation Memory — persistent chat history across sessions
"""
import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class Turn:
    role: str
    content: str
    agent: str = ""
    protocol: str = ""
    timestamp: float = field(default_factory=time.time)


class ConversationMemory:
    """
    Stores conversation history in a JSON file
    Supports multiple sessions
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "conversations.json"
        )
        self._sessions: Dict[str, List[Turn]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    raw = json.load(f)
                    for sid, turns in raw.items():
                        self._sessions[sid] = [Turn(**t) for t in turns]
            except Exception:
                self._sessions = {}

    def _save(self):
        with open(self.storage_path, "w") as f:
            json.dump(
                {sid: [asdict(t) for t in turns] for sid, turns in self._sessions.items()},
                f, indent=2
            )

    def add(self, session_id: str, role: str, content: str, agent: str = "", protocol: str = ""):
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        self._sessions[session_id].append(Turn(role, content, agent, protocol))
        self._save()

    def get(self, session_id: str) -> List[Turn]:
        return self._sessions.get(session_id, [])

    def get_context(self, session_id: str, last_n: int = 10) -> str:
        """Returns last N turns as formatted string for AI context"""
        turns = self.get(session_id)[-last_n:]
        return "\n".join(f"{t.role.upper()}: {t.content}" for t in turns)

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()

    def clear_all(self):
        self._sessions = {}
        self._save()
