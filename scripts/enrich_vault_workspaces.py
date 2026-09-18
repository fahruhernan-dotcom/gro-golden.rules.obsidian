#!/usr/bin/env python3
"""
Enrich and Restructure Existing Obsidian Vault Workspaces.
Transforms flat/raw notes into interconnected semantic graph clusters
following the standard established by 'Pelatihan Publik Speaking'.

Features:
- Deduplication of truncated/collision duplicate files.
- Title normalization (replaces raw prompts like 'yo chat', 'githpush', path dumps with semantic titles).
- Domain Concept Tagging (connects notes to 00_Meta/Concepts/ nodes).
- Episodic chaining (connects chronological sessions via prev_part/next_part).
- Rebuilding 2-tier MOCs (Workspace Sub-MOC & Master MOC).
- Safe dry-run mode.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure skill directory in sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT
from core.archive_engine import CONCEPT_RULES
from core.sanitizer import sanitize_filename, make_session_filename
from core.indexer import MOCIndexer
from core.validator import parse_frontmatter


RAW_PROMPT_PATTERNS = [
    r"^yo\b",
    r"^halo+\b",
    r"^gith?push\b",
    r"^push github\b",
    r"^test\b",
    r"^cek\b",
    r"^sudah ditambahkan\b",
    r"^ini kan emang\b",
    r"^bantu\b",
    r"^coba\b",
    r"^tolong\b",
    r"^oke\b",
    r"^ok\b",
    r"^d\s+dokumen\b",
    r"^diskusi antigravity\b",
    r"^read all dokumen\b",
    r"^pelajari folder\b",
    r"^researh terlebih\b",
    r"^mau notulensi\b",
    r"^if enabled\b",
    r"^auto syn\b",
]

# Workspace specific fallback concept seeds
WORKSPACE_DEFAULT_CONCEPTS: Dict[str, List[str]] = {
    "TernakOS": ["TernakOS Core Architecture"],
    "Juragan by Anak Bawang": ["Juragan POS & Billing Engine"],
    "Dasboard Gopek": ["Gopek Financial Analytics"],
    "Dashboard Virgin": ["Gopek Financial Analytics"],
    "07_Skripsi_&_TA": ["Skripsi & Academic Research"],
    "Pelatihan Publik Speaking": ["Event Operations & Blueprint"],
    "Company Profile": ["Frontend UX & Responsive Design"],
    "Myself": ["Obsidian Vault Memory & Capacity Rules"],
}


def is_raw_prompt_title(title: str) -> bool:
    """Detects if a title is a raw prompt, conversational greeting, or path fragment."""
    clean = title.strip().lower()
    if len(clean) < 8 or "02_kerja_profesional" in clean or clean.startswith("d:"):
        return True
    for pat in RAW_PROMPT_PATTERNS:
        if re.search(pat, clean):
            return True
    return False


def infer_semantic_title(content: str, current_title: str, workspace: str) -> str:
    """Infers a clean, substantive title from the note content."""
    if not is_raw_prompt_title(current_title) and len(current_title) > 12 and not current_title.endswith("."):
        return current_title

    # 1. Look for User Request or Main Result in summary
    req_match = re.search(r"-\s*(?:Masalah\s*/\s*Request|Permintaan Pengguna):\s*([^\r\n]+)", content, re.IGNORECASE)
    sol_match = re.search(r"-\s*(?:Solusi\s*/\s*Output Utama|Hasil Utama):\s*([^\r\n]+)", content, re.IGNORECASE)

    req_text = req_match.group(1).strip() if req_match else ""
    sol_text = sol_match.group(1).strip() if sol_match else ""

    # Check content corpus
    lower_c = (current_title + " " + req_text + " " + sol_text + " " + content[:3000]).lower()

    # Domain specific intent recognition with specific rules first
    if "qr" in current_title.lower() or ("qr" in req_text.lower()):
        return "Instalasi Generator QR & Konfigurasi VPS"
    if "plan_configs" in lower_c or "requests.js" in lower_c:
        return "Fix Error 404 plan_configs Supabase & Mobile View"
    if "halaman akun" in lower_c:
        return "Audit & Optimasi Antarmuka Halaman Akun Sembako"
    if "sembako" in lower_c and ("copy" in lower_c or "client" in lower_c or "dasboard" in lower_c):
        return "Setup Proyek Dasboard Sembako Client & Pemisahan Modul"
    if "superadmin" in lower_c and "navigasi" in lower_c:
        return "Fix Navigasi Superadmin Panel & Pengaturan Profil"
    if "db spike" in lower_c or "crash" in lower_c:
        return "Frontend Audit — Analisis DB Spike & Penanganan Crash"
    if "profile email null" in lower_c or "email null" in lower_c:
        return "Audit & Perbaikan Nilai Null Email Profil Pengguna"
    if "notulensi" in lower_c or "bulan baru agustus" in lower_c:
        return f"Notulensi & Rekapitulasi Rapat Pengembangan {workspace}"
    if "keyword categor" in lower_c or "product card" in lower_c:
        return "Konfigurasi Product Card & Keyword Categorization POS"
    if "auto syn" in lower_c or "auto sync" in lower_c:
        return "Implementasi Background Auto-Sync POS & Database"
    if "researh" in lower_c or "riset" in lower_c:
        return f"Riset & Penentuan Arsitektur Fitur {workspace}"
    if "pelajari folder" in lower_c or "read all dokumen" in lower_c:
        return f"Audit & Pemetaan Menyeluruh Modul {workspace}"
    if "yo chat" in lower_c or "haloo" in lower_c or "halo" in lower_c:
        return f"Inisialisasi Workspace & Arsitektur {workspace}"
    if "githpush" in lower_c or "push github" in lower_c:
        return f"Sinkronisasi Kode & Pembaruan Repositori GitHub"
    if "skripsi" in lower_c or "tugas akhir" in lower_c:
        return "Penyusunan Metodologi & Analisis Riset Skripsi"

    # Fallback to cleaned request or current title
    if req_text and len(req_text) > 8 and not is_raw_prompt_title(req_text):
        cleaned = re.sub(r"[^\w\s-]", "", req_text).strip()
        words = cleaned.split()[:6]
        return " ".join(words).title()

    if sol_text and len(sol_text) > 10:
        cleaned = re.sub(r"[^\w\s-]", "", sol_text).strip()
        words = cleaned.split()[:6]
        return " ".join(words).title()

    return current_title


def detect_note_concepts(content: str, workspace: str) -> List[str]:
    """Matches content against CONCEPT_RULES and injects domain defaults."""
    lower_content = content.lower()
    matched = []

    for concept, keywords in CONCEPT_RULES.items():
        if any(k in lower_content for k in keywords):
            matched.append(concept)

    # Add workspace-specific seeds if matched list is sparse (< 2)
    default_seeds = WORKSPACE_DEFAULT_CONCEPTS.get(workspace, [])
    for seed in default_seeds:
        if seed not in matched:
            matched.append(seed)

    # General infrastructure / database inferences
    if ("supabase" in lower_content or "postgres" in lower_content) and "Database & Supabase Architecture" not in matched:
        matched.append("Database & Supabase Architecture")
    if ("vps" in lower_content or "docker" in lower_content or "nginx" in lower_content or "github" in lower_content) and "DevOps & Cloud Infrastructure" not in matched:
        matched.append("DevOps & Cloud Infrastructure")
    if ("ui" in lower_content or "frontend" in lower_content or "tailwind" in lower_content) and "Frontend UX & Responsive Design" not in matched:
        matched.append("Frontend UX & Responsive Design")

    return sorted(list(set(matched)))[:4]


class VaultWorkspaceEnricher:
    """
    Enriches and restructures notes inside Antigravity Logs to create
    semantic clusters and chronological graph topology.
    """

    def __init__(self, logs_dir: Optional[Path] = None, dry_run: bool = False):
        self.logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
        self.dry_run = dry_run

    def process_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """Processes all notes in a specific workspace."""
        ws_dir = self.logs_dir / workspace_name
        if not ws_dir.is_dir():
            return {"workspace": workspace_name, "status": "NOT_FOUND"}

        print(f"\n==================================================")
        print(f"📁 Memproses Workspace: {workspace_name}")
        print(f"==================================================")

        all_notes = sorted([f for f in ws_dir.glob("*.md") if not f.name.startswith("Index - ")])
        print(f"Total catatan awal: {len(all_notes)}")

        # Step 1: Detect and remove truncated duplicates
        kept_notes = []
        deleted_count = 0
        skip_files = set()

        for i, f1 in enumerate(all_notes):
            if f1 in skip_files:
                continue
            is_truncated_duplicate = False
            for j, f2 in enumerate(all_notes):
                if i == j or f2 in skip_files:
                    continue
                # Check prefix match where f1 is a shorter prefix of f2
                base1 = f1.stem
                base2 = f2.stem
                if (base2.startswith(base1[:len(base1)-3]) or base1.startswith(base2[:len(base2)-3])):
                    # Compare file lengths
                    if len(base1) < len(base2) and f1.stat().st_size <= f2.stat().st_size + 50:
                        print(f"  🗑️ Duplikat terpotong terdeteksi:")
                        print(f"     Hapus: {f1.name}")
                        print(f"     Simpan: {f2.name}")
                        is_truncated_duplicate = True
                        skip_files.add(f1)
                        if not self.dry_run:
                            f1.unlink()
                        deleted_count += 1
                        break
            if not is_truncated_duplicate:
                kept_notes.append(f1)

        print(f"Catatan setelah deduplikasi: {len(kept_notes)} (Dihapus: {deleted_count})")

        # Step 2: Parse and Enrich notes
        processed_records: List[Dict[str, Any]] = []
        title_counts: Dict[str, int] = {}

        for note_path in kept_notes:
            content = note_path.read_text(encoding="utf-8", errors="ignore")
            fm, is_valid = parse_frontmatter(content)

            # Parse filename components (YYYY-MM-DD - HH.mm - Title.md)
            name_match = re.match(r"^(\d{4}-\d{2}-\d{2})\s*-\s*(\d{2}[.:]\d{2})\s*-\s*(.+?)(?:\.md)$", note_path.name)
            if name_match:
                date_str = name_match.group(1)
                time_str = name_match.group(2).replace(".", ":")
                old_title = name_match.group(3).strip()
            else:
                date_str = fm.get("date", "2026-01-01")
                time_str = str(fm.get("time", "00:00"))
                old_title = note_path.stem

            raw_new_title = infer_semantic_title(content, old_title, workspace_name)
            clean_new_title = sanitize_filename(raw_new_title, max_length=65)

            concepts = detect_note_concepts(content, workspace_name)

            processed_records.append({
                "path": note_path,
                "content": content,
                "fm": fm,
                "date": date_str,
                "time": time_str,
                "old_title": old_title,
                "raw_new_title": clean_new_title,
                "concepts": concepts
            })

        # Step 3: Sort chronologically
        processed_records.sort(key=lambda r: (r["date"], r["time"], r["raw_new_title"]))

        # Assign unique filename with collision handling
        used_filenames = set()
        for rec in processed_records:
            date_str = rec["date"]
            time_formatted = rec["time"].replace(":", ".")
            base_name = f"{date_str} - {time_formatted} - {rec['raw_new_title']}"
            target_name = f"{base_name}.md"

            collision_idx = 2
            while target_name in used_filenames:
                target_name = f"{base_name} [{collision_idx}].md"
                collision_idx += 1

            used_filenames.add(target_name)
            rec["final_filename"] = target_name
            rec["final_title"] = target_name[:-3]

        # Step 4: Write enriched content with episodic chaining
        total_records = len(processed_records)
        renamed_count = 0
        updated_count = 0

        for idx, rec in enumerate(processed_records):
            content = rec["content"]
            fm = rec["fm"]
            date_str = rec["date"]
            final_filename = rec["final_filename"]
            new_path = ws_dir / final_filename

            # Episodic links
            prev_link = f"[[{processed_records[idx-1]['final_title']}]]" if idx > 0 else "null"
            next_link = f"[[{processed_records[idx+1]['final_title']}]]" if idx < total_records - 1 else "null"

            # Concepts YAML
            concepts_lines = "\n".join([f'  - "[[{c}]]"' for c in rec["concepts"]])
            concepts_yaml = f"concepts:\n{concepts_lines}" if rec["concepts"] else "concepts: []"

            # Extract body
            if content.startswith("---"):
                parts = content.split("---", 2)
                body = parts[2] if len(parts) > 2 else ""
            else:
                body = content

            # Clean body from duplicate concept sections or old episodic navigation
            body = re.sub(r"> \[!info\] 🧭 \*\*Navigasi Sesi Episodik[^\n]*\n(?:> [^\n]*\n)*\n?", "", body)
            body = re.sub(r"##\s*🧠\s*Node Konsep Terkait[^\n]*\n(?:\[\[.*?\]\][^\n]*\n)*", "", body)

            # Insert episodic navigation banner
            p_display = f"[[{processed_records[idx-1]['final_title']}|⬅️ Sebelumnya]]" if idx > 0 else "*(Awal Sesi)*"
            n_display = f"[[{processed_records[idx+1]['final_title']}|Selanjutnya ➔]]" if idx < total_records - 1 else "*(Akhir Sesi / Aktif)*"
            nav_banner = f"> [!info] 🧭 **Navigasi Sesi Episodik ({idx+1}/{total_records})**\n> ⏮️ **Sebelumnya:** {p_display} | ⏭️ **Selanjutnya:** {n_display}\n\n"

            # Insert concept cluster section
            concept_cluster_links = " • ".join([f"[[{c}]]" for c in rec["concepts"]])
            concept_cluster_section = f"\n## 🧠 Node Konsep Terkait (Graph Clusters)\n{concept_cluster_links}\n"

            # Place concept cluster section right before metadata / catatan tambahan / file
            if re.search(r"##\s*[^#\n]*(?:Metadata|Catatan|File|Perubahan)", body, re.IGNORECASE):
                body = re.sub(
                    r"(##\s*[^#\n]*(?:Metadata|Catatan|File|Perubahan)[^\n]*)",
                    f"{concept_cluster_section}\n\\1",
                    body,
                    count=1,
                    flags=re.IGNORECASE
                )
            elif "> [!example]-" in body:
                body = body.replace("> [!example]-", f"{concept_cluster_section}\n> [!example]-")
            else:
                body = body + f"\n{concept_cluster_section}\n"

            # Update H1 Title to match semantic title
            body = re.sub(r"^#\s*[^\r\n]+", f"# 🤖 Sesi Antigravity: {rec['raw_new_title']}", body.lstrip(), count=1)
            # Clean excess blank lines
            body = re.sub(r"\n{3,}", "\n\n", body)

            # Place nav banner right after the main H1 title
            h1_match = re.search(r"^(# [^\r\n]+)", body, re.MULTILINE)
            if h1_match:
                h1_full = h1_match.group(1)
                body = body.replace(h1_full, f"{h1_full}\n\n{nav_banner}", 1)
            else:
                body = nav_banner + body

            # Reconstruct frontmatter
            conv_id = fm.get("conversation_id", f"conv-{date_str}-{rec['time'].replace(':', '.')}")
            new_frontmatter = f"""---
