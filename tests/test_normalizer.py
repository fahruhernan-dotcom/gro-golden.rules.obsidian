"""
Tests for normalize_history.py and models.py
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

from core.models import ChatMessage, ChatSession, Workspace
try:
    from scripts.normalize_history import normalize_database_record
except ImportError:
    from normalize_history import normalize_database_record


def test_models_serialization(mock_session):
    d = mock_session.to_dict()
    assert d["conversation_id"] == "conv-abc-123"
    assert len(d["messages"]) == 2
    assert d["workspace_name"] == "TernakOS"

    restored = ChatSession.from_dict(d)
    assert restored.conversation_id == mock_session.conversation_id
    assert restored.title == mock_session.title
    assert len(restored.messages) == 2
    assert restored.messages[0].role == "user"
    assert restored.messages[1].role == "assistant"


def test_normalize_empty_record(tmp_path):
    db_file = tmp_path / "dummy.db"
    res = normalize_database_record(
        db_file=db_file,
        trajectory_meta=None,
        metadata_blob=None,
        steps=[]
    )
    # Empty steps should return None
    assert res is None


def test_normalize_valid_record(tmp_path):
    db_file = tmp_path / "conv-999.db"
    meta = {"trajectory_id": "conv-999"}
    # Trajectory metadata blob containing workspace path
    blob = b"\n\x1a/Users/dev/Projects/TernakOS\x12\x08TernakOS"
    # Mock step tuples: (idx, step_type, status, metadata, task_details, step_payload)
    # Step type 14 = user input, 15 = assistant
    steps = [
        (1, 14, 1, None, None, b'\x9a\x01\x15\x12\x13Hello from user\x28\x80\x80\x80\x80\x05'),
        (2, 15, 1, None, None, b'\xa2\x01\x18\x0a\x16Hello from assistant')
    ]

    session = normalize_database_record(db_file, meta, blob, steps)
    assert session is not None
    assert session.conversation_id == "conv-999"
    assert len(session.messages) >= 1
