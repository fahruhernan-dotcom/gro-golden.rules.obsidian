#!/usr/bin/env python3
"""
Rename Session Note Script for Persistent Obsidian Memory System.
Safely renames an existing session note, updates internal title heading,
and rebuilds MOC hub indexes across the vault.
"""

import sys
import re
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

SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR
from core.identity import SessionIdentityResolver
from core.sanitizer import sanitize_filename
from core.indexer import MOCIndexer


def rename_session_note(
    conv_id: Optional[str] = None,
    note_path: Optional[str] = None,
    new_title: str = "",
    logs_dir: Optional[Path] = None
) -> Dict[str, Any]:
    logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
    clean_title = sanitize_filename(new_title.strip())

    if not clean_title:
        return {"status": "error", "message": "Judul baru tidak boleh kosong."}

    # Find the target note
    target_note: Optional[Path] = None
    if note_path:
        p = Path(note_path)
        if p.exists() and p.is_file():
            target_note = p

    if not target_note and conv_id:
        target_note = SessionIdentityResolver.find_existing_note(logs_dir, conv_id)

    if not target_note or not target_note.exists():
        return {
            "status": "error",
            "message": f"Catatan sesi tidak ditemukan (Conv ID: {conv_id}, Path: {note_path})."
        }

    old_filename = target_note.name
    # Match date and time pattern: YYYY-MM-DD - HH.MM - ...
    pattern = r"^(\d{4}-\d{2}-\d{2}\s*-\s*\d{2}\.\d{2})\s*-\s*(.+?)\.md$"
    m = re.match(pattern, old_filename)
    if m:
        prefix = m.group(1)
        new_filename = f"{prefix} - {clean_title}.md"
    else:
        new_filename = f"{clean_title}.md"

    destination = target_note.parent / new_filename

    # Read and update heading #
    content = target_note.read_text(encoding="utf-8")
    # Replace top h1 heading
    content = re.sub(r"^#\s+.*$", f"# {clean_title}", content, flags=re.MULTILINE, count=1)

    if destination != target_note and destination.exists():
        return {
            "status": "error",
            "message": f"File tujuan sudah ada: {destination.name}"
        }

    # Write updated content and rename
    target_note.write_text(content, encoding="utf-8")
    if destination != target_note:
        target_note.rename(destination)

    # Rebuild indexes
    MOCIndexer.build_all_indexes(logs_dir=logs_dir)

    return {
        "status": "success",
        "old_file": str(target_note),
        "new_file": str(destination),
        "new_title": clean_title
    }


def main():
    parser = argparse.ArgumentParser(description="Rename catatan sesi Obsidian dengan aman.")
    parser.add_argument("--conv-id", type=str, help="Conversation ID sesi")
    parser.add_argument("--path", type=str, help="Path absolut file catatan")
    parser.add_argument("--new-title", type=str, required=True, help="Judul baru catatan")
    parser.add_argument("--logs-dir", type=str, help="Path root Obsidian Logs")

    args = parser.parse_args()
    res = rename_session_note(
        conv_id=args.conv_id,
        note_path=args.path,
        new_title=args.new_title,
        logs_dir=Path(args.logs_dir) if args.logs_dir else None
    )

    if res["status"] == "success":
        print(f"Berhasil merename catatan sesi:")
        print(f"  - Dari: {res['old_file']}")
        print(f"  - Menjadi: {res['new_file']}")
    else:
        print(f"Gagal: {res.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
