#!/usr/bin/env python3
"""
Archive Session CLI Script.
Thin entry point delegating to AntigravityHistoryProvider and core ArchiveEngine.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add skill directory to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR, DEFAULT_CONVERSATIONS_DIR
from core.archive_engine import ArchiveEngine
from core.identity import SessionIdentityResolver
from core.sanitizer import sanitize_filename
from providers.antigravity.provider import AntigravityHistoryProvider


def find_existing_note_by_conv_id(logs_dir: Path, conv_id: str) -> Optional[Path]:
    """Backward-compatible helper to find an existing note by conversation ID."""
    return SessionIdentityResolver.find_existing_note(Path(logs_dir), conv_id)


def archive_session(
    conv_id: Optional[str] = None,
    custom_topic: Optional[str] = None,
    source_dir: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    provider = AntigravityHistoryProvider()
    if source_dir:
        provider.conv_dir = Path(source_dir)

    session = provider.extract_session(conversation_id=conv_id or "")
    if not session:
        print(f"Error: Tidak dapat menemukan atau membaca sesi percakapan (ID: {conv_id or 'latest'}).")
        return {"error": "Session not found", "status": "failed"}

    if custom_topic:
        session.title = sanitize_filename(custom_topic)

    engine = ArchiveEngine(logs_dir=logs_dir or DEFAULT_LOGS_DIR)
    result = engine.save_session(session=session, dry_run=dry_run, rebuild_mocs=True)

    action_label = "MENGUPDATE" if result["action"] == "UPDATE" else "MEMBUAT"
    mode_label = "[DRY-RUN] " if dry_run else ""
    print(f"{mode_label}Berhasil {action_label} catatan sesi:")
    print(f"  - Topik: {session.title}")
    print(f"  - Workspace: {result['workspace']}")
    print(f"  - File: {result['target_file']}")
    print(f"  - Sesi ID: {session.conversation_id}")
    print(f"  - Pesan: {result['messages_count']} | File terpengaruh: {result['affected_files_count']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Arsipkan sesi Antigravity ke Obsidian Vault Lemonaru.")
    parser.add_argument("--conv-id", type=str, default=None, help="Conversation/Trajectory ID spesifik")
    parser.add_argument("--topic", type=str, default=None, help="Judul kustom untuk topik sesi")
    parser.add_argument("--source", type=str, default=None, help="Direktori database sumber")
    parser.add_argument("--vault", type=str, default=None, help="Direktori target Antigravity Logs di Obsidian")
    parser.add_argument("--dry-run", action="store_true", help="Simulasi arsip tanpa menulis ke disk")
    args = parser.parse_args()

    archive_session(
        conv_id=args.conv_id,
        custom_topic=args.topic,
        source_dir=Path(args.source) if args.source else None,
        logs_dir=Path(args.vault) if args.vault else None,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
