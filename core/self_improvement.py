"""
Self-Improvement Engine for Persistent Obsidian Memory System.
Extracts user corrections, root causes of mistakes, and actionable directives
to create a continuous learning loop directly within Obsidian Vault Lemonaru.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

CORRECTION_PATTERNS = [
    r"(?i)(?:kan aku dah bilang|kan sudah dibilang|kenapa kamu|kok kamu|bukan begitu|bukan itu)",
    r"(?i)(?:apa perintahku kurang jelas|nggak nyambung|jangan|harusnya|ya ampun|astaga)",
    r"(?i)(?:sesuai dengan isi|jangan asal|salah folder|salah tempat|di folder .agent)",
    r"(?i)(?:berapa informasi|kapasitas|batasi|chatnya ilang|ga efektif|make a plan)"
]

DEFAULT_LEARNING_LOG = Path("D:/Dokumen/02_Kerja_Profesional/Myself/Vault/Lemonaru/00_Meta/Learnings/AI_Continuous_Learning_Log.md")


class SelfImprovementEngine:
    """
    Extracts lessons learned and human corrections from chat sessions
    and writes them to both the session note and global learning log.
    """

    @classmethod
    def analyze_session(cls, messages: List[Any], workspace_name: str = "") -> List[Dict[str, str]]:
        learnings: List[Dict[str, str]] = []
        user_msgs = [m for m in messages if getattr(m, "role", "") == "user"]

        for msg in user_msgs:
            content = getattr(msg, "content", "")
            raw = re.sub(r"<[^>]+>", " ", content).strip()

            for pattern in CORRECTION_PATTERNS:
                matches = re.findall(pattern, raw)
                if matches:
                    category = cls._categorize_correction(raw)
                    directive = cls._distill_directive(raw, category)
                    learnings.append({
                        "user_quote": raw[:250].replace("\n", " ").strip(),
                        "category": category,
                        "directive": directive
                    })
                    break

        return learnings

    @staticmethod
    def _categorize_correction(text: str) -> str:
        t_low = text.lower()
        if any(k in t_low for k in ("kapasitas", "berapa informasi", "batasi", "chatnya ilang", "ga efektif")):
            return "Kapasitas Memori & Atomic Notes"
        if any(k in t_low for k in ("judul", "title", "sesuai dengan isi")):
            return "Akurasi Judul Sesi"
        if any(k in t_low for k in ("vault", "obsidian", "memory", "ingatan")):
            return "Navigasi Memori Vault"
        if any(k in t_low for k in ("folder", ".agent", "myself", "lokasi", "tempat")):
            return "Lokasi Skills & Direktori"
        if any(k in t_low for k in ("perintah", "kurang jelas", "bukan")):
            return "Kepatuhan Instruksi Pengguna"
        return "Pengalaman Operasional"

    @staticmethod
    def _distill_directive(text: str, category: str) -> str:
        t_low = text.lower()
        if any(k in t_low for k in ("kapasitas", "berapa informasi", "batasi", "chatnya ilang", "ga efektif")):
            return "Batasi isi setiap berkas catatan sesi maksimal 10 giliran user / ~250 baris. Pecah sesi panjang menjadi Part 01, Part 02 dengan tautan dua arah, dan hubungkan ke node konsep di 00_Meta/Concepts."
        if "judul" in t_low or "sesuai dengan isi" in t_low:
            return "Jangan gunakan prompt pertama mentah sebagai judul. Rangkum esensi tugas dan konteks substantif seluruh chat."
        if "folder" in t_low and ("myself" in t_low or ".agent" in t_low):
            return "Pusatkan seluruh skill, tool arsitektur, dan memory agent di D:/Dokumen/02_Kerja_Profesional/Myself/.agents, jangan membuat salinan terpecah."
        if "obsidian" in t_low or "vault" in t_low:
            return "Selalu prioritaskan membaca Vault Obsidian Lemonaru saat membahas riwayat lampau atau progres kerja."
        return "Pahami intensi substantif di balik pertanyaan pengguna sebelum merespons secara teknis kaku."

    @classmethod
    def record_global_learning(
        cls,
        learnings: List[Dict[str, str]],
        workspace_name: str,
        session_title: str,
        learning_log_path: Optional[Path] = None
    ) -> bool:
        if not learnings:
            return False

        target_path = learning_log_path or DEFAULT_LEARNING_LOG
        target_path.parent.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        date_today = datetime.now().strftime("%Y-%m-%d")

        entry_lines = [
            f"### 📅 {now_str} — [{workspace_name}] {session_title}",
            f"- **Konteks:** Interaksi pada workspace `{workspace_name}`"
        ]

        for idx, item in enumerate(learnings, 1):
            entry_lines.append(f"- **Pelajaran #{idx} ({item['category']}):**")
            entry_lines.append(f"  - 💬 *Koreksi Pengguna:* \"{item['user_quote']}\"")
            entry_lines.append(f"  - 🎯 *Aturan Evolved:* {item['directive']}")
        entry_lines.append("")

        entry_text = "\n".join(entry_lines) + "\n"

        if not target_path.exists():
            header = f"""---
tags:
  - type/ai-learning
  - source/antigravity
updated: {date_today}
---

# 🧠 AI Continuous Learning & Self-Improvement Log

Buku catatan akumulasi pelajaran penting, koreksi dari pengguna, dan evolusi aturan kerja agen Antigravity di Obsidian Vault Lemonaru.

---

"""
            target_path.write_text(header + entry_text, encoding="utf-8")
        else:
            content = target_path.read_text(encoding="utf-8")
            target_path.write_text(content + entry_text, encoding="utf-8")

        return True
