#!/usr/bin/env python3
"""
Complete Project-Based Restructuring & Naming Standardization for Obsidian Vault.
Strictly enforces:
1. Base on Project Isolation (Zero cross-project hairball entanglement).
2. Exact Naming Convention as Pelatihan Publik Speaking:
   'YYYY-MM-DD - HH.mm - Part NN - <Substantive Milestone Title>.md'
3. Sequential Episodic Chaining (prev_part / next_part).
4. Full Sub-MOC and Master MOC rebuilding.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

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

from core.config import DEFAULT_LOGS_DIR
from core.sanitizer import sanitize_filename
from core.indexer import MOCIndexer
from core.validator import parse_frontmatter


# Explicit curated milestone mappings for projects to ensure 100% professional titles
# keyed by (workspace, original_date, original_time)
CURATED_MILESTONES: Dict[str, Dict[str, str]] = {
    "TernakOS": {
        "2026-05-26_20:26": "Inisialisasi Proyek & Setup Arsitektur TernakOS",
        "2026-05-29_01:42": "Instalasi Generator QR Code & Konfigurasi Docker VPS",
        "2026-06-04_15:53": "Pembaruan Repositori GitHub & Sinkronisasi Build",
        "2026-06-05_03:52": "Perbaikan Navigasi Superadmin Panel & Pengaturan Profil",
        "2026-06-05_12:47": "Audit Nilai Null Email Profil Pengguna pada Skema Supabase",
        "2026-06-08_03:46": "Investigasi Latensi Database Spike Crash & Optimasi Frontend",
        "2026-06-14_23:22": "Sinkronisasi Kode Repositori & Persiapan Modul",
        "2026-08-04_01:00": "Pemisahan Modul Mandiri Dashboard Sembako Client",
        "2026-08-04_01:21": "Remediasi Bug 404 Endpoint plan_configs & Penyesuaian Mobile",
        "2026-08-04_04:24": "Audit & Optimasi Antarmuka Halaman Akun Sembako",
    },
    "07_Skripsi_&_TA": {
        "2026-06-07_15:56": "Audit Naskah Bab 4 & Analisis Heteroskedastisitas",
        "2026-06-22_03:48": "Ekstraksi Dokumen DOCX & Pembahasan Revisi Dosen Pembimbing",
        "2026-06-27_18:00": "Penyusunan Latar Belakang Dampak Wabah PMK Sapi Potong 2022",
        "2026-06-28_22:35": "Pembahasan Partisipasi Peternak dalam Kelompok Tani Ternak KTT",
        "2026-06-28_23:48": "Evaluasi Komprehensif Naskah PDF Skripsi & Catatan Revisi",
        "2026-07-02_19:02": "Penyesuaian Naskah Abstrak Bilingual Bahasa Indonesia & Inggris",
        "2026-07-07_21:41": "Analisis Tren Populasi Sapi Potong Kecamatan Nogosari 2021-2024",
        "2026-07-08_19:24": "Pembahasan Landasan Teori Sapi Potong & Analisis Gap",
        "2026-07-16_19:54": "Sinkronisasi Perubahan Naskah Skripsi ke GitHub",
        "2026-07-21_09:49": "Penyusunan Halaman Persembahan & Ucapan Terima Kasih",
        "2026-07-21_10:37": "Perumusan Ringkasan Saran bagi Peternak Rakyat & Instansi",
        "2026-07-28_18:47": "Finalisasi Draf Saran & Masukan Dosen Pembimbing",
        "2026-08-05_13:07": "Pengisian Permohonan Perpanjangan Masa Studi Prodi Peternakan",
        "2026-08-28_22:24": "Rekapitulasi Judul Skripsi, Script Analisis R & Validasi Responden",
    },
    "Company Profile": {
        "2026-08-14_13:57": "Perancangan Konsep & Arsitektur Website Svarna Vanilla",
        "2026-08-14_22:20": "Inisialisasi Git & Integrasi Repositori GitHub Svarna",
        "2026-08-15_17:20": "Audit Struktur Direktori & Analisis Basis Kode Svarna",
        "2026-08-15_19:05": "Pengembangan Komponen & Penyempurnaan Tampilan Web",
    },
    "Essence Indonesia": {
        "2026-08-17_00:26": "Konfigurasi Akun Web Disk & Panduan Deployment Server",
        "2026-08-17_01:39": "Investigasi Tampilan Index Of & Penataan Direktori CPanel",
        "2026-08-17_17:41": "Pengujian Local Development Server & Validasi Port",
        "2026-08-18_19:52": "Verifikasi Kepemilikan Domain DNS Google Search Console",
        "2026-08-24_15:19": "Optimasi Metadata Favicon & Pengindeksan Mesin Pencari",
        "2026-09-03_01:29": "Pemetaan Arsitektur & Analisis Strategis Proyek Essence",
        "2026-09-03_16:26": "Validasi Build Produksi & Sinkronisasi Git Push ke GitHub",
        "2026-09-04_03:45": "Audit Linting & Remediasi Permasalahan Kode Terkini",
    },
    "Anak Bawang": {
        "2026-06-14_22:03": "Perancangan Landing Page Minimalis Brand Bawang Goreng",
        "2026-07-11_01:44": "Eksplorasi Struktur Direktori & Persiapan Aset Brand",
    },
    "Dashboard Virgin": {
        "2026-08-22_01:19": "Audit Struktur Folder & Analisis Kode Dashboard Virgin",
        "2026-08-22_17:44": "Penataan Struktur File & Tata Kelola Modul Dashboard",
        "2026-08-22_20:18": "Normalisasi Skema & Pembersihan Format Data",
        "2026-08-22_20:20": "Evaluasi Komprehensif Arsitektur Dashboard Virgin",
    },
    "Google One Pro": {
        "2026-09-01_13:01": "Audit Alur Manajemen Email & Penataan Akun Pengguna",
        "2026-09-04_03:26": "Menjalankan Server Web & Validasi Antarmuka",
    },
    "Hero Farm File": {
        "2026-07-19_03:34": "Pemodelan Finansial & Analisis Siklus Penggemukan Ternak",
        "2026-07-19_23:31": "Pemetaan Struktur Draf & Perencanaan Bisnis Hero Farm",
    },
    "Hukum": {
        "2026-07-14_13:48": "Analisis Yuridis Surat Gugatan Penggugat & Kajian Dokumen Hukum",
    },
    "Kedokteran": {
        "2026-08-20_17:34": "Transformasi Materi & Penyusunan Tinjauan Pustaka Kedokteran",
    },
    "Didi": {
        "2026-06-04_23:05": "Asistensi Penulisan Profesional & Editing Editorial Naskah Didi",
    },
    "File": {
        "2026-07-26_01:03": "Pemrosesan & Validasi File Data CSV",
    },
    "GDG": {
        "2026-08-29_13:20": "Perancangan Arsitektur Web React GDG & Master Implementation Plan",
    },
    "Shutterstock": {
        "2026-07-21_19:09": "Perumusan Rencana Strategis & Kurasi Portofolio Shutterstock",
        "2026-07-21_23:42": "Analisis Spesifikasi Teknis & Ukuran Thumbnail Kontributor",
        "2026-07-24_13:59": "Validasi Berkas Gambar & Verifikasi Integritas File",
        "2026-07-26_03:34": "Pembersihan Berkas & Eliminasi Aset Tidak Terpakai",
        "2026-07-26_21:38": "Penyusunan Metadata Resmi Batch Gambar Parents Day",
        "2026-08-22_01:52": "Penyesuaian Resolusi & Format Unggah Aset Gambar",
        "2026-08-22_19:51": "Penyempurnaan Metadata & Optimasi Tagging Konten",
        "2026-08-27_16:53": "Sinkronisasi Aset & Finalisasi Koleksi Shutterstock",
    }
}


def extract_smart_title_for_session(content: str, ws_name: str, date_str: str, time_str: str, part_num: int) -> str:
    """Extracts a high-level engineering milestone title from note contents."""
    key = f"{date_str}_{time_str}"
    if ws_name in CURATED_MILESTONES and key in CURATED_MILESTONES[ws_name]:
        return CURATED_MILESTONES[ws_name][key]

    # Specific heuristic fallbacks for Juragan by Anak Bawang, Dasboard Gopek, Myself
    lower_c = content.lower()

    if ws_name == "Juragan by Anak Bawang":
        if "mutasi" in lower_c and "polymailer" in lower_c:
            return "Perbaikan Modal Riwayat Mutasi Bahan Baku Polymailer"
        if "stok" in lower_c and "label" in lower_c:
            return "Sinkronisasi Data Supplier & Penambahan Stok Label Depan"
        if "ai agent" in lower_c or "orchestrator" in lower_c:
            return "Perancangan Sistem Main AI Agent & Orchestrator Juragan"
        if "notulensi" in lower_c:
            return "Notulensi & Rekapitulasi Rapat Pengembangan POS Juragan"
        if "keyword categor" in lower_c or "product card" in lower_c:
            return "Konfigurasi Product Card & Keyword Categorization POS"
        if "auto syn" in lower_c or "auto sync" in lower_c:
            return "Implementasi Background Auto-Sync POS & Database"
        if "pesanan baru" in lower_c or "farhan" in lower_c:
            return "Pencatatan Pesanan Penjualan Baru & Verifikasi Transaksi"
        if "invoice" in lower_c and ("ongkir" in lower_c or "berat" in lower_c):
            return "Penyesuaian Komponen Ongkos Kirim pada Pembuatan Invoice"
        if "n8n" in lower_c or "email" in lower_c:
            return "Perancangan Blueprint Workflow Otomasi Email n8n"
        if "perhitungan" in lower_c and "selisih" in lower_c:
            return "Investigasi Selisih Perhitungan Rincian Transaksi POS"
        if "npm run dev" in lower_c:
            return "Menjalankan Local Development Server Vite Website v2"
        if "npm run build" in lower_c:
            return "Verifikasi Build Produksi & Pemeriksaan Linting Web"
        if "konten video" in lower_c or "multi-part" in lower_c:
            return "Perencanaan Konten Video & Seri Edukasi Bisnis Juragan"
        if "riset" in lower_c or "researh" in lower_c:
            return "Riset Arsitektur Fitur & Kebutuhan Pengguna Juragan"
        if "pelajari folder" in lower_c or "read all dokumen" in lower_c:
            return "Audit Menyeluruh Struktur Modul & Dokumen Juragan"
        return f"Pengembangan Modul Operasional Juragan Fitur {part_num:02d}"

    if ws_name == "Dasboard Gopek":
        if "reset database" in lower_c:
            return "Investigasi Notifikasi Reset Database & Integritas Data"
        if "invoice" in lower_c and ("download" in lower_c or "hp" in lower_c):
            return "Optimasi Tombol Unduh Faktur Invoice pada Mobile Android"
        if "wizard" in lower_c or "toko" in lower_c:
            return "Perbaikan Validasi Pemilihan Toko pada Wizard Transaksi"
        if "supabase_app_releases" in lower_c or "tenant_members" in lower_c:
            return "Skrip Migrasi SQL Rilis Aplikasi Supabase & Relasi Tenant"
        if "kirekplastik" in lower_c:
            return "Konfigurasi Email Owner Kirekplastik & Hak Akses Database"
        if "samsung" in lower_c or "crash" in lower_c:
            return "Investigasi Crash & Optimasi Performa Samsung Galaxy A07"
        if "maintenance" in lower_c or "kick" in lower_c:
            return "Implementasi Fitur Maintenance Mode & Pemutusan Sesi Login"
        if "lisensi" in lower_c:
            return "Troubleshooting Akses & Validasi Lisensi Server"
        if "pengeluaran" in lower_c:
            return "Pencatatan & Visualisasi Pengeluaran Finansial Bulanan"
        if "port" in lower_c or "27100" in lower_c:
            return "Monitoring & Penanganan Port Lokal Development Server"
        if "npm run build" in lower_c or "dev" in lower_c:
            return "Verifikasi Build Produksi & Server Development Vite"
        return f"Pengembangan Fitur Dashboard Gopek Analitik {part_num:02d}"

    if ws_name == "Myself":
        if "kkn" in lower_c or "ketua" in lower_c:
            return "Optimasi Resume & Integrasi Pengalaman Kepemimpinan KKN"
        if "profile.pdf" in lower_c or "profilepdf" in lower_c:
            return "Ekstraksi Profil Profesional & Analisis Kompetensi CV"
        if "gsp540" in lower_c or "conversational agent" in lower_c:
            return "Panduan Lab Cloud Conversational Agent & Generative AI"
        if "bluetooth" in lower_c:
            return "Troubleshooting Driver Hardware & Layanan Bluetooth Windows"
        if "google ai studio" in lower_c:
            return "Pengembangan Prototipe AI di Google AI Studio Challenge Lab"
        if "cloud storage" in lower_c:
            return "Otomasi Skrip Cloud Storage CLI SDK Challenge Lab"
        if "adk" in lower_c and "tools" in lower_c:
            return "Integrasi Tool Calling pada Agent Development Kit ADK"
        if "adk" in lower_c and "multi-agent" in lower_c:
            return "Perancangan Arsitektur Multi-Agent System dengan ADK"
        if "clear pod" in lower_c or "errno 98" in lower_c:
            return "Penanganan Port Conflict & Reset Credential Service"
        if "api gateway" in lower_c:
            return "Deploy & Konfigurasi Keamanan Serverless API Gateway"
        if "jarvis" in lower_c or "daddys home" in lower_c:
            return "Inisialisasi Environment Agent Jarvis & System Health Check"
        if "9router" in lower_c or "hermes" in lower_c:
            return "Menjalankan Layanan 9Router & Hermes Agent Gateway"
        if "vault" in lower_c and "memory" in lower_c:
            return "Arsitektur Persistent Memory System Vault Obsidian"
        if "vault" in lower_c:
            return "Integrasi Global Antigravity dengan Obsidian Vault Lemonaru"
        return f"Catatan Pengembangan Diri & Proyek Mandiri {part_num:02d}"

    # General fallback
    return f"Eksplorasi & Implementasi Teknis {ws_name} Bagian {part_num:02d}"


class ProjectVaultRestructurer:
    """
    Restructures workspaces strictly 'Base on Project':
    - Clean 'Part NN - <Milestone>' filenames.
    - Zero cross-project concepts.
    - Sequential episodic navigation.
    - Rebuilds Sub-MOC and Master MOC.
    """

    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR

    def restructure_workspace(self, ws_dir: Path):
        ws_name = ws_dir.name
        print(f"\n📁 Menata Workspace: {ws_name}")

        # Skip Pelatihan Publik Speaking (Gold Standard reference)
        if ws_name == "Pelatihan Publik Speaking":
            print(f"  ⏩ Dilewati (Sudah sesuai standar gold reference).")
            return

        all_notes = sorted([f for f in ws_dir.glob("*.md") if not f.name.startswith("Index - ")])
        if not all_notes:
            return

        # 1. Parse dates and sort chronologically
        parsed_notes = []
        for p in all_notes:
            content = p.read_text(encoding="utf-8", errors="ignore")
            fm, _ = parse_frontmatter(content)

            # Match date and time pattern
            m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*-\s*(\d{2}[.:]\d{2})", p.name)
            if m:
                d_str = m.group(1)
                t_str = m.group(2).replace(".", ":")
            else:
                d_str = str(fm.get("date", "2026-01-01"))
                t_str = str(fm.get("time", "00:00"))

            parsed_notes.append({
                "path": p,
                "content": content,
                "fm": fm,
                "date": d_str,
                "time": t_str
            })

        parsed_notes.sort(key=lambda x: (x["date"], x["time"], x["path"].name))
        total_parts = len(parsed_notes)

        # 2. Assign milestone titles & Part numbers
        for idx, item in enumerate(parsed_notes, 1):
            milestone = extract_smart_title_for_session(
                item["content"], ws_name, item["date"], item["time"], idx
            )
            time_dot = item["time"].replace(":", ".")
            clean_milestone = sanitize_filename(milestone, max_length=65)
            
            item["part"] = idx
            item["milestone"] = clean_milestone
            item["final_stem"] = f"{item['date']} - {time_dot} - Part {idx:02d} - {clean_milestone}"
            item["final_filename"] = f"{item['final_stem']}.md"
            item["target_path"] = ws_dir / item["final_filename"]

        # 3. Rewrite notes with project isolation & episodic chaining
        for idx, item in enumerate(parsed_notes):
            part_num = item["part"]
            content = item["content"]
            fm = item["fm"]
            target_path = item["target_path"]
            old_path = item["path"]

            # Episodic links
            prev_link = f"[[{parsed_notes[idx-1]['final_stem']}]]" if idx > 0 else "null"
            next_link = f"[[{parsed_notes[idx+1]['final_stem']}]]" if idx < total_parts - 1 else "null"

            p_display = f"[[{parsed_notes[idx-1]['final_stem']}|⬅️ Part {idx:02d}]]" if idx > 0 else "*(Awal Sesi)*"
            n_display = f"[[{parsed_notes[idx+1]['final_stem']}|Part {idx+2:02d} ➔]]" if idx < total_parts - 1 else "*(Akhir Sesi / Aktif)*"
            nav_banner = f"> [!info] 🧭 **Navigasi Sesi Episodik: Bagian {part_num} dari {total_parts}**\n> ⏮️ **Sebelumnya:** {p_display} | ⏭️ **Selanjutnya:** {n_display}\n\n"

            # Clean body: strip previous banners and cross-project concept clusters
            if content.startswith("---"):
                parts = content.split("---", 2)
                body = parts[2] if len(parts) > 2 else ""
            else:
                body = content

            body = re.sub(r"> \[!info\] 🧭 \*\*Navigasi Sesi Episodik[^\n]*\n(?:> [^\n]*\n)*\n?", "", body)
            body = re.sub(r"##\s*🧠\s*Node Konsep Terkait[^\n]*\n(?:\[\[.*?\]\][^\n]*\n)*", "", body)
            body = re.sub(r"^#\s*[^\r\n]+", f"# 🤖 Sesi Part {part_num:02d}: {item['milestone']}", body.lstrip(), count=1)
            body = re.sub(r"\n{3,}", "\n\n", body)

            # Insert nav banner after H1
            h1_match = re.search(r"^(# [^\r\n]+)", body, re.MULTILINE)
            if h1_match:
                h1_full = h1_match.group(1)
                body = body.replace(h1_full, f"{h1_full}\n\n{nav_banner}", 1)
            else:
                body = nav_banner + body

            # Frontmatter strictly Base on Project:
            # concepts: [] (No cross-project concepts to avoid hairball entanglement!)
            conv_id = fm.get("conversation_id", f"conv-{item['date']}-{item['time'].replace(':', '.')}")
            new_frontmatter = f"""---
