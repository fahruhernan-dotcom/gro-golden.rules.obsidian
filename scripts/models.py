"""
Normalized Data Model for Antigravity Chat History and Obsidian Knowledge Management.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ChatMessage:
    conversation_id: str
    workspace_id: str
    timestamp: str          # ISO-8601 string
    role: str               # 'user', 'assistant', 'system', 'tool'
    step_type: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(**data)


@dataclass
class ChatSession:
    conversation_id: str
    workspace_id: str
    workspace_name: str
    title: str
    started_at: str         # ISO-8601 string
    ended_at: str           # ISO-8601 string
    messages: List[ChatMessage] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["messages"] = [m.to_dict() if isinstance(m, ChatMessage) else m for m in self.messages]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        raw_msgs = data.pop("messages", [])
        messages = [ChatMessage.from_dict(m) if isinstance(m, dict) else m for m in raw_msgs]
        return cls(messages=messages, **data)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    path: Optional[str] = None
    session_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workspace":
        return cls(**data)
