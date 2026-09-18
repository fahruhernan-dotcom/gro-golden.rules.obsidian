"""
Obsidian MOC (Map of Content) Builder.
Implements 2-Tier Hub-and-Spoke architecture:
Main MOC links exclusively to Workspace MOCs.
Workspace MOCs link to individual session notes.
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

try:
    from .config import DEFAULT_LOGS_DIR, REQUIRED_HUB_TAGS, REQUIRED_SUBHUB_TAGS
except ImportError:
    DEFAULT_LOGS_DIR = Path(r"D:\Dokumen\02_Kerja_Profesional\Myself\Vault\Lemonaru\00_Meta\Antigravity Logs")
    REQUIRED_HUB_TAGS = ["type/master-hub", "type/moc", "source/antigravity"]
    REQUIRED_SUBHUB_TAGS = ["type/sub-hub", "type/moc", "source/antigravity"]


class MOCIndexer:
    """
    Generates and updates 2-tier Hub-and-Spoke indexes across the Obsidian vault.
    """

    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR

    def build_all(self) -> Dict[str, Any]:
        return self.build_all_indexes(self.logs_dir)

    @staticmethod
    def _extract_deliverable(note_file: Path) -> str:
        """Extracts a short one-line executive summary / deliverable from a session note."""
        try:
            content = note_file.read_text(encoding="utf-8", errors="replace")
            # 1. Match Hasil Utama or Solusi / Output Utama
            m_res = re.search(r"(?:-\s*\*\*Hasil Utama:\*\*|-\s*Solusi\s*/\s*Output\s*Utama:)\s*(.+)", content)
            if m_res:
                raw_text = m_res.group(1).strip()
                cleaned = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw_text)
                cleaned = cleaned.replace("*", "").replace("`", "").replace("|", "-").strip()
                if len(cleaned) > 75:
                    cleaned = cleaned[:72] + "..."
                return cleaned if cleaned else "-"

            # 2. Match Permintaan Pengguna or Masalah / Request
            m_req = re.search(r"(?:-\s*\*\*Permintaan Pengguna:\*\*|-\s*Masalah\s*/\s*Request:)\s*(.+)", content)
            if m_req:
                raw_text = m_req.group(1).strip()
                cleaned = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw_text)
                cleaned = cleaned.replace("*", "").replace("`", "").replace("|", "-").strip()
                if len(cleaned) > 75:
                    cleaned = cleaned[:72] + "..."
                return cleaned if cleaned else "-"
        except Exception:
            pass
        return "-"

    @classmethod
    def build_all_indexes(cls, logs_dir: Optional[Path] = None) -> Dict[str, Any]:
        base_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
        main_moc_file = base_dir / "Index - Antigravity Logs.md"

        if not base_dir.exists():
            return {"error": f"Directory {base_dir} does not exist.", "sub_mocs": []}

        workspace_records: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        sub_mocs: List[str] = []
        total_sessions = 0

        # Scan all workspace subdirectories
        for ws_dir in sorted(base_dir.iterdir()):
            if not ws_dir.is_dir() or ws_dir.name.startswith("."):
                continue

            ws_name = ws_dir.name
            for note_file in sorted(ws_dir.glob("*.md")):
                if note_file.name.startswith("Index - "):
                    continue

                total_sessions += 1
                dt_str = ""
                topic_str = note_file.stem

                # Parse filename pattern: YYYY-MM-DD - HH.mm - Topic
                m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*-\s*(\d{2}\.\d{2})\s*-\s*(.+)$", note_file.stem)
                if m:
                    date_part, time_part, topic_part = m.groups()
                    dt_str = f"{date_part} {time_part.replace('.', ':')}"
                    topic_str = topic_part
                else:
                    try:
                        mtime = note_file.stat().st_mtime
                        dt_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        dt_str = "Unknown Date"

                deliverable = cls._extract_deliverable(note_file)
                workspace_records[ws_name].append({
                    "file_path": note_file,
                    "stem": note_file.stem,
                    "datetime": dt_str,
                    "topic": topic_str,
                    "deliverable": deliverable
                })

        # 1. Build Sub-MOC for each workspace
        for ws_name, notes in workspace_records.items():
            ws_dir = base_dir / ws_name
            sub_moc_file = ws_dir / f"Index - {ws_name}.md"

            # Sort notes by date descending
            notes.sort(key=lambda x: x["datetime"], reverse=True)

            table_rows = []
            for n in notes:
                clean_topic = n["topic"].replace("|", "-")
                clean_deliverable = n.get("deliverable", "-").replace("|", "-")
                table_rows.append(f"| `{n['datetime']}` | [[{n['stem']}]] | {clean_topic} | {clean_deliverable} |")

            table_content = "\n".join(table_rows) if table_rows else "| - | *(Belum ada sesi tercatat)* | - | - |"

            sub_moc_content = f"""---
