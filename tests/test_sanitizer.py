"""
Tests for title_sanitizer.py
"""

import sys
from pathlib import Path
import pytest

# Ensure skill directory in sys.path for IDE analyzer
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.sanitizer import (
    sanitize_filename,
    generate_title_from_prompt,
    make_session_filename,
    generate_session_filename
)


def test_sanitize_illegal_characters():
    dirty = 'Project / Path \\ With: Colons * Asterisks ? Questions " Quotes < Less > Greater | Pipes'
    clean = sanitize_filename(dirty)
    for char in r'\/:*?"<>|':
        assert char not in clean


def test_sanitize_wikilink_characters():
    dirty = "Setup @[current_problems] and [features]"
    clean = sanitize_filename(dirty)
    assert "[" not in clean
    assert "]" not in clean
    assert "@" not in clean


def test_sanitize_windows_reserved_names():
    for res in ["CON", "prn", "Aux", "NUL", "COM1", "LPT2"]:
        clean = sanitize_filename(res)
        assert clean.startswith("_") or clean != res.upper()


def test_sanitize_trailing_dots_and_spaces():
    dirty = "Setup Project ....   "
    clean = sanitize_filename(dirty)
    assert not clean.endswith(".")
    assert not clean.endswith(" ")


def test_sanitize_empty_string():
    clean = sanitize_filename("")
    assert clean == "Catatan Tanpa Judul"


def test_sanitize_long_string():
    long_str = "This is an extremely long title for a note that goes on and on and contains a lot of unnecessary repetitive words"
    clean = sanitize_filename(long_str, max_length=40)
    assert len(clean) <= 45


def test_generate_title_from_prompt():
    prompt = "# Setup 9Router configuration\nPlease help me setup routing in Next.js"
    title = generate_title_from_prompt(prompt)
    assert "Setup 9Router" in title
    assert "#" not in title


def test_make_session_filename():
    fn1 = make_session_filename("2026-09-08", "14.30", "Setup 9Router")
    assert fn1 == "2026-09-08 - 14.30 - Setup 9Router.md"

    fn2 = make_session_filename("2026-09-08", "14.30", "Setup 9Router", suffix=2)
    assert fn2 == "2026-09-08 - 14.30 - Setup 9Router [2].md"
