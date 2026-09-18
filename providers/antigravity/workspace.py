"""
Workspace Resolution Engine for Antigravity provider.
Resolves workspace name and original path using strict 5-tier precedence.
"""

import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from core.sanitizer import sanitize_filename

import os
import json

def get_custom_workspace_aliases() -> Dict[str, str]:
    """
    Returns user-defined workspace alias mappings if configured via
    the GRO_WORKSPACE_ALIASES environment variable (JSON object string).
    Default is an empty dictionary to ensure 100% portability.
    """
    env_aliases = os.environ.get("GRO_WORKSPACE_ALIASES")
    if env_aliases:
        try:
            parsed = json.loads(env_aliases)
            if isinstance(parsed, dict):
                return {str(k).lower(): str(v) for k, v in parsed.items()}
        except Exception:
            pass
    return {}


# Default aliases dictionary (empty for 100% portability across all users and folders)
KNOWN_WORKSPACE_ALIASES: Dict[str, str] = {}


def resolve_workspace(
    workspace_name: Optional[str] = None,
    workspace_path_or_uri: Optional[str] = None,
    workspace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    custom_aliases: Optional[Dict[str, str]] = None
) -> Tuple[str, Optional[str]]:
    """
    Returns (clean_workspace_name, original_path_or_uri).
    Dynamically resolves the workspace name based on the user's project folder.
    """
    original_path = workspace_path_or_uri or (metadata.get("workspace_path") if metadata else None)
    aliases = custom_aliases if custom_aliases is not None else (KNOWN_WORKSPACE_ALIASES or get_custom_workspace_aliases())

    # 1. Check explicit workspace_name
    if workspace_name and len(workspace_name.strip()) > 1:
        clean_name = sanitize_filename(workspace_name.strip())
        lower_name = clean_name.lower()
        for key, canonical in aliases.items():
            if key in lower_name:
                return canonical, original_path
        return clean_name, original_path

    # 2. Check workspace_path_or_uri (auto-detects project folder basename)
    if original_path:
        unquoted = urllib.parse.unquote(original_path)
        clean_p = unquoted.replace("file:///", "").replace("file://", "")
        clean_p = clean_p.rstrip("/\\")
        lower_path = clean_p.lower()

        # Check user-configured aliases across full path first if any exist
        for key, canonical in aliases.items():
            if key in lower_path:
                return canonical, original_path

        if clean_p:
            parts = [p for p in re.split(r"[/\\]", clean_p) if p and ":" not in p]
            if parts:
                folder_name = sanitize_filename(parts[-1])
                return folder_name, original_path

    # 3. Check workspace_id metadata
    if workspace_id and len(workspace_id.strip()) > 1:
        lower_id = workspace_id.lower()
        for key, canonical in aliases.items():
            if key in lower_id:
                return canonical, original_path
        return sanitize_filename(workspace_id.strip()), original_path

    # 4. Check conversation metadata
    if metadata:
        for k in ("workspace", "project", "folder", "cwd"):
            if k in metadata and metadata[k]:
                resolved_name, _ = resolve_workspace(workspace_name=str(metadata[k]), custom_aliases=aliases)
                if resolved_name != "Unknown Workspace":
                    return resolved_name, original_path

    # 5. Fallback
    return "Unknown Workspace", original_path


def resolve_workspace_name(
    workspace_name: Optional[str] = None,
    workspace_path: Optional[str] = None,
    workspace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience helper that returns only the resolved workspace name."""
    name, _ = resolve_workspace(
        workspace_name=workspace_name,
        workspace_path_or_uri=workspace_path,
        workspace_id=workspace_id,
        metadata=metadata
    )
    return name


def extract_workspace_from_blob(blob: bytes) -> Tuple[str, Optional[str]]:
    """Extracts workspace name and path from raw trajectory metadata blob."""
    if not blob:
        return "Unknown Workspace", None
    text = blob.decode("utf-8", errors="ignore")
    m = re.search(r'(file:///[^\s\x00-\x1f"\'<>]+|[a-zA-Z]:[/\\][^\s\x00-\x1f"\'<>]+|/(?:Users|home|var|tmp|srv|root|workspace|code|projects|dev)/[^\s\x00-\x1f"\'<>]+)', text)
    if m:
        path_or_uri = m.group(1)
        return resolve_workspace(workspace_path_or_uri=path_or_uri)
    return "Unknown Workspace", None