tags:
  - type/sub-hub
  - type/moc
  - source/antigravity
workspace: "{ws_name}"
up: "[[Index - Antigravity Logs]]"
total_sessions: {len(notes)}
---

# 📁 Hub: {ws_name}

> [!info] 🧭 Navigasi Hirarki
> - **Induk Sentral:** [[Index - Antigravity Logs]]
> - **Total Sesi:** `{len(notes)}` percakapan
> - **Workspace:** `{ws_name}`

---

## 📋 Daftar Riwayat Percakapan Antigravity

| Tanggal & Waktu | Catatan Sesi | Topik | Ringkasan / Hasil Utama |
| :--- | :--- | :--- | :--- |
{table_content}

---
- 🔗 Kembali ke: [[Index - Antigravity Logs]]
"""
            sub_moc_file.write_text(sub_moc_content, encoding="utf-8")
            sub_mocs.append(str(sub_moc_file))

        # 2. Build Master MOC (Main Hub)
        ws_table_rows = []
        for idx, (ws_name, notes) in enumerate(sorted(workspace_records.items()), 1):
            ws_table_rows.append(
                f"| {idx} | **{ws_name}** | [[Index - {ws_name}]] | `{len(notes)}` sesi |"
            )

        ws_table_content = "\n".join(ws_table_rows) if ws_table_rows else "| - | *Belum ada riwayat sesi* | - | 0 sesi |"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        master_moc_content = f"""---
tags:
  - type/master-hub
  - type/moc
  - source/antigravity
date: {datetime.now().strftime('%Y-%m-%d')}
status: active
---

# 🌐 Hub Indeks Utama: Antigravity Session Logs

Selamat datang di titik sentral dokumentasi seluruh riwayat interaksi dan pengerjaan tugas bersama **Antigravity**.

> [!tip] 🧭 Arsitektur Graph View (Hub-and-Spoke / MOC)
> Indeks ini dirancang menggunakan sistem **hirarki bertingkat**:
> 1. **Master Hub (Node Utama):** `Index - Antigravity Logs` *(file ini)*
> 2. **Sub-Hubs (Cluster Proyek):** Masing-masing terhubung ke sub-indeks proyek di bawah.
> 3. **Leaf Notes (Catatan Sesi):** Hanya terhubung ke sub-indeks proyeknya masing-masing.
> 
> *Struktur ini mencegah penumpukan 'bola rambut' di Obsidian Graph View dan membentuk kluster percabangan yang rapi.*

---

### 📊 Statistik Keseluruhan
- **Total Sesi Percakapan:** `{total_sessions}` sesi
- **Total Workspace / Proyek:** `{len(workspace_records)}` workspace
- **Terakhir Diperbarui:** `{now_str}`

---

## 🗂️ Direktori Sub-Indeks Workspace

| No | Workspace / Proyek | Sub-Indeks Hub | Jumlah Sesi |
| :-: | :--- | :--- | :-: |
{ws_table_content}

---

## 📌 Pedoman Sistem Log
Setiap sesi baru secara otomatis terdaftar ke dalam sub-indeks workspace masing-masing:
- **Lokasi File Log:** `00_Meta/Antigravity Logs/[Workspace]/`
- **Sub-Indeks Proyek:** `Index - [Workspace]`
- **Master Index:** `Index - Antigravity Logs`
"""
        main_moc_file.write_text(master_moc_content, encoding="utf-8")

        return {
            "master_moc": str(main_moc_file),
            "main_moc": str(main_moc_file),
            "workspaces_updated": len(workspace_records),
            "sub_mocs": sub_mocs,
            "total_sessions": total_sessions
        }


build_all_indexes = MOCIndexer.build_all_indexes
