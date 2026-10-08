"""
Golden Rules Obsidian (`gro`) v3.0 - Core Package.
Zero-Dependency Universal Working Memory & Knowledge Architecture for AI Coding Agents.
Pure Python Standard Library.
"""

from .config import find_obsidian_vault, DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
from .sanitizer import sanitize_filename
from .indexer import MOCIndexer
from .validator import VaultValidator, ValidationReport
from .search import VaultSearchEngine, SearchResult

__all__ = [
    "find_obsidian_vault",
    "DEFAULT_LOGS_DIR",
    "DEFAULT_VAULT_ROOT",
    "sanitize_filename",
    "MOCIndexer",
    "VaultValidator",
    "ValidationReport",
    "VaultSearchEngine",
    "SearchResult",
]
