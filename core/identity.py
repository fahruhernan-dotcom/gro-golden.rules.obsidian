"""
Session Identity and Deduplication Registry.
Provides deterministic identity resolution, collision detection, and idempotent note matching.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from .models import ChatSession


class SessionIdentityResolver:
    """
    Manages session identity, deduplication, and filename collision resolution.
    Decoupled from file rendering and storage engines.
    """

    @staticmethod
    def compute_stable_identity(session: ChatSession) -> str:
        """
        Determines canonical identity:
        Primary: session.conversation_id
        Fallback: deterministic hash of workspace + timestamp + normalized title
        """
        if session.conversation_id and len(session.conversation_id.strip()) > 3:
            return session.conversation_id.strip()

        raw_sig = f"{session.workspace_name}|{session.started_at}|{session.title.strip().lower()}"
        return hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def find_existing_note(
        logs_dir: Path,
        conversation_id: str,
        workspace_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Scans vault for a note matching the given conversation_id in YAML frontmatter.
        """
        logs_dir = Path(logs_dir)
        if not logs_dir.exists():
            return None

        search_dirs = [logs_dir / workspace_name] if (workspace_name and (logs_dir / workspace_name).exists()) else [logs_dir]
        target_id_str = f'conversation_id: "{conversation_id}"'
        target_id_raw = f'conversation_id: {conversation_id}'

        for search_dir in search_dirs:
            for p in search_dir.rglob("*.md"):
                if p.name.startswith("Index - "):
                    continue
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for _ in range(40):
                            line = f.readline()
                            if not line:
                                break
                            if target_id_str in line or target_id_raw in line:
                                return p
                except Exception:
                    continue

        if search_dirs != [logs_dir]:
            for p in logs_dir.rglob("*.md"):
                if p.name.startswith("Index - "):
                    continue
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for _ in range(40):
                            line = f.readline()
                            if not line:
                                break
                            if target_id_str in line or target_id_raw in line:
                                return p
                except Exception:
                    continue

        return None

    @staticmethod
    def find_session_parts(
        logs_dir: Path,
        conversation_id: str,
        workspace_name: Optional[str] = None
    ) -> List[Tuple[int, Path]]:
        """
        Finds all note parts for the given conversation_id, returned as sorted list of (part_num, Path).
        """
        logs_dir = Path(logs_dir)
        search_dirs = [logs_dir / workspace_name] if (workspace_name and (logs_dir / workspace_name).exists()) else [logs_dir]
        target_id_str = f'conversation_id: "{conversation_id}"'
        target_id_raw = f'conversation_id: {conversation_id}'

        parts = []
        for sdir in search_dirs:
            for p in sdir.rglob("*.md"):
                if p.name.startswith("Index - "):
                    continue
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        content_head = "".join([f.readline() for _ in range(45)])
                        if target_id_str in content_head or target_id_raw in content_head:
                            part_match = re.search(r'part:\s*(\d+)', content_head)
                            p_num = int(part_match.group(1)) if part_match else 1
                            parts.append((p_num, p))
                except Exception:
                    continue

        parts.sort(key=lambda x: x[0])
        return parts

    @classmethod
    def resolve_target_file(
        cls,
        target_folder: Path,
        base_filename: str,
        session: ChatSession,
        existing_note: Optional[Path] = None
    ) -> Tuple[Path, str]:
        """
        Resolves the final target file path and action.
        """
        target_folder = Path(target_folder)

        if existing_note and existing_note.exists():
            return existing_note, "UPDATE"

        target_file = target_folder / base_filename
        if not target_file.exists():
            return target_file, "CREATE"

        canonical_id = cls.compute_stable_identity(session)
        match = cls.find_existing_note(target_folder, canonical_id)
        if match and match == target_file:
            return target_file, "UPDATE"

        stem = target_file.stem
        ext = target_file.suffix
        counter = 2

        while target_file.exists():
            match = cls.find_existing_note(target_folder, canonical_id)
            if match and match == target_file:
                return target_file, "UPDATE"

            suffixed_name = f"{stem} [{counter}]{ext}"
            target_file = target_folder / suffixed_name
            counter += 1
            if counter > 50:
                break

        return target_file, "CREATE"
