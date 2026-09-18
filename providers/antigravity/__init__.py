"""
Antigravity Provider Package.
Adapts Antigravity IDE storage, SQLite databases, and protobuf streams into canonical ChatSession models.
"""

from .provider import AntigravityHistoryProvider
from .sqlite import SafeDatabaseReader, DatabaseReadError
from .discovery import AntigravityDiscovery

__all__ = [
    "AntigravityHistoryProvider",
    "SafeDatabaseReader",
    "DatabaseReadError",
    "AntigravityDiscovery"
]
