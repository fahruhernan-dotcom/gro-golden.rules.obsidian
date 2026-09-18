"""
Tests for core/identity.py - SessionIdentityResolver.
Verifies stable identity computation, fallback hash generation,
in-place update detection, and collision resolution ([2], [3]).
"""

import pytest
from pathlib import Path

from core.models import ChatMessage, ChatSession
from core.identity import SessionIdentityResolver
from core.renderer import render_session_to_markdown
from core.sanitizer import make_session_filename


def test_compute_stable_identity_primary():
    session = ChatSession(
        conversation_id="conv-primary-12345",
        workspace_id="ws1",
        workspace_name="SampleWorkspace",
        title="Test Task",
        started_at="2026-09-08T10:00:00+07:00",
        ended_at="2026-09-08T10:10:00+07:00"
    )
    ident = SessionIdentityResolver.compute_stable_identity(session)
    assert ident == "conv-primary-12345"


def test_compute_stable_identity_fallback_hash():
    session = ChatSession(
        conversation_id="",
        workspace_id="ws1",
        workspace_name="SampleWorkspace",
        title="Test Task",
        started_at="2026-09-08T10:00:00+07:00",
        ended_at="2026-09-08T10:10:00+07:00"
    )
    ident = SessionIdentityResolver.compute_stable_identity(session)
    assert len(ident) == 16
    assert ident.isalnum()

    # Deterministic: identical inputs produce identical hash
    session2 = ChatSession(
        conversation_id=None,
        workspace_id="ws1",
        workspace_name="SampleWorkspace",
        title="Test Task",
        started_at="2026-09-08T10:00:00+07:00",
        ended_at="2026-09-08T10:10:00+07:00"
    )
    assert SessionIdentityResolver.compute_stable_identity(session2) == ident


def test_find_existing_note(temp_vault):
    # temp_vault contains WorkspaceA / 2026-09-08 - 10.00 - Setup Project.md with conv-001
    found = SessionIdentityResolver.find_existing_note(temp_vault, "conv-001")
    assert found is not None
    assert found.name == "2026-09-08 - 10.00 - Setup Project.md"

    not_found = SessionIdentityResolver.find_existing_note(temp_vault, "nonexistent-id-999")
    assert not_found is None


def test_resolve_target_file_new_and_update(tmp_path):
    ws_folder = tmp_path / "WorkspaceX"
    ws_folder.mkdir(parents=True)

    session = ChatSession(
        conversation_id="conv-alpha",
        workspace_id="ws-x",
        workspace_name="WorkspaceX",
        title="Init DB",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:10:00+07:00"
    )
    base_name = "2026-09-08 - 12.00 - Init DB.md"

    # 1. New file -> CREATE
    target_file, action = SessionIdentityResolver.resolve_target_file(
        target_folder=ws_folder,
        base_filename=base_name,
        session=session
    )
    assert action == "CREATE"
    assert target_file.name == base_name

    # Write file with conv-alpha in frontmatter
    target_file.write_text(render_session_to_markdown(session), encoding="utf-8")

    # 2. Same conversation_id -> UPDATE (in-place)
    target_file2, action2 = SessionIdentityResolver.resolve_target_file(
        target_folder=ws_folder,
        base_filename=base_name,
        session=session
    )
    assert action2 == "UPDATE"
    assert target_file2 == target_file


def test_resolve_target_file_collision_suffix(tmp_path):
    ws_folder = tmp_path / "WorkspaceX"
    ws_folder.mkdir(parents=True)

    session_a = ChatSession(
        conversation_id="conv-session-A",
        workspace_id="ws-x",
        workspace_name="WorkspaceX",
        title="Duplicate Topic",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:10:00+07:00"
    )
    base_name = "2026-09-08 - 12.00 - Duplicate Topic.md"
    file_a = ws_folder / base_name
    file_a.write_text(render_session_to_markdown(session_a), encoding="utf-8")

    # Session B has a DIFFERENT conversation_id but exact same timestamp and title
    session_b = ChatSession(
        conversation_id="conv-session-B",
        workspace_id="ws-x",
        workspace_name="WorkspaceX",
        title="Duplicate Topic",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:10:00+07:00"
    )

    target_file_b, action_b = SessionIdentityResolver.resolve_target_file(
        target_folder=ws_folder,
        base_filename=base_name,
        session=session_b
    )
    assert action_b == "CREATE"
    assert target_file_b.name == "2026-09-08 - 12.00 - Duplicate Topic [2].md"

    # Write file B
    target_file_b.write_text(render_session_to_markdown(session_b), encoding="utf-8")

    # Session C also collides -> receives [3]
    session_c = ChatSession(
        conversation_id="conv-session-C",
        workspace_id="ws-x",
        workspace_name="WorkspaceX",
        title="Duplicate Topic",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:10:00+07:00"
    )
    target_file_c, action_c = SessionIdentityResolver.resolve_target_file(
        target_folder=ws_folder,
        base_filename=base_name,
        session=session_c
    )
    assert action_c == "CREATE"
    assert target_file_c.name == "2026-09-08 - 12.00 - Duplicate Topic [3].md"
