"""
Abstract Provider Interface for Persistent Obsidian Memory System.
Enables agent-agnostic extraction across Antigravity, Claude Code, Cursor, or local CLI transcripts.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Iterable, Dict, Any

from .models import ChatSession, DiscoveryReport, InspectionReport


class HistoryProvider(ABC):
    """
    Abstract contract for agent history sources.
    Source-specific adapters implement this interface to produce canonical ChatSession objects.
    """

    @abstractmethod
    def discover(self, source_root: Optional[Path] = None) -> DiscoveryReport:
        """Discovers available databases, telemetry, or transcript files in the source storage."""
        pass

    @abstractmethod
    def inspect(self, target: Path) -> InspectionReport:
        """Performs read-only inspection of a specific conversation file or store."""
        pass

    @abstractmethod
    def extract(
        self,
        source_dir: Optional[Path] = None,
        limit: Optional[int] = None
    ) -> Iterable[ChatSession]:
        """Extracts and normalizes conversation records into canonical ChatSession models."""
        pass

    @abstractmethod
    def extract_session(self, conversation_id: str) -> Optional[ChatSession]:
        """Extracts and normalizes a single specific conversation session by its ID."""
        pass
