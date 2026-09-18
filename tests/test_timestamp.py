"""
Tests for timestamp_parser.py
"""

import sys
from pathlib import Path
from datetime import datetime
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.timestamp import parse_timestamp, format_dt


def test_parse_unix_seconds():
    # 1773000000 -> 2026-03-08
    dt, orig = parse_timestamp(1773000000)
    assert dt.year == 2026
    f = format_dt(dt)
    assert "2026-" in f["date"]


def test_parse_unix_milliseconds():
    # 1773000000000
    dt, orig = parse_timestamp(1773000000000)
    assert dt.year == 2026
    assert orig == 1773000000000


def test_parse_unix_microseconds():
    # 1773000000000000
    dt, orig = parse_timestamp(1773000000000000)
    assert dt.year == 2026


def test_parse_iso8601():
    dt, orig = parse_timestamp("2026-09-08T14:30:00+07:00")
    f = format_dt(dt)
    assert f["date"] == "2026-09-08"
    assert f["time"] == "14:30"
    assert f["file_time"] == "14.30"


def test_parse_sqlite_datetime():
    dt, orig = parse_timestamp("2026-09-08 07:30:00")
    assert dt.year == 2026


def test_parse_protobuf_timestamp_dict():
    pb_dict = {"seconds": 1773000000, "nanos": 500000000}
    dt, orig = parse_timestamp(pb_dict)
    assert dt.year == 2026


def test_parse_malformed_timestamp():
    dt, orig = parse_timestamp("not-a-timestamp-xyz")
    # Should safely fallback to now without raising exception
    assert isinstance(dt, datetime)
