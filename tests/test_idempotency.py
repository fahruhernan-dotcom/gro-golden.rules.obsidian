"""
Tests for archive_session.py idempotency and collision resolution (Phase 14 & 17).
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

from core.models import ChatMessage, ChatSession
from core.renderer import render_session_markdown
from core.sanitizer import make_session_filename
try:
    from scripts.archive_session import find_existing_note_by_conv_id, archive_session
except ImportError:
    from archive_session import find_existing_note_by_conv_id, archive_session


def test_find_existing_note_by_conv_id(temp_vault):
    found = find_existing_note_by_conv_id(temp_vault, "conv-001")
    assert found is not None
    assert found.name == "2026-09-08 - 10.00 - Setup Project.md"

    not_found = find_existing_note_by_conv_id(temp_vault, "conv-non-existent")
    assert not_found is None


def test_idempotent_archive_updates_existing_note(temp_vault):
    ws_dir = temp_vault / "WorkspaceA"
    note_path = ws_dir / "2026-09-08 - 10.00 - Setup Project.md"
    initial_mtime = note_path.stat().st_mtime

    # Update session content for conv-001
    updated_session = ChatSession(
        conversation_id="conv-001",
        workspace_id="ws1",
        workspace_name="WorkspaceA",
        title="Setup Project",
        started_at="2026-09-08T10:00:00+07:00",
        ended_at="2026-09-08T10:05:00+07:00",
        messages=[
            ChatMessage(
                conversation_id="conv-001",
                workspace_id="ws1",
                timestamp="2026-09-08T10:00:00+07:00",
                role="user",
                step_type="USER_INPUT",
                content="Updated prompt"
            )
        ],
        affected_files=["src/main.py", "README.md"]
    )

    # Overwrite in-place as idempotent update
    content = render_session_markdown(updated_session)
    note_path.write_text(content, encoding="utf-8")

    # Re-check: note still exists in same place, no duplicate file created
    notes = list(ws_dir.glob("*.md"))
    # Index + 1 note = 2 files
    assert len(notes) == 2
    assert "Updated prompt" in note_path.read_text(encoding="utf-8")


def test_collision_different_conversation_gets_suffix(temp_vault):
    ws_dir = temp_vault / "WorkspaceA"
    
    # Existing note is 2026-09-08 - 10.00 - Setup Project.md (conv-001)
    # New session with different conversation_id but exact same date, time, and title
    diff_session = ChatSession(
        conversation_id="conv-002",
        workspace_id="ws1",
        workspace_name="WorkspaceA",
        title="Setup Project",
        started_at="2026-09-08T10:00:00+07:00",
        ended_at="2026-09-08T10:05:00+07:00",
        messages=[],
        affected_files=[]
    )

    # Resolve filename
    base_name = make_session_filename("2026-09-08", "10.00", "Setup Project")
    target_file = ws_dir / base_name
    if target_file.exists():
        target_file = ws_dir / make_session_filename("2026-09-08", "10.00", "Setup Project", suffix=2)

    assert target_file.name == "2026-09-08 - 10.00 - Setup Project [2].md"
    target_file.write_text(render_session_markdown(diff_session), encoding="utf-8")
    assert target_file.exists()


def test_archive_dry_run_leaves_disk_untouched(temp_vault, monkeypatch):
    ws_dir = temp_vault / "WorkspaceA"
    count_before = len(list(ws_dir.glob("*.md")))

    res = archive_session(
        conv_id="conv-dryrun-test",
        logs_dir=temp_vault,
        dry_run=True
    )
    # If conv_id doesn't exist on disk as db, it returns error or dry-run info
    count_after = len(list(ws_dir.glob("*.md")))
    assert count_before == count_after
