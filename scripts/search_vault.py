#!/usr/bin/env python3
"""
Vault Search CLI Script.
Thin entry point delegating to core VaultSearchEngine.
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

# Add skill directory to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
from core.search import VaultSearchEngine, SearchResult


def search_vault(
    query: str,
    vault_root: Optional[Path] = None,
    logs_dir: Optional[Path] = None,
    workspace: Optional[str] = None,
    after_date: Optional[str] = None,
    before_date: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 10,
    json_output: bool = False,
    full: bool = False,
    after: Optional[str] = None,
    before: Optional[str] = None
) -> List[Dict[str, Any]]:
    results = VaultSearchEngine.search(
        query=query,
        logs_dir=logs_dir,
        vault_root=vault_root,
        workspace=workspace,
        after_date=after_date,
        before_date=before_date,
        tag=tag,
        limit=limit,
        full=full,
        after=after,
        before=before
    )

    dict_results = [r.to_dict() for r in results]

    if json_output:
        print(json.dumps(dict_results, indent=2, ensure_ascii=False))
        return dict_results

    print(f"=== HASIL PENCARIAN VAULT ({len(dict_results)} catatan ditemukan) ===")
    if not dict_results:
        print("Tidak ada catatan yang cocok dengan kriteria pencarian.")
        return dict_results

    for i, r in enumerate(dict_results, 1):
        print(f"\n[{i}] {r['title']}")
        print(f"    Workspace: {r['workspace']} | Date: {r['date']}")
        print(f"    Path: [[{r['stem']}]] ({r['path']})")
        if r["matched_snippets"]:
            print("    Matched:")
            for s in r["matched_snippets"]:
                print(f"      - {s}")

    return dict_results


def main():
    parser = argparse.ArgumentParser(description="Cari catatan riwayat percakapan di Obsidian Vault.")
    parser.add_argument("query", type=str, nargs="?", default="", help="Kata kunci pencarian")
    parser.add_argument("--workspace", type=str, default=None, help="Filter berdasarkan workspace/proyek")
    parser.add_argument("--after", type=str, default=None, help="Hanya sesi setelah tanggal ini (YYYY-MM-DD)")
    parser.add_argument("--before", type=str, default=None, help="Hanya sesi sebelum tanggal ini (YYYY-MM-DD)")
    parser.add_argument("--tag", type=str, default=None, help="Filter berdasarkan tag frontmatter")
    parser.add_argument("--limit", type=int, default=5, help="Jumlah maksimal hasil yang ditampilkan (default: 5)")
    parser.add_argument("--vault", type=str, default=None, help="Path ke root Obsidian Vault")
    parser.add_argument("--json", action="store_true", help="Output dalam format JSON murni")
    parser.add_argument("--full", action="store_true", help="Sertakan isi lengkap catatan")
    args = parser.parse_args()

    search_vault(
        query=args.query,
        vault_root=Path(args.vault) if args.vault else None,
        workspace=args.workspace,
        after_date=args.after,
        before_date=args.before,
        tag=args.tag,
        limit=args.limit,
        json_output=args.json,
        full=args.full
    )


if __name__ == "__main__":
    main()
