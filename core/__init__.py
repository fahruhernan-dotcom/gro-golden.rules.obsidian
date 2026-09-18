"""
Persistent Obsidian Memory System - Core Package.
Agent-agnostic memory engine providing models, indexing, search, rendering, validation, and identity.
"""

from .models import ChatMessage, ChatSession, Workspace, DiscoveryReport, InspectionReport, SearchResult, ValidationReport
from .history_provider import HistoryProvider
from .identity import SessionIdentityResolver
from .archive_engine import ArchiveEngine
from .indexer import MOCIndexer
from .search import VaultSearchEngine
from .validator import VaultValidator

__all__ = [
    "ChatMessage",
    "ChatSession",
    "Workspace",
    "DiscoveryReport",
    "InspectionReport",
    "SearchResult",
    "ValidationReport",
    "HistoryProvider",
    "SessionIdentityResolver",
    "ArchiveEngine",
    "MOCIndexer",
    "VaultSearchEngine",
    "VaultValidator",
]
