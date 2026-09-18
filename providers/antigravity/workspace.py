"""
Workspace Resolution Engine for Antigravity provider.
Resolves workspace name and original path using strict 5-tier precedence.
"""

import re
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from core.sanitizer import sanitize_filename

KNOWN_WORKSPACE_ALIASES: Dict[str, str] = {
    "myself": "Myself",
    "ternakos": "TernakOS",
    "ternak os": "TernakOS",
    "ternak": "TernakOS",
    "company profile": "Company Profile",
    "vanila": "Company Profile",
    "juragan": "Juragan by Anak Bawang",
    "anak bawang": "Anak Bawang",
    "gopek": "Dasboard Gopek",
    "dasboard gopek": "Dasboard Gopek",
    "skripsi": "07_Skripsi_&_TA",
    "ta": "07_Skripsi_&_TA",
    "essence": "Essence Indonesia",
    "shutterstock": "Shutterstock",
    "virgin": "Dashboard Virgin",
    "dashboard virgin": "Dashboard Virgin",
    "publik speaking": "Pelatihan Publik Speaking",
    "google one": "Google One Pro",
    "hero farm": "Hero Farm File",
    "kedokteran": "Kedokteran",
    "didi": "Didi",
    "hukum": "Hukum",
    "gdg": "GDG"
}


def resolve_workspace(
    workspace_name: Optional[str] = None,
    workspace_path_or_uri: Optional[str] = None,
    workspace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[str]]:
    """
    Returns (clean_workspace_name, original_path_or_uri).
    """
    original_path = workspace_path_or_uri or (metadata.get("workspace_path") if metadata else None)

    # 1. Check explicit workspace_name
    if workspace_name and len(workspace_name.strip()) > 1:
        clean_name = sanitize_filename(workspace_name.strip())
        lower_name = clean_name.lower()
        for key, canonical in KNOWN_WORKSPACE_ALIASES.items():
            if key in lower_name:
                return canonical, original_path
        return clean_name, original_path

    # 2. Check workspace_path_or_uri
    if original_path:
        unquoted = urllib.parse.unquote(original_path)
        clean_p = unquoted.replace("file:///", "").replace("file://", "")
        clean_p = clean_p.rstrip("/\\")
        lower_path = clean_p.lower()

        # Check known aliases across full path first
        for key, canonical in KNOWN_WORKSPACE_ALIASES.items():
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
        for key, canonical in KNOWN_WORKSPACE_ALIASES.items():
            if key in lower_id:
                return canonical, original_path
        return sanitize_filename(workspace_id.strip()), original_path

    # 4. Check conversation metadata
    if metadata:
        for k in ("workspace", "project", "folder", "cwd"):
            if k in metadata and metadata[k]:
                resolved_name, _ = resolve_workspace(workspace_name=str(metadata[k]))
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
    m = re.search(r'(file:///[^\s\x00-\x1f"\'<>]+|[a-zA-Z]:\\[^\s\x00-\x1f"\'<>]+)', text)
    if m:
        path_or_uri = m.group(1)
        return resolve_workspace(workspace_path_or_uri=path_or_uri)
    return "Unknown Workspace", None
