"""
Golden Rules Obsidian (`gro`) v3.0 CLI Entrypoint.
100% Zero-Dependency Universal Vault Maintenance & Context Toolkit.
Pure Python Standard Library (argparse, pathlib, re, json, datetime).
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output across Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
from core.indexer import MOCIndexer
from core.validator import VaultValidator
from core.search import VaultSearchEngine

VERSION = "3.0.0"


def resolve_current_workspace(cwd: Optional[Path] = None, logs_dir: Optional[Path] = None) -> str:
    """Infers workspace name from active path or directory name, matching against vault if available."""
    curr = (cwd or Path.cwd()).resolve()
    target_logs = logs_dir or DEFAULT_LOGS_DIR
    parts = list(reversed(curr.parts))

    def is_valid_name(name: str) -> bool:
        if not name or name.endswith(":") or name in ("\\", "/"):
            return False
        if name.lower() in ("src", "core", "scripts", "tests", "docs", ".git", ".agents"):
            return False
        return True

    # First priority: check if any ancestor directory directly matches an existing workspace in vault
    if target_logs.is_dir():
        for p in parts:
            if not is_valid_name(p):
                continue
            candidate = target_logs / p
            if candidate.is_dir() and candidate.parent == target_logs:
                return p

    # Second priority: pick first non-technical folder name
    for p in parts:
        if is_valid_name(p):
            return p
    return curr.name


def cmd_resume(args: argparse.Namespace) -> int:
    logs_dir = Path(args.logs_dir) if args.logs_dir else DEFAULT_LOGS_DIR
    ws_name = args.workspace or resolve_current_workspace(logs_dir=logs_dir)
    ws_dir = logs_dir / ws_name

    active_ctx_file = ws_dir / "ActiveContext.md"
    if active_ctx_file.exists():
        content = active_ctx_file.read_text(encoding="utf-8")
        if args.for_agent:
            print(content)
        else:
            print(f"🧠 [GRO RESUME] Active Context: {ws_name}\n")
            print(content)
        return 0

    # Fallback: Sub-MOC table
    sub_moc = ws_dir / f"Index - {ws_name}.md"
    if sub_moc.exists():
        content = sub_moc.read_text(encoding="utf-8")
        print(f"⚠️ ActiveContext.md belum ada untuk workspace '{ws_name}'. Menampilkan Sub-MOC:")
        print(content[:1500])
        return 0

    print(f"❌ Tidak ditemukan konteks atau catatan untuk workspace '{ws_name}' di {logs_dir}")
    return 1


def cmd_index(args: argparse.Namespace) -> int:
    logs_dir = Path(args.logs_dir) if args.logs_dir else DEFAULT_LOGS_DIR
    print("📚 [GRO INDEX] Rebuilding 2-Tier Hub-and-Spoke MOC Indexes...")
    indexer = MOCIndexer(logs_dir=logs_dir)
    if args.workspace:
        res = indexer.update_workspace(args.workspace)
        print(f"✅ Sub-MOC untuk workspace '{args.workspace}' berhasil diperbarui.")
    else:
        res = indexer.build_all()
        print(f"=== MOC BUILDER ===")
        print(f"Logs Directory: {logs_dir}")
        print(f"✅ Master MOC dan {len(res.get('sub_mocs', []))} Sub-MOCs berhasil diperbarui.")
        print(f"Total sesi terindeks: {res.get('total_sessions', 0)} sesi.")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    logs_dir = Path(args.logs_dir) if args.logs_dir else DEFAULT_LOGS_DIR
    print("🔍 [GRO VALIDATE] Auditing Vault Health & Link Integrity...")
    validator = VaultValidator(logs_dir=logs_dir)
    is_valid = validator.validate()
    print(validator.format_report())
    return 0 if is_valid else 1


def cmd_search(args: argparse.Namespace) -> int:
    logs_dir = Path(args.logs_dir) if args.logs_dir else DEFAULT_LOGS_DIR
    results = VaultSearchEngine.search(
        query=args.query,
        logs_dir=logs_dir,
        workspace=args.workspace,
        after_date=args.after,
        before_date=args.before,
        limit=args.limit or 10,
        full=args.full
    )

    if args.json:
        payload = [
            {
                "title": r.title,
                "workspace": r.workspace,
                "date": r.date,
                "path": r.path,
                "snippets": r.matched_snippets
            }
            for r in results
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if not results:
        print(f"Tidak ada catatan yang cocok dengan query '{args.query}'.")
        return 0

    print(f"=== HASIL PENCARIAN VAULT ({len(results)} catatan ditemukan) ===\n")
    for idx, r in enumerate(results, 1):
        print(f"[{idx}] {r.title}")
        print(f"    Workspace: {r.workspace} | Date: {r.date}")
        print(f"    Path: [[{r.stem}]] ({r.path})")
        if r.matched_snippets:
            print("    Matched:")
            for s in r.matched_snippets:
                print(f"      - {s}")
        print()
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    logs_dir = Path(args.logs_dir) if args.logs_dir else DEFAULT_LOGS_DIR
    ws_name = args.workspace or resolve_current_workspace()
    ws_dir = logs_dir / ws_name

    bundle = {
        "workspace": ws_name,
        "active_context": None,
        "recent_sessions": []
    }

    active_ctx_file = ws_dir / "ActiveContext.md"
    if active_ctx_file.exists():
        bundle["active_context"] = active_ctx_file.read_text(encoding="utf-8")

    sub_moc = ws_dir / f"Index - {ws_name}.md"
    if sub_moc.exists():
        bundle["sub_moc"] = sub_moc.read_text(encoding="utf-8")

    print(json.dumps(bundle, indent=2, ensure_ascii=False))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gro",
        description="Golden Rules Obsidian (gro) v3.0 -- Zero-Dependency Universal Working Memory for AI Agents."
    )
    parser.add_argument("-v", "--version", action="version", version=f"golden-rules-obsidian (gro) v{VERSION} (Zero-Dependency Universal)")
    parser.add_argument("--logs-dir", help="Kustom direktori logs (default: auto-detected Obsidian vault)")

    subparsers = parser.add_subparsers(dest="subcommand", help="Sub-command yang tersedia")

    # resume
    p_resume = subparsers.add_parser("resume", help="Tampilkan konteks aktif workspace saat ini")
    p_resume.add_argument("--workspace", "-w", help="Target nama workspace")
    p_resume.add_argument("--for-agent", action="store_true", help="Output markdown bersih untuk injeksi prompt agen")
    p_resume.set_defaults(func=cmd_resume)

    # index
    p_index = subparsers.add_parser("index", help="Bangun ulang Master Hub dan Sub-MOCs")
    p_index.add_argument("--workspace", "-w", help="Perbarui hanya workspace spesifik")
    p_index.set_defaults(func=cmd_index)

    # validate
    p_validate = subparsers.add_parser("validate", help="Audit integritas vault, skema frontmatter, dan wikilinks")
    p_validate.set_defaults(func=cmd_validate)

    # search
    p_search = subparsers.add_parser("search", help="Cari kata kunci di catatan vault")
    p_search.add_argument("query", help="Query kata kunci pencarian")
    p_search.add_argument("--workspace", "-w", help="Filter berdasarkan workspace")
    p_search.add_argument("--limit", "-l", type=int, default=10, help="Batas hasil pencarian")
    p_search.add_argument("--after", help="Filter tanggal sesudah (YYYY-MM-DD)")
    p_search.add_argument("--before", help="Filter tanggal sebelum (YYYY-MM-DD)")
    p_search.add_argument("--full", action="store_true", help="Sertakan isi dokumen lengkap")
    p_search.add_argument("--json", action="store_true", help="Output format JSON")
    p_search.set_defaults(func=cmd_search)

    # pack
    p_pack = subparsers.add_parser("pack", help="Ekspor bundle konteks aktif dalam format JSON")
    p_pack.add_argument("--workspace", "-w", help="Target nama workspace")
    p_pack.set_defaults(func=cmd_pack)

    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
