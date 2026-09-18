"""
Workspace Resolution Module.
Delegates to providers.antigravity.workspace for dynamic folder-based workspace detection.
"""

import sys
from pathlib import Path

# Ensure root package is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from providers.antigravity.workspace import (
    resolve_workspace,
    resolve_workspace_name,
    extract_workspace_from_blob,
    get_custom_workspace_aliases,
    KNOWN_WORKSPACE_ALIASES,
)

__all__ = [
    "resolve_workspace",
    "resolve_workspace_name",
    "extract_workspace_from_blob",
    "get_custom_workspace_aliases",
    "KNOWN_WORKSPACE_ALIASES",
]
