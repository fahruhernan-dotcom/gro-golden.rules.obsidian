"""
Tests for build_index.py (Phase 12 & 13: 2-Tier MOC Architecture).
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.indexer import build_all_indexes
from core.validator import extract_wikilinks


def test_build_all_indexes(temp_vault):
    build_all_indexes(logs_dir=temp_vault)

    main_moc = temp_vault / "Index - Antigravity Logs.md"
    assert main_moc.exists()

    content = main_moc.read_text(encoding="utf-8")
    links = extract_wikilinks(content)

    # 1. Main MOC only points to Workspace MOCs
    for link in links:
        if link in ("Index - Antigravity Logs", "Index - [Workspace]"):
            continue
        assert link.startswith("Index - ")
        assert not link.startswith("2026-")

    assert "Index - WorkspaceA" in links

    # 2. Workspace MOC points to notes inside Workspace A
    ws1_moc = temp_vault / "WorkspaceA" / "Index - WorkspaceA.md"
    assert ws1_moc.exists()
    ws1_content = ws1_moc.read_text(encoding="utf-8")
    ws1_links = extract_wikilinks(ws1_content)

    assert "Index - Antigravity Logs" in ws1_links
    assert any("2026-09-08 - 10.00 - Setup Project" in l for l in ws1_links)
