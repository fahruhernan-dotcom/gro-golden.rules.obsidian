"""
Tests for markdown_renderer.py
"""

import sys
from pathlib import Path
import pytest

TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.renderer import render_session_markdown
from core.validator import parse_frontmatter


def test_render_session_markdown(mock_session):
    md = render_session_markdown(mock_session)

    # 1. Frontmatter
    fm, valid = parse_frontmatter(md)
    assert valid is True
    assert "type/ai-log" in fm["tags"]
    assert "source/antigravity" in fm["tags"]
    assert fm["workspace"] == "DemoApp"
    assert fm["conversation_id"] == "conv-abc-123"

    # 2. Sections
    assert "# Setup Supabase Auth Next.js" in md
    assert "## 🎯 Keluaran Tujuan" in md
    assert "## 💬 Poin Dialog Kunci" in md
    assert "## 📁 File yang Terpengaruh" in md
    assert "## 📋 Metadata" in md

    # 3. Affected Files (backticks, never wikilinks to avoid graph view ghost nodes)
    assert "- `src/lib/supabase.ts`" in md

    # 4. Workspace Sub-MOC link
    assert "[[Index - DemoApp]]" in md

    # 5. Folded transcript callout
    assert "> [!example]- 📖 Transkrip Dialog Lengkap" in md
    assert "**User • 14:30:00**" in md
    assert "**Assistant • 14:31:00**" in md
