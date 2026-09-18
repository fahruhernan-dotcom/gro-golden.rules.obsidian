#!/usr/bin/env python3
"""
MOC Builder CLI Script.
Thin entry point delegating to core MOCIndexer.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

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

from core.config import DEFAULT_LOGS_DIR
from core.indexer import MOCIndexer


def build_all_indexes(logs_dir: Optional[Path] = None) -> Dict[str, Any]:
    base_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
    print("=== MOC BUILDER ===")
    print(f"Logs Directory: {base_dir}")

    res = MOCIndexer.build_all_indexes(logs_dir=base_dir)
    if "error" in res:
        print(f"Error: {res['error']}")
        return res

    print(f"✅ Master MOC dan {res['workspaces_updated']} Sub-MOCs berhasil diperbarui.")
    print(f"Total sesi terindeks: {res['total_sessions']} sesi.")
    return res


def main():
    parser = argparse.ArgumentParser(description="Generate/rebuild 2-tier MOC indexes.")
    parser.add_argument("--logs-dir", type=str, default=str(DEFAULT_LOGS_DIR), help="Path to Antigravity Logs directory")
    args = parser.parse_args()

    build_all_indexes(logs_dir=Path(args.logs_dir))


if __name__ == "__main__":
    main()
