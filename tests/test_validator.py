"""
Tests for validate_vault.py (Phase 16).
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.validator import VaultValidator, parse_frontmatter


def test_validator_pass_on_clean_vault(temp_vault):
    validator = VaultValidator(temp_vault)
    is_valid = validator.validate()
    report = validator.format_report()

    assert is_valid is True
    assert "STATUS: PASS" in report
    assert validator.broken_links == 0
    assert validator.duplicate_conv_ids == 0
    assert validator.invalid_frontmatter == 0


def test_validator_fails_missing_main_moc(temp_vault):
    main_moc = temp_vault / "Index - Antigravity Logs.md"
    main_moc.unlink()

    validator = VaultValidator(temp_vault)
    is_valid = validator.validate()
    assert is_valid is False
    assert any("Main MOC missing" in issue for issue in validator.issues)


def test_validator_fails_on_duplicate_conv_ids(temp_vault):
    ws_dir = temp_vault / "WorkspaceA"
    dup_note = ws_dir / "2026-09-08 - 11.00 - Duplicate Note.md"
    # Same conversation_id: conv-001
    dup_note.write_text("""---
tags:
  - type/ai-log
  - source/antigravity
date: 2026-09-08
time: "11:00"
status: archived
workspace: WorkspaceA
conversation_id: "conv-001"
---
# Duplicate Note
> [!example]- 📜 Transkrip Dialog Lengkap
> **User:** Hi
""", encoding="utf-8")

    validator = VaultValidator(temp_vault)
    is_valid = validator.validate()
    assert is_valid is False
    assert validator.duplicate_conv_ids == 1


def test_validator_fails_on_broken_links(temp_vault):
    ws_dir = temp_vault / "WorkspaceA"
    moc = ws_dir / "Index - WorkspaceA.md"
    content = moc.read_text(encoding="utf-8")
    content += "\n| [[Non-Existent Note]] | Broken |"
    moc.write_text(content, encoding="utf-8")

    validator = VaultValidator(temp_vault)
    is_valid = validator.validate()
    assert is_valid is False
    assert validator.broken_links >= 1
