"""
Obsidian Markdown Renderer for ChatSession objects.
Implements Phase 9 & Phase 10: High-fidelity Obsidian Markdown and raw transcript safety.
"""

import re
from typing import Dict, Any, List
from models import ChatSession, ChatMessage
from timestamp_parser import parse_timestamp, format_dt

def render_session_markdown(session: ChatSession) -> str:
    """
    Renders a ChatSession into production-grade Obsidian Markdown.
    """
    # 1. Parse dates
    dt_start, _ = parse_timestamp(session.started_at)
    formatted = format_dt(dt_start)
    date_str = formatted["date"]
    time_str = formatted["time"]

    # 2. Extract purpose / main goal from first user turn
    user_msgs = [m for m in session.messages if m.role == "user"]
    assistant_msgs = [m for m in session.messages if m.role == "assistant"]

    first_req = user_msgs[0].content[:250].replace("\n", " ").strip() if user_msgs else "Permintaan teknis otomatis."
    first_resp = assistant_msgs[0].content[:250].replace("\n", " ").strip() if assistant_msgs else "Hasil eksekusi tugas."

    # 3. Key dialog bullet points (top 5 turns)
    dialog_bullets: List[str] = []
    turn_idx = 1
    # Pair up user and assistant messages
    msg_i = 0
    while msg_i < len(session.messages) and turn_idx <= 6:
        msg = session.messages[msg_i]
        if msg.role == "user":
            u_snip = msg.content[:150].replace("\n", " ").strip()
            dialog_bullets.append(f"- **Pengguna:** {u_snip}")
            # Look ahead for immediate assistant response
            if msg_i + 1 < len(session.messages) and session.messages[msg_i + 1].role == "assistant":
                a_snip = session.messages[msg_i + 1].content[:180].replace("\n", " ").strip()
                dialog_bullets.append(f"- **Antigravity:** {a_snip}")
                msg_i += 1
            turn_idx += 1
        msg_i += 1

    dialog_section = "\n".join(dialog_bullets) if dialog_bullets else "- Sesi interaksi langsung tanpa dialog panjang."

    # 4. Affected files
    if session.affected_files:
        clean_files = [
            f.strip("[]()\",' ") for f in session.affected_files
            if f.strip() and not any(bad in f for bad in ("(?:", "..", "/*", "*/", "<", ">", "|", " "))
        ]
        file_bullets = [f"- `{f}`" for f in clean_files[:25]]
        if len(clean_files) > 25:
            file_bullets.append(f"- *... dan {len(clean_files) - 25} berkas lainnya.*")
        files_section = "\n".join(file_bullets) if file_bullets else "- Tidak ada berkas yang dimodifikasi secara langsung."
    else:
        files_section = "- Tidak ada berkas yang dimodifikasi secara langsung."

    # 5. Metadata section
    metadata_lines = [
        f"- **ID Percakapan:** `{session.conversation_id}`",
        f"- **Workspace:** `{session.workspace_name}`",
        f"- **Waktu Mulai:** `{session.started_at}`",
        f"- **Waktu Selesai:** `{session.ended_at}`",
        f"- **Jumlah Pesan:** `{len(session.messages)}` pesan"
    ]
    if session.metadata.get("original_workspace_path"):
        metadata_lines.append(f"- **Direktori Asal:** `{session.metadata['original_workspace_path']}`")
    metadata_section = "\n".join(metadata_lines)

    # 6. Raw Transcript with Safe Blockquote formatting (Phase 10)
    transcript_blocks: List[str] = []
    
    current_role = None
    for msg in session.messages:
        m_dt, _ = parse_timestamp(msg.timestamp)
        m_time = format_dt(m_dt)["time"]
        role_title = "User" if msg.role == "user" else "Assistant"

        transcript_blocks.append(f"> **{role_title} — {m_time}**")
        transcript_blocks.append(">")

        # Safely wrap content into blockquote
        for line in msg.content.splitlines():
            # If line is empty
            if not line.strip():
                transcript_blocks.append(">")
            else:
                # Prepend with '> '
                transcript_blocks.append(f"> {line}")
        transcript_blocks.append(">")

    raw_transcript = "\n".join(transcript_blocks) if transcript_blocks else "> *(Tidak ada pesan dialog tersimpan)*"

    md = f"""---
tags:
  - type/ai-log
  - source/antigravity
date: {date_str}
time: "{time_str}"
status: archived
workspace: "{session.workspace_name}"
conversation_id: "{session.conversation_id}"
up: "[[Index - {session.workspace_name}]]"
sub_hub: "[[Index - {session.workspace_name}]]"
---

# {session.title}

## 🎯 Keluaran Tujuan
- **Permintaan Pengguna:** {first_req}
- **Hasil Utama:** {first_resp}

## 💬 Poin Dialog Kunci
{dialog_section}

## 📁 File yang Terpengaruh
{files_section}

## 🧩 Metadata
{metadata_section}
- 🔗 **Sub-Indeks:** [[Index - {session.workspace_name}]]

> [!example]- 📜 Transkrip Dialog Lengkap
>
{raw_transcript}
"""
    return md


render_session_to_markdown = render_session_markdown