tags:
  - type/ai-log
  - source/antigravity
  - workspace/{workspace_name.lower().replace(' ', '-')}
date: {date_str}
time: "{rec['time']}"
status: archived
workspace: "{workspace_name}"
conversation_id: "{conv_id}"
part: {idx + 1}
total_parts: {total_records}
prev_part: {f'"{prev_link}"' if prev_link != 'null' else 'null'}
next_part: {f'"{next_link}"' if next_link != 'null' else 'null'}
up: "[[Index - {workspace_name}]]"
sub_hub: "[[Index - {workspace_name}]]"
{concepts_yaml}
---
"""
            new_content = new_frontmatter + body.lstrip()

            if not self.dry_run:
                # If path changed
                if rec["path"] != new_path:
                    if rec["path"].exists():
                        rec["path"].unlink()
                    new_path.write_text(new_content, encoding="utf-8")
                    renamed_count += 1
                else:
                    rec["path"].write_text(new_content, encoding="utf-8")
                    updated_count += 1
            else:
                if rec["path"].name != final_filename:
                    print(f"  [Dry-Run] Rename: '{rec['path'].name}' ➔ '{final_filename}'")
                print(f"  [Dry-Run] Konsep: {rec['concepts']}")

        print(f"Selesai memproses {workspace_name}: {updated_count} diperbarui, {renamed_count} di-rename.")

        # Step 5: Rebuild Indexes
        if not self.dry_run:
            MOCIndexer.build_all_indexes(self.logs_dir)
            print(f"✅ Seluruh indeks MOC (Sub-MOC & Master) berhasil diregenerasi.")

        return {
            "workspace": workspace_name,
            "total": total_records,
            "updated": updated_count,
            "renamed": renamed_count,
            "deleted_duplicates": deleted_count
        }

    def process_all_workspaces(self) -> Dict[str, Any]:
        """Runs enrichment across all workspaces."""
        results = {}
        for item in sorted(self.logs_dir.iterdir()):
            if item.is_dir() and item.name != "Pelatihan Publik Speaking":
                res = self.process_workspace(item.name)
                results[item.name] = res

        if not self.dry_run:
            MOCIndexer.build_all_indexes(self.logs_dir)
            print("\n✅ Seluruh MOC dan Master Index - Antigravity Logs.md berhasil diregenerasi.")

        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Enrich and restructure Obsidian Vault workspaces into semantic graph clusters.")
    parser.add_argument("--workspace", type=str, default=None, help="Target specific workspace (e.g. TernakOS).")
    parser.add_argument("--dry-run", action="store_true", help="Preview modifications without touching files.")
    args = parser.parse_args()

    enricher = VaultWorkspaceEnricher(dry_run=args.dry_run)
    if args.workspace:
        enricher.process_workspace(args.workspace)
    else:
        enricher.process_all_workspaces()


if __name__ == "__main__":
    main()
