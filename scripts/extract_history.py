#!/usr/bin/env python3
"""
History Extraction Pipeline.
Extracts conversation records via AntigravityHistoryProvider into intermediate normalized JSON structures.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure skill directory in sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_CONVERSATIONS_DIR, DEFAULT_NORMALIZED_DIR
from core.models import ChatSession
from providers.antigravity.provider import AntigravityHistoryProvider


def extract_history(
    source_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    src = Path(source_dir) if source_dir else DEFAULT_CONVERSATIONS_DIR
    out = Path(output_dir) if output_dir else DEFAULT_NORMALIZED_DIR
    out.mkdir(parents=True, exist_ok=True)

    print("=== HISTORY EXTRACTION PIPELINE ===")
    print(f"Source: {src}")
    print(f"Output: {out}")

    provider = AntigravityHistoryProvider()
    if source_dir:
        provider.conv_dir = Path(source_dir)

    db_files = sorted(src.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit and limit > 0:
        db_files = db_files[:limit]

    print(f"Ditemukan {len(db_files)} berkas database untuk diekstrak.\n")

    sessions: List[Dict[str, Any]] = []
    report = {
        "source": str(src),
        "total_databases": len(db_files),
        "extracted_sessions": 0,
        "skipped_empty": 0,
        "errors": [],
        "workspaces": {}
    }

    count = 0
    for session in provider.extract(source_dir=src, limit=limit):
        count += 1
        sessions.append(session.to_dict())
        report["extracted_sessions"] += 1
        ws = session.workspace_name
        report["workspaces"][ws] = report["workspaces"].get(ws, 0) + 1

        if count % 25 == 0 or count == len(db_files):
            print(f"Progress: [{count}/{len(db_files)}] Selesai diekstrak ({report['extracted_sessions']} sesi)...")

    # Save to JSON
    conversations_file = out / "conversations.json"
    report_file = out / "extraction-report.json"

    with open(conversations_file, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n✅ Ekstraksi selesai!")
    print(f"- Sesi berhasil diekstrak: {report['extracted_sessions']}")
    print(f"- File disimpan ke: {conversations_file}")

    return {"sessions": sessions, "report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Antigravity conversation history into normalized JSON.")
    parser.add_argument("--source", type=str, default=None, help="Source conversations directory")
    parser.add_argument("--output", type=str, default=None, help="Output directory for normalized JSON")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of databases to process")
    args = parser.parse_args()

    extract_history(
        source_dir=Path(args.source) if args.source else None,
        output_dir=Path(args.output) if args.output else None,
        limit=args.limit
    )
