"""
Tests for raw transcript safety and formatting (Phase 10).
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.models import ChatMessage, ChatSession
from core.renderer import render_session_markdown


def test_transcript_preserves_code_blocks():
    code_content = "def hello():\n    print('Hello World')\n    return True"
    msg = ChatMessage(
        conversation_id="conv-t1",
        workspace_id="ws1",
        timestamp="2026-09-08T12:00:00+07:00",
        role="assistant",
        step_type="PLANNER_RESPONSE",
        content=f"Here is code:\n```python\n{code_content}\n```"
    )
    session = ChatSession(
        conversation_id="conv-t1",
        workspace_id="ws1",
        workspace_name="TestWS",
        title="Code Test",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:01:00+07:00",
        messages=[msg],
        affected_files=[]
    )

    md = render_session_markdown(session)
    assert "> ```python" in md
    assert "> def hello():" in md
    assert "> ```" in md


def test_transcript_nested_blockquotes_and_horizontal_rules():
    content = "> Quote line 1\n>> Nested quote\n\n---\nDivider text\n[[LinkedNote]]"
    msg = ChatMessage(
        conversation_id="conv-t2",
        workspace_id="ws1",
        timestamp="2026-09-08T12:00:00+07:00",
        role="user",
        step_type="USER_INPUT",
        content=content
    )
    session = ChatSession(
        conversation_id="conv-t2",
        workspace_id="ws1",
        workspace_name="TestWS",
        title="Quote Test",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:01:00+07:00",
        messages=[msg],
        affected_files=[]
    )

    md = render_session_markdown(session)
    assert "> > Quote line 1" in md
    assert "> >> Nested quote" in md
    assert "> ---" in md
    assert "[[LinkedNote]]" in md


def test_transcript_empty_messages():
    session = ChatSession(
        conversation_id="conv-empty",
        workspace_id="ws1",
        workspace_name="TestWS",
        title="Empty Test",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:01:00+07:00",
        messages=[],
        affected_files=[]
    )
    md = render_session_markdown(session)
    assert "> *(Tidak ada pesan dialog tersimpan)*" in md


def test_transcript_large():
    # 300 messages
    msgs = [
        ChatMessage(
            conversation_id="conv-large",
            workspace_id="ws1",
            timestamp="2026-09-08T12:00:00+07:00",
            role="user" if i % 2 == 0 else "assistant",
            step_type="USER_INPUT" if i % 2 == 0 else "PLANNER_RESPONSE",
            content=f"Message turn #{i} with detailed explanation and logs."
        )
        for i in range(300)
    ]
    session = ChatSession(
        conversation_id="conv-large",
        workspace_id="ws1",
        workspace_name="TestWS",
        title="Large Transcript Test",
        started_at="2026-09-08T12:00:00+07:00",
        ended_at="2026-09-08T12:30:00+07:00",
        messages=msgs,
        affected_files=[]
    )
    md = render_session_markdown(session)
    assert "Message turn #0" in md
    assert "Message turn #299" in md
