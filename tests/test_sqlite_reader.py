"""
Tests for database_reader.py and inspect_database.py
"""

import sys
import sqlite3
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
for p in (SKILL_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from providers.antigravity.sqlite import SafeDatabaseReader, DatabaseReadError
try:
    from scripts.inspect_database import inspect_database
except ImportError:
    from inspect_database import inspect_database


def test_reader_read_only_enforcement(valid_antigravity_db):
    """Ensure database cannot be mutated (PRAGMA query_only = ON)."""
    with SafeDatabaseReader(valid_antigravity_db) as reader:
        # SELECT works
        meta = reader.read_trajectory_meta()
        assert meta is not None
        assert meta["trajectory_id"] == "traj-test-123"

        # Attempt to insert or modify should raise DatabaseReadError / OperationalError
        with pytest.raises(Exception):
            cur = reader.conn.cursor()
            cur.execute("INSERT INTO trajectory_meta VALUES ('fail', 'fail', 'fail', 'fail')")


def test_reader_empty_db(empty_db):
    """Empty 0-byte file should raise DatabaseReadError gracefully."""
    with pytest.raises(DatabaseReadError):
        with SafeDatabaseReader(empty_db) as reader:
            reader.read_trajectory_meta()


def test_reader_corrupt_db(corrupt_db):
    """Corrupt file should raise DatabaseReadError without crashing process."""
    with pytest.raises(DatabaseReadError):
        with SafeDatabaseReader(corrupt_db) as reader:
            reader.read_trajectory_meta()


def test_inspect_valid_db(valid_antigravity_db):
    res = inspect_database(valid_antigravity_db)
    assert res["is_sqlite"] is True
    assert res["readable"] is True
    assert "trajectory_meta" in res["tables"]
    assert "steps" in res["tables"]
    assert res["detected_fields"]["conversation_id"] is True


def test_inspect_corrupt_db(corrupt_db):
    res = inspect_database(corrupt_db)
    assert res["is_sqlite"] is False
    assert res["readable"] is False
    assert res["error"] is not None


def test_inspect_unknown_schema_db(unknown_schema_db):
    res = inspect_database(unknown_schema_db)
    assert res["is_sqlite"] is True
    assert res["readable"] is True
    assert "foo" in res["tables"]
    assert res["detected_fields"]["conversation_id"] is False
