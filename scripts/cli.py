#!/usr/bin/env python3
"""
Unified CLI for Golden Rules Obsidian.
Command: golden-rules-obsidian / gro
Subcommands:
  archive  - Archive current or specific conversation to Obsidian Vault with proactive turn-8 checkpointing
  search   - Fast context and keyword search across archived notes and transcript snippets
  index    - Rebuild 2-Tier Hub-and-Spoke MOC with executive summary columns
  validate - Audit health, frontmatter schema, and link integrity of the vault
  council  - Convene a 5-persona LLM Architecture Council review for engineering dilemmas
"""

import sys
import argparse
from pathlib import Path

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

from scripts.archive_session import archive_session
from scripts.search_vault import search_vault
from scripts.build_index import build_all_indexes
from scripts.validate_vault import VaultValidator
from scripts.council import run_council
from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT

VERSION = "1.0.0"


def cmd_archive(args):
    """Handler for 'archive' subcommand."""
    print("🚀 [GRO ARCHIVE] Initiating Obsidian Session Archive...")
    archive_session(
        conv_id=args.conv_id,
        custom_topic=args.topic,
        source_dir=Path(args.source) if args.source else None,
        logs_dir=Path(args.vault) if args.vault else None,
        dry_run=args.dry_run
    )


def cmd_search(args):
    """Handler for 'search' subcommand."""
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


def cmd_index(args):
    """Handler for 'index' subcommand."""
    print("📚 [GRO INDEX] Rebuilding 2-Tier Hub-and-Spoke MOC Indexes...")
    build_all_indexes(logs_dir=Path(args.logs_dir) if args.logs_dir else None)


def cmd_validate(args):
    """Handler for 'validate' subcommand."""
    print("🔍 [GRO VALIDATE] Auditing Vault Health & Link Integrity...")
    target_dir = Path(args.vault) if args.vault else DEFAULT_LOGS_DIR
    validator = VaultValidator(target_dir)
    is_valid = validator.validate()
    print(validator.format_report())
    if not is_valid:
        sys.exit(1)


def cmd_council(args):
    """Handler for 'council' subcommand."""
    run_council(
        dilemma=args.dilemma,
        save_to_vault=args.save,
        logs_dir=Path(args.vault) if args.vault else None
    )


def main():
    parser = argparse.ArgumentParser(
        prog="gro",
        description="🌟 Golden Rules Obsidian (`gro`) — Production-Grade Working Memory & Knowledge Architecture for AI Coding Agents."
    )
    parser.add_argument("-v", "--version", action="version", version=f"golden-rules-obsidian (gro) v{VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Sub-command to execute")

    # 1. Archive
    p_archive = subparsers.add_parser("archive", help="Archive session with proactive turn-8 checkpointing")
    p_archive.add_argument("--conv-id", type=str, default=None, help="Specific conversation/trajectory ID")
    p_archive.add_argument("--topic", type=str, default=None, help="Custom semantic title/topic")
    p_archive.add_argument("--source", type=str, default=None, help="Path to source session DB directory")
    p_archive.add_argument("--vault", type=str, default=None, help="Target Antigravity Logs directory in Obsidian")
    p_archive.add_argument("--dry-run", action="store_true", help="Simulate without writing to disk")
    p_archive.set_defaults(func=cmd_archive)

    # 2. Search
    p_search = subparsers.add_parser("search", help="Fast keyword & semantic context search across vault notes")
    p_search.add_argument("query", type=str, nargs="?", default="", help="Search query or keyword")
    p_search.add_argument("--workspace", type=str, default=None, help="Filter by workspace name")
    p_search.add_argument("--after", type=str, default=None, help="Filter notes after date (YYYY-MM-DD)")
    p_search.add_argument("--before", type=str, default=None, help="Filter notes before date (YYYY-MM-DD)")
    p_search.add_argument("--tag", type=str, default=None, help="Filter by frontmatter tag")
    p_search.add_argument("--limit", type=int, default=5, help="Max results to display (default: 5)")
    p_search.add_argument("--vault", type=str, default=None, help="Path to Obsidian vault root")
    p_search.add_argument("--json", action="store_true", help="Output pure JSON")
    p_search.add_argument("--full", action="store_true", help="Display full note content")
    p_search.set_defaults(func=cmd_search)

    # 3. Index
    p_index = subparsers.add_parser("index", help="Rebuild 2-tier Hub-and-Spoke MOC tables")
    p_index.add_argument("--logs-dir", type=str, default=None, help="Path to Antigravity Logs directory")
    p_index.set_defaults(func=cmd_index)

    # 4. Validate
    p_validate = subparsers.add_parser("validate", help="Audit vault structure, frontmatter schemas, and wikilink integrity")
    p_validate.add_argument("--vault", type=str, default=None, help="Path to Antigravity Logs folder")
    p_validate.set_defaults(func=cmd_validate)

    # 5. Council
    p_council = subparsers.add_parser("council", help="Convene 5-persona LLM Council for architectural review")
    p_council.add_argument("dilemma", type=str, help="Architecture dilemma or technical decision statement")
    p_council.add_argument("--save", action="store_true", help="Save review markdown directly to Obsidian Vault Concept node")
    p_council.add_argument("--vault", type=str, default=None, help="Path to Obsidian vault root")
    p_council.set_defaults(func=cmd_council)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
