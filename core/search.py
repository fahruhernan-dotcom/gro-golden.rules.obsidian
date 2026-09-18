"""
Contextual Knowledge Retrieval Engine for Obsidian Vault.
Searches session notes by topic, content, workspace, and dates, returning concise snippet hits.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import SearchResult
try:
    from .config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
except ImportError:
    try:
        from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
    except ImportError:
        from config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """Extracts simple key-value pairs from YAML frontmatter."""
    meta: Dict[str, Any] = {}
    if not content.startswith("---"):
        return meta
    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta
    fm_text = parts[1]
    for line in fm_text.splitlines():
        if ":" in line and not line.strip().startswith("-"):
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"\'')
    return meta


class VaultSearchEngine:
    """
    Search engine for contextual memory retrieval across Obsidian logs.
    """

    @classmethod
    def search(
        cls,
        query: str,
        logs_dir: Optional[Path] = None,
        vault_root: Optional[Path] = None,
        workspace: Optional[str] = None,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10,
        full: bool = False,
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[SearchResult]:
        effective_root = logs_dir or vault_root or DEFAULT_LOGS_DIR
        root = Path(effective_root)
        if not root.exists():
            return []

        after_date = after or after_date
        before_date = before or before_date

        q_lower = query.lower() if query else ""
        ws_filter = workspace.lower() if workspace else None
        tag_filter = tag.lower() if tag else None

        after_dt = None
        if after_date:
            try:
                after_dt = datetime.strptime(after_date.strip(), "%Y-%m-%d")
            except ValueError:
                pass

        before_dt = None
        if before_date:
            try:
                before_dt = datetime.strptime(before_date.strip(), "%Y-%m-%d")
            except ValueError:
                pass

        results: List[SearchResult] = []

        for p in root.rglob("*.md"):
            if ".obsidian" in p.parts:
                continue

            # Skip MOC indexes unless query explicitly targets index/hub
            is_moc = p.name.startswith("Index - ")
            if is_moc and "index" not in q_lower and "hub" not in q_lower:
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                fm = parse_frontmatter(content)
                note_ws = fm.get("workspace", p.parent.name)

                # Workspace filter
                if ws_filter and ws_filter not in note_ws.lower():
                    continue

                # Tag filter
                if tag_filter and tag_filter not in content.lower():
                    continue

                # Date filter
                note_date_str = fm.get("date")
                if after_dt or before_dt:
                    if not note_date_str:
                        continue
                    try:
                        ndt = datetime.strptime(note_date_str, "%Y-%m-%d")
                        if after_dt and ndt < after_dt:
                            continue
                        if before_dt and ndt > before_dt:
                            continue
                    except ValueError:
                        continue

                # Query match check
                stem_match = q_lower in p.stem.lower() if q_lower else True
                content_match = q_lower in content.lower() if q_lower else True

                if not (stem_match or content_match):
                    continue

                # Extract topic/title
                title = p.stem
                m_fn = re.match(r'^\d{4}-\d{2}-\d{2}\s*-\s*\d{2}\.\d{2}\s*-\s*(.+?)(?:\s*\[\d+\])?$', p.stem)
                if m_fn:
                    title = m_fn.group(1).strip()
                else:
                    m_h1 = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if m_h1:
                        title = m_h1.group(1).strip()

                # Extract matching snippets (up to 3 concise lines)
                snippets: List[str] = []
                if q_lower:
                    for line_idx, line in enumerate(content.splitlines(), 1):
                        if q_lower in line.lower():
                            clean_l = re.sub(r'^[>#*\-\s]+', '', line).strip()
                            if clean_l and clean_l not in snippets:
                                snippets.append(f"L{line_idx}: {clean_l[:140]}")
                            if len(snippets) >= 3:
                                break
                else:
                    snippets.append("Catatan cocok dengan filter metadata.")

                rel_path = p.relative_to(root)
                results.append(SearchResult(
                    title=title,
                    stem=p.stem,
                    workspace=note_ws,
                    date=note_date_str or datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
                    path=str(rel_path),
                    full_path=str(p),
                    matched_snippets=snippets,
                    full_content=content if full else None
                ))

            except Exception:
                continue

        results.sort(key=lambda x: x.date, reverse=True)
        return results[:limit]


search_vault = VaultSearchEngine.search
