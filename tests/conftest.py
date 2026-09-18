"""
Pytest configuration and test fixtures for obsidian-vault test suite.
"""

import os
import sys
import sqlite3
import pytest
from pathlib import Path
from datetime import datetime

# Add skill and scripts directory to sys.path
TESTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TESTS_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.models import ChatMessage, ChatSession, Workspace


@pytest.fixture
def temp_vault(tmp_path):
    """Creates a temporary Obsidian logs directory structure with Main MOC and Workspace MOCs."""
    logs_dir = tmp_path / "00_Meta" / "Antigravity Logs"
    ws1_dir = logs_dir / "WorkspaceA"
    ws2_dir = logs_dir / "WorkspaceB"
    ws1_dir.mkdir(parents=True)
    ws2_dir.mkdir(parents=True)

    # Main MOC
    main_moc = logs_dir / "Index - Antigravity Logs.md"
    main_moc.write_text("""---
tags:
  - type/master-hub
  - type/moc
  - source/antigravity
date: 2026-09-08
status: active
---

# 🌐 Hub Indeks Utama: Antigravity Session Logs

| Workspace | Sub-Indeks |
|---|---|
| WorkspaceA | [[Index - WorkspaceA]] |
| WorkspaceB | [[Index - WorkspaceB]] |
""", encoding="utf-8")

    # Workspace A MOC
    ws1_moc = ws1_dir / "Index - WorkspaceA.md"
    ws1_moc.write_text("""---
tags:
  - type/sub-hub
  - type/moc
  - source/antigravity
workspace: "WorkspaceA"
up: "[[Index - Antigravity Logs]]"
---

# 📁 Hub: WorkspaceA

| Sesi | Topik |
|---|---|
| [[2026-09-08 - 10.00 - Setup Project]] | Setup Project |
""", encoding="utf-8")

    # Sample Note in Workspace A
    note_a = ws1_dir / "2026-09-08 - 10.00 - Setup Project.md"
    note_a.write_text("""---
tags:
  - type/ai-log
  - source/antigravity
date: 2026-09-08
time: "10:00"
status: archived
workspace: WorkspaceA
conversation_id: "conv-001"
---

# Setup Project

## 🎯 Keluaran Tujuan
Initial setup

## 💬 Poin Dialog Kunci
- User requested project setup

## 📁 File yang Terpengaruh
- [[src/main.py]]

## 🧩 Metadata
- 🆔 **ID Sesi:** `conv-001`
- 🔗 **Sub-Indeks:** [[Index - WorkspaceA]]

> [!example]- 📜 Transkrip Dialog Lengkap
>
> **User — 10:00**
>
> Setup project
>
> **Assistant — 10:01**
>
> Done setting up
""", encoding="utf-8")

    # Workspace B MOC
    ws2_moc = ws2_dir / "Index - WorkspaceB.md"
    ws2_moc.write_text("""---
tags:
  - type/sub-hub
  - type/moc
  - source/antigravity
workspace: "WorkspaceB"
up: "[[Index - Antigravity Logs]]"
---

# 📁 Hub: WorkspaceB

| Sesi | Topik |
|---|---|
""", encoding="utf-8")

    return logs_dir


@pytest.fixture
def empty_db(tmp_path):
    """Creates a 0-byte file mimicking an empty or uninitialized DB."""
    db_path = tmp_path / "empty.db"
    db_path.touch()
    return db_path


@pytest.fixture
def corrupt_db(tmp_path):
    """Creates a corrupt file with non-SQLite header bytes."""
    db_path = tmp_path / "corrupt.db"
    db_path.write_bytes(b"THIS IS NOT A SQLITE DATABASE HEADER GIBBERISH")
    return db_path


@pytest.fixture
def unknown_schema_db(tmp_path):
    """Creates a valid SQLite database but with unexpected table schema."""
    db_path = tmp_path / "unknown_schema.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE foo (id INT, note TEXT)")
    cur.execute("INSERT INTO foo VALUES (1, 'hello')")
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def valid_antigravity_db(tmp_path):
    """Creates a valid mock SQLite database matching Antigravity schema."""
    db_path = tmp_path / "valid_conv.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE trajectory_meta (
            trajectory_id TEXT,
            cascade_id TEXT,
            trajectory_type TEXT,
            source TEXT
        )
    """)
    cur.execute("INSERT INTO trajectory_meta VALUES ('traj-test-123', 'casc-456', 'code', 'ide')")

    cur.execute("""
        CREATE TABLE steps (
            idx INTEGER,
            step_type INTEGER,
            status INTEGER,
            has_subtrajectory INTEGER,
            metadata BLOB,
            error_details BLOB,
            permissions BLOB,
            task_details BLOB,
            render_info BLOB,
            step_payload BLOB,
            step_format INTEGER
        )
    """)

    cur.execute("CREATE TABLE gen_metadata (idx INTEGER, data BLOB, size INTEGER)")
    cur.execute("CREATE TABLE trajectory_metadata_blob (id TEXT, data BLOB)")
    cur.execute("CREATE TABLE executor_metadata (idx INTEGER, data BLOB)")
    cur.execute("CREATE TABLE parent_references (idx INTEGER, data BLOB)")
    cur.execute("CREATE TABLE battle_mode_infos (idx INTEGER, data BLOB)")

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def mock_session():
    """Returns a valid populated ChatSession object for testing."""
    msgs = [
        ChatMessage(
            conversation_id="conv-abc-123",
            workspace_id="ws-uuid-1",
            timestamp="2026-09-08T14:30:00+07:00",
            role="user",
            step_type="USER_INPUT",
            content="Bantu konfigurasi Supabase Auth di Next.js",
            metadata={"step_idx": 1}
        ),
        ChatMessage(
            conversation_id="conv-abc-123",
            workspace_id="ws-uuid-1",
            timestamp="2026-09-08T14:31:00+07:00",
            role="assistant",
            step_type="PLANNER_RESPONSE",
            content="Tentu, berikut konfigurasi auth helper untuk Next.js:\n```typescript\nimport { createClient } from '@supabase/supabase-js';\n```",
            metadata={"step_idx": 2}
        )
    ]
    return ChatSession(
        conversation_id="conv-abc-123",
        workspace_id="ws-uuid-1",
        workspace_name="TernakOS",
        title="Setup Supabase Auth Next.js",
        started_at="2026-09-08T14:30:00+07:00",
        ended_at="2026-09-08T14:35:00+07:00",
        messages=msgs,
        affected_files=["src/lib/supabase.ts", "src/app/auth/callback/route.ts"],
        metadata={"source": "antigravity"}
    )
