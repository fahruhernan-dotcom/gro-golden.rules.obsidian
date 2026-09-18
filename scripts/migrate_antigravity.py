#!/usr/bin/env python3
"""
Full Migration Pipeline for Antigravity Session Logs into Obsidian Vault.
Orchestrates: Discover -> Inspect -> Extract -> Reconcile Identity -> Render -> Index -> Validate.
Supports --dry-run for zero-mutation preview.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

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

from core.config import (
    DEFAULT_ANTIGRAVITY_ROOT,
    DEFAULT_LOGS_DIR,
    DEFAULT_CONVERSATIONS_DIR
)
from core.archive_engine import ArchiveEngine
from core.indexer import MOCIndexer
from core.validator import VaultValidator
from providers.antigravity.provider import AntigravityHistoryProvider


def run_migration(
    source_root: Optional[Path] = None,
    target_logs_dir: Optional[Path] = None,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Execute end-to-end migration pipeline using core and providers."""
    src_root = Path(source_root) if source_root else DEFAULT_ANTIGRAVITY_ROOT
    logs_dir = Path(target_logs_dir) if target_logs_dir else DEFAULT_LOGS_DIR

    print("=" * 60)
    print("🚀 ANTIGRAVITY TO OBSIDIAN MIGRATION PIPELINE")
    print(f"Mode: {'DRY RUN (Preview Only - No Disk Changes)' if dry_run else 'LIVE EXECUTION'}")
    print(f"Source: {src_root}")
    print(f"Vault Logs Target: {logs_dir}")
    print("=" * 60)

    provider = AntigravityHistoryProvider(root_dir=src_root)
    archive_engine = ArchiveEngine(logs_dir=logs_dir)

    # 1. DISCOVER
    print("\n[Step 1/6] 🔍 Discovering Antigravity storage...")
    disc_report = provider.discover(source_root=src_root)
    print(f"  Found {len(disc_report.databases)} databases, {len(disc_report.conversation_stores)} conversation stores.")
    print(f"  Storage exists: {disc_report.exists}")

    # 2. INSPECT
    print("\n[Step 2/6] 🔬 Inspecting conversation database schema...")
    inspection_target = None
    if disc_report.conversation_stores:
        inspection_target = src_root / disc_report.conversation_stores[0]
    elif disc_report.databases:
        inspection_target = src_root / disc_report.databases[0]

    if inspection_target and inspection_target.exists():
        inspect_report = provider.inspect(inspection_target)
        print(f"  Target: {inspect_report.name} (Valid: {inspect_report.is_valid_source}, Readable: {inspect_report.readable})")
        print(f"  Tables: {list(inspect_report.tables.keys())}")
    else:
        print("  ⚠️ No primary SQLite conversation database found in standard locations.")

    # 3. EXTRACT & RECONCILE (via ArchiveEngine)
    print("\n[Step 3/6] 📦 Extracting & archiving conversations...")
    created_count = 0
    updated_count = 0
    errors: List[str] = []
    workspaces = set()

    for session in provider.extract(limit=limit):
        try:
            res = archive_engine.save_session(session=session, dry_run=dry_run, rebuild_mocs=False)
            workspaces.add(res["workspace"])
            if res["action"] == "CREATE":
                created_count += 1
            else:
                updated_count += 1
        except Exception as e:
            errors.append(f"Error archiving {session.conversation_id}: {e}")

    print(f"  Processed {created_count + updated_count} sessions across {len(workspaces)} workspaces.")
    print(f"  - New notes: {created_count}")
    print(f"  - Updated notes: {updated_count}")
    if errors:
        print(f"  - Errors encountered: {len(errors)}")

    # 4. REBUILD MOCs
    print("\n[Step 4/6] 🗺️ Updating Hub-and-Spoke MOC Index Hierarchy...")
    if dry_run:
        print("  DRY RUN: Skipped MOC index writing.")
        moc_res = {"main_moc": None, "sub_mocs": []}
    else:
        indexer = MOCIndexer(logs_dir=logs_dir)
        moc_res = indexer.build_all()
        print(f"  Main MOC: {Path(moc_res['main_moc']).name if moc_res['main_moc'] else 'N/A'}")
        print(f"  Updated {len(moc_res['sub_mocs'])} workspace Sub-MOCs.")

    # 5. VALIDATE VAULT
    print("\n[Step 5/6] 🔍 Validating vault integrity...")
    val_status = "SKIPPED (dry-run)"
    val_summary = {}
    if not dry_run and logs_dir.exists():
        validator = VaultValidator(logs_dir=logs_dir)
        val_report = validator.validate_all()
        val_status = val_report.status
        val_summary = val_report.to_dict()
        print(f"  Validation Status: {val_status}")
        print(f"  - Total Notes: {val_report.total_notes}")
        print(f"  - Workspaces: {val_report.total_workspaces}")
        print(f"  - Valid Frontmatter: {val_report.valid_frontmatter}")
        print(f"  - Broken Links: {val_report.broken_links}")
        print(f"  - Duplicate IDs: {len(val_report.duplicate_conversation_ids)}")

    # 6. SUMMARY REPORT
    print("\n[Step 6/6] 📊 Migration Summary")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'COMPLETED'}")
    print(f"Notes Created: {created_count}")
    print(f"Notes Updated: {updated_count}")
    print(f"Workspaces Covered: {len(workspaces)}")
    print(f"MOC Sub-indexes: {len(moc_res.get('sub_mocs', []))}")
    print(f"Vault Health: {val_status}")
    print("=" * 60)

    return {
        "mode": "dry_run" if dry_run else "live",
        "created": created_count,
        "updated": updated_count,
        "workspaces": list(workspaces),
        "errors": errors,
        "validation": val_summary
    }


def main():
    parser = argparse.ArgumentParser(description="Full migration pipeline for Antigravity logs to Obsidian.")
    parser.add_argument("--source", type=str, default=None, help="Antigravity root or conversations directory")
    parser.add_argument("--vault", type=str, default=None, help="Target Obsidian Antigravity Logs directory")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without modifying disk")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of databases to process")
    args = parser.parse_args()

    run_migration(
        source_root=Path(args.source) if args.source else None,
        target_logs_dir=Path(args.vault) if args.vault else None,
        dry_run=args.dry_run,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
