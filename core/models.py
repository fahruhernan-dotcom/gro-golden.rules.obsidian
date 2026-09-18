"""
Canonical Data Models for Persistent Obsidian Memory System.
Defines agent-agnostic representations for chat sessions, messages, reports, and search results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ChatMessage:
    conversation_id: str
    timestamp: str
    role: str
    step_type: Any
    content: str
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "workspace_id": self.workspace_id,
            "timestamp": self.timestamp,
            "role": self.role,
            "step_type": self.step_type,
            "content": self.content,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            conversation_id=data.get("conversation_id", ""),
            workspace_id=data.get("workspace_id"),
            timestamp=data.get("timestamp", ""),
            role=data.get("role", "assistant"),
            step_type=data.get("step_type", 0),
            content=data.get("content", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class ChatSession:
    conversation_id: str
    workspace_id: str
    workspace_name: str
    title: str
    started_at: str
    ended_at: str
    part: int = 1
    total_parts: int = 1
    prev_part: Optional[str] = None
    next_part: Optional[str] = None
    concepts: List[str] = field(default_factory=list)
    messages: List[ChatMessage] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace_name,
            "title": self.title,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "part": self.part,
            "total_parts": self.total_parts,
            "prev_part": self.prev_part,
            "next_part": self.next_part,
            "concepts": self.concepts,
            "messages": [m.to_dict() for m in self.messages],
            "affected_files": self.affected_files,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        msgs = [ChatMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data.get("conversation_id", ""),
            workspace_id=data.get("workspace_id", ""),
            workspace_name=data.get("workspace_name", "Unknown Workspace"),
            title=data.get("title", "Diskusi Antigravity"),
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
            part=data.get("part", 1),
            total_parts=data.get("total_parts", 1),
            prev_part=data.get("prev_part"),
            next_part=data.get("next_part"),
            concepts=data.get("concepts", []),
            messages=msgs,
            affected_files=data.get("affected_files", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class Workspace:
    workspace_id: str
    name: str
    path: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryReport:
    root: str
    exists: bool
    databases: List[str] = field(default_factory=list)
    wal_shm_files: List[str] = field(default_factory=list)
    json_files: List[str] = field(default_factory=list)
    jsonl_files: List[str] = field(default_factory=list)
    proto_files: List[str] = field(default_factory=list)
    conversation_stores: List[str] = field(default_factory=list)
    workspace_metadata_sources: List[str] = field(default_factory=list)
    total_files_scanned: int = 0
    newest_timestamp: Optional[str] = None
    oldest_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "exists": self.exists,
            "databases": self.databases,
            "wal_shm_files": self.wal_shm_files,
            "json_files": self.json_files,
            "jsonl_files": self.jsonl_files,
            "proto_files": self.proto_files,
            "conversation_stores": self.conversation_stores,
            "workspace_metadata_sources": self.workspace_metadata_sources,
            "total_files_scanned": self.total_files_scanned,
            "newest_timestamp": self.newest_timestamp,
            "oldest_timestamp": self.oldest_timestamp
        }


@dataclass
class InspectionReport:
    file: str
    name: str
    exists: bool
    is_valid_source: bool
    readable: bool
    tables: Dict[str, int] = field(default_factory=dict)
    detected_fields: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "name": self.name,
            "exists": self.exists,
            "is_valid_source": self.is_valid_source,
            "readable": self.readable,
            "tables": self.tables,
            "detected_fields": self.detected_fields,
            "error": self.error
        }


@dataclass
class SearchResult:
    title: str
    stem: str
    workspace: str
    date: str
    path: str
    full_path: str
    matched_snippets: List[str] = field(default_factory=list)
    full_content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "stem": self.stem,
            "workspace": self.workspace,
            "date": self.date,
            "path": self.path,
            "full_path": self.full_path,
            "matched_snippets": self.matched_snippets,
            "full_content": self.full_content
        }


@dataclass
class ValidationReport:
    status: str
    total_notes: int
    total_workspaces: int
    valid_frontmatter: int
    broken_links: int
    duplicate_conversation_ids: List[str] = field(default_factory=list)
    missing_transcripts: int = 0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_notes": self.total_notes,
            "total_workspaces": self.total_workspaces,
            "valid_frontmatter": self.valid_frontmatter,
            "broken_links": self.broken_links,
            "duplicate_conversation_ids": self.duplicate_conversation_ids,
            "missing_transcripts": self.missing_transcripts,
            "issues": self.issues,
            "warnings": self.warnings
        }
