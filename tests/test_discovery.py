"""
Tests for discover_antigravity.py
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

# pyright: reportMissingImports=false
try:
    from scripts.discover_antigravity import discover_antigravity
except ImportError:
    from discover_antigravity import discover_antigravity  # type: ignore[import-not-found]


def test_discover_non_existent_directory(tmp_path):
    non_existent = tmp_path / "does_not_exist"
    report = discover_antigravity(source_root=non_existent)
    assert report["exists"] is False
    assert len(report["databases"]) == 0


def test_discover_antigravity_files(tmp_path):
    # Setup test file tree
    conv_dir = tmp_path / "conversations"
    conv_dir.mkdir()
    (conv_dir / "abc.db").touch()
    (conv_dir / "abc.db-wal").touch()
    (conv_dir / "abc.db-shm").touch()
    (conv_dir / "def.sqlite").touch()
    (conv_dir / "ghi.pb").touch()

    meta_file = tmp_path / "metadata.json"
    meta_file.write_text('{"key": "value"}', encoding="utf-8")

    report = discover_antigravity(source_root=tmp_path)
    assert report["exists"] is True
    assert len(report["databases"]) >= 2
    assert len(report["wal_shm_files"]) >= 2
    assert len(report["proto_files"]) >= 1
    assert len(report["json_files"]) >= 1
    assert report["newest_timestamp"] is not None
