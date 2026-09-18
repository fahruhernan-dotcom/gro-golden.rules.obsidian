"""
Deterministic Markdown Renderer for Obsidian Vault Notes.
Produces standard Frontmatter, Structured Sections, Navigation Banners,
Concept Nodes, and Collapsible Full Transcripts.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import ChatSession, ChatMessage
from .timestamp import parse_timestamp, format_dt


def clean_summary_text(text: str, max_length: int = 350) -> str:
    """Cleans up internal instructions, tags, and formatting for summary display."""
    if not text:
        return "Tidak ada ringkasan teks."

    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if len(cleaned) > max_length:
        return cleaned[:max_length].rstrip() + "..."
    return cleaned


def render_session_markdown(session: ChatSession) -> str:
    """
    Renders a canonical ChatSession into standard Obsidian Markdown.
    Includes atomic capacity metadata, episodic navigation, and concept wikilinks.
    """
    # 1. Parse Timestamps
    start_dt, _ = parse_timestamp(session.started_at)
    formatted = format_dt(start_dt)
    date_str = formatted["date"]
    time_str = formatted["time"]

    # 2. Extract Key Summaries
    first_req = "Eksplorasi dan diskusi teknis."
    first_resp = "Solusi dan langkah eksekusi."

    for msg in session.messages:
        if msg.role == "user" and first_req == "Eksplorasi dan diskusi teknis.":
            first_req = clean_summary_text(msg.content)
        elif msg.role == "assistant" and first_resp == "Solusi dan langkah eksekusi.":
            first_resp = clean_summary_text(msg.content)

    # 3. Build Dialog Highlights (up to 5 key turns)
    dialog_points = []
    user_turns = [m for m in session.messages if m.role == "user"]
    for idx, u_msg in enumerate(user_turns[:5], 1):
        summary_turn = clean_summary_text(u_msg.content, max_length=150)
        dialog_points.append(f"- **Poin #{idx}:** {summary_turn}")

    dialog_section = "\n".join(dialog_points) if dialog_points else "- *(Diskusi teknis interaktif)*"

    # 4. Self-Improvement Learnings
    from .self_improvement import SelfImprovementEngine
    learnings = SelfImprovementEngine.analyze_session(session.messages, session.workspace_name) if SelfImprovementEngine else []
    if learnings:
        learning_lines = ["## 🧠 Pelajaran Berkelanjutan (Self-Improvement)"]
        for idx, l in enumerate(learnings, 1):
            learning_lines.append(f"- **Pelajaran #{idx} ({l['category']}):**")
            learning_lines.append(f"  - 💬 *Koreksi Pengguna:* \"{l['user_quote']}\"")
            learning_lines.append(f"  - 🎯 *Aturan Evolved:* {l['directive']}")
        self_improvement_section = "\n" + "\n".join(learning_lines) + "\n"
    else:
        self_improvement_section = ""

    # 5. Affected Files Section
    if session.affected_files:
        files_lines = [f"- `{f}`" for f in sorted(session.affected_files)[:15]]
        if len(session.affected_files) > 15:
            files_lines.append(f"- *...dan {len(session.affected_files) - 15} file lainnya.*")
        files_section = "\n".join(files_lines)
    else:
        files_section = "- *(Tidak ada file yang termodifikasi)*"

    # 6. Metadata Block
    end_dt, _ = parse_timestamp(session.ended_at)
    metadata_section = f"""- 🆔 **Conversation ID:** `{session.conversation_id}`
- 🏷️ **Workspace:** `{session.workspace_name}`
- ⏱️ **Mulai:** `{start_dt.strftime('%Y-%m-%d %H:%M:%S')}`
- 🏁 **Selesai:** `{end_dt.strftime('%Y-%m-%d %H:%M:%S')}`
- 💬 **Jumlah Pesan:** {len(session.messages)}
- 📑 **Bagian:** Part {session.part} dari {session.total_parts}"""

    # 7. Collapsible Transcript
    transcript_blocks = []
    for msg in session.messages:
        m_dt, _ = parse_timestamp(msg.timestamp)
        m_time = m_dt.strftime("%H:%M:%S")
        role_title = "User" if msg.role == "user" else "Assistant"

        transcript_blocks.append(f"> **{role_title} • {m_time}**")
        transcript_blocks.append(">")

        for line in msg.content.splitlines():
            if not line.strip():
                transcript_blocks.append(">")
            else:
                transcript_blocks.append(f"> {line}")
        transcript_blocks.append(">")

    raw_transcript = "\n".join(transcript_blocks) if transcript_blocks else "> *(Tidak ada pesan dialog tersimpan)*"

    # 8. Concept Nodes & Navigation Banner
    concepts_yaml = ""
    if session.concepts:
        c_yaml_lines = [f'  - "[[{c}]]"' for c in session.concepts]
        concepts_yaml = "concepts:\n" + "\n".join(c_yaml_lines)
    else:
        concepts_yaml = "concepts: []"

    prev_part_yaml = f'"{session.prev_part}"' if session.prev_part else "null"
    next_part_yaml = f'"{session.next_part}"' if session.next_part else "null"

    nav_banner = ""
    if session.prev_part or session.next_part:
        p_link = f"[[{session.prev_part}]]" if session.prev_part else "*(Awal Sesi)*"
        n_link = f"[[{session.next_part}]]" if session.next_part else "*(Akhir Sesi / Aktif)*"
        nav_banner = f"> [!info] 🧭 **Navigasi Sesi Episodik (Part {session.part}/{session.total_parts})**\n> ⏮️ **Sebelumnya:** {p_link} | ⏭️ **Selanjutnya:** {n_link}\n\n"

    concepts_section = ""
    if session.concepts:
        c_links = " • ".join([f"[[{c}]]" for c in session.concepts])
        concepts_section = f"\n## 🧠 Node Konsep Terkait (Graph Clusters)\n{c_links}\n"

    md = f"""---
tags:
  - type/ai-log
  - source/antigravity
date: {date_str}
time: "{time_str}"
status: archived
workspace: "{session.workspace_name}"
conversation_id: "{session.conversation_id}"
part: {session.part}
total_parts: {session.total_parts}
prev_part: {prev_part_yaml}
next_part: {next_part_yaml}
up: "[[Index - {session.workspace_name}]]"
sub_hub: "[[Index - {session.workspace_name}]]"
{concepts_yaml}
---

# {session.title}

{nav_banner}## 🎯 Keluaran Tujuan
- **Permintaan Pengguna:** {first_req}
- **Hasil Utama:** {first_resp}

## 💬 Poin Dialog Kunci
{dialog_section}
{self_improvement_section}{concepts_section}
## 📁 File yang Terpengaruh
{files_section}

## 📋 Metadata
{metadata_section}
- 🔗 **Sub-Indeks:** [[Index - {session.workspace_name}]]

> [!example]- 📖 Transkrip Dialog Lengkap
>
{raw_transcript}
"""
    return md


render_session_to_markdown = render_session_markdown