tags:
  - type/ai-log
  - source/antigravity
  - workspace/{ws_name.lower().replace(' ', '-')}
date: {item['date']}
time: "{item['time']}"
status: archived
workspace: "{ws_name}"
conversation_id: "{conv_id}"
part: {part_num}
total_parts: {total_parts}
prev_part: {f'"{prev_link}"' if prev_link != 'null' else 'null'}
next_part: {f'"{next_link}"' if next_link != 'null' else 'null'}
up: "[[Index - {ws_name}]]"
sub_hub: "[[Index - {ws_name}]]"
concepts: []
---
"""
            new_content = new_frontmatter + body.lstrip()

            # Rename or update file
            if old_path != target_path:
                if old_path.exists():
                    old_path.unlink()
                target_path.write_text(new_content, encoding="utf-8")
            else:
                target_path.write_text(new_content, encoding="utf-8")

        print(f"  ✅ {total_parts} catatan berhasil distandarisasi ke format 'Part NN - <Milestone>'.")

    def run(self):
        print("=" * 60)
        print("🚀 RESTRUKTURISASI KETAT: BASE ON PROJECT OBSIDIAN VAULT")
        print("=" * 60)

        for ws in sorted(self.logs_dir.iterdir()):
            if ws.is_dir():
                self.restructure_workspace(ws)

        # Rebuild all MOCs cleanly
        print("\n🔄 Membangun ulang seluruh Sub-MOC dan Master MOC...")
        MOCIndexer.build_all_indexes(self.logs_dir)
        print("✅ Seluruh MOC berhasil diperbarui dengan tautan Part NN yang valid!")


if __name__ == "__main__":
    restructurer = ProjectVaultRestructurer()
    restructurer.run()
