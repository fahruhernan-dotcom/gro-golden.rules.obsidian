#!/usr/bin/env python3
"""
Antigravity Discovery CLI Script.
Thin entry point delegating to AntigravityHistoryProvider.
"""

import sys
import json
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

from core.config import DEFAULT_ANTIGRAVITY_ROOT
from providers.antigravity.provider import AntigravityHistoryProvider


def discover_antigravity(source_root: Optional[Path] = None, json_output: bool = False) -> Dict[str, Any]:
    provider = AntigravityHistoryProvider(root_dir=source_root)
    report = provider.discover(source_root=source_root)
    d = report.to_dict()

    if json_output:
        print(json.dumps(d, indent=2))
        return d

    print("=== ANTIGRAVITY STORAGE ===")
    print(f"Root:\n  {report.root}")
    if not report.exists:
        print("  (DOES NOT EXIST)")
        return d

    print(f"\nDatabases ({len(report.databases)} found):")
    for db in report.databases[:8]:
        print(f"  - {db}")
    if len(report.databases) > 8:
        print(f"  ... and {len(report.databases) - 8} more databases.")

    print(f"\nPotential conversation stores ({len(report.conversation_stores)} found):")
    for cs in report.conversation_stores[:5]:
        print(f"  - {cs}")
    if len(report.conversation_stores) > 5:
        print(f"  ... and {len(report.conversation_stores) - 5} more.")

    print(f"\nPotential workspace metadata ({len(report.workspace_metadata_sources)} files):")
    for meta in report.workspace_metadata_sources[:5]:
        print(f"  - {meta}")

    print(f"\nPotential protobuf data ({len(report.proto_files)} files):")
    for pb in report.proto_files[:5]:
        print(f"  - {pb}")

    print(f"\nPotential timestamps:")
    print(f"  Oldest activity: {report.oldest_timestamp}")
    print(f"  Newest activity: {report.newest_timestamp}")
    print(f"  Total files scanned: {report.total_files_scanned}")

    return d


def main():
    parser = argparse.ArgumentParser(description="Discover local Antigravity storage, databases, and protobuf telemetry.")
    parser.add_argument("--source", type=str, default=str(DEFAULT_ANTIGRAVITY_ROOT), help="Path to Antigravity storage root")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    discover_antigravity(source_root=Path(args.source), json_output=args.json)


if __name__ == "__main__":
    main()
