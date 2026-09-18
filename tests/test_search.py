"""
Tests for search_vault.py (Phase 15).
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
for p in (SKILL_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from scripts.search_vault import search_vault
except ImportError:
    from search_vault import search_vault


def test_search_by_query_in_title(temp_vault):
    results = search_vault(
        query="Setup Project",
        logs_dir=temp_vault
    )
    assert len(results) >= 1
    assert results[0]["title"] == "Setup Project"
    assert results[0]["workspace"] == "WorkspaceA"


def test_search_by_query_in_content(temp_vault):
    results = search_vault(
        query="Initial setup",
        logs_dir=temp_vault
    )
    assert len(results) >= 1
    assert "Setup Project" in results[0]["title"]


def test_search_filter_by_workspace(temp_vault):
    # Matches in WorkspaceA
    res_a = search_vault(
        query="Setup",
        workspace="WorkspaceA",
        logs_dir=temp_vault
    )
    assert len(res_a) == 1

    # Should not match in WorkspaceB
    res_b = search_vault(
        query="Setup",
        workspace="WorkspaceB",
        logs_dir=temp_vault
    )
    assert len(res_b) == 0


def test_search_filter_by_date(temp_vault):
    res_after = search_vault(
        query="Setup",
        after="2026-09-01",
        logs_dir=temp_vault
    )
    assert len(res_after) >= 1

    res_future = search_vault(
        query="Setup",
        after="2026-12-31",
        logs_dir=temp_vault
    )
    assert len(res_future) == 0


def test_search_limit(temp_vault):
    res = search_vault(
        query="Setup",
        limit=1,
        logs_dir=temp_vault
    )
    assert len(res) <= 1
