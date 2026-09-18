---
name: golden-rules-obsidian
description: Production-grade persistent working memory and 2-tier hub-and-spoke knowledge architecture for AI coding agents. Automates proactive turn-8 session archiving, MOC index regeneration, health auditing, and 5-advisor architecture council deliberations.
tags:
  - ai-memory
  - obsidian
  - knowledge-graph
  - llm-council
  - architecture
  - context-management
---

# 🧠 Golden Rules Obsidian Agent Skill

Gunakan skill ini ketika agen AI perlu:
1. Membaca konteks atau keputusan arsitektur lampau dari Obsidian Vault.
2. Mengarsipkan sesi percakapan aktif ke dalam Obsidian Vault secara otomatis dan terstruktur.
3. Mencegah amnesia akibat proses *context compaction* dengan melakukan checkpoint proaktif pada turn 8–10.
4. Membangun kembali indeks 2-tier Hub-and-Spoke (Master Hub & Workspace Sub-Indices).
5. Mengaudit kesehatan frontmatter, broken links, dan integritas vault.
6. Menjalankan telaah dialektika 5 persona ahli (LLM Council) terhadap keputusan arsitektur atau refactoring besar.

---

## 🏛️ The 7 Golden Rules (Wajib Dipatuhi)

1. **Atomic Notes:** 1 berkas `.md` untuk 1 topik atau milestone tunggal. Maksimal 250–300 baris Markdown (~15–20 KB) atau 8–10 giliran interaksi.
2. **Proactive Turn-8 Checkpoints:** Jika percakapan panjang, pecah sesi secara berkala menjadi `Part 01`, `Part 02` dengan wikilinks dua arah (`prev_part` dan `next_part`) sebelum context window terkompresi.
3. **2-Tier Hub-and-Spoke MOC:** Catatan sesi hanya menautkan ke Sub-Indeks Workspace (`up: "[[Index - Workspace]]"`), bukan langsung ke Master Hub.
4. **Star Graph Clusters:** Tautkan konsep dan entitas arsitektur (`[[Database Architecture]]`, `[[DevOps VPS Ubuntu]]`) agar Graph View Obsidian membentuk klaster bintang yang rapi.
5. **Semantic Title Hygiene:** Dilarang keras menamai file dengan prompt mentah pengguna (misal: *"cek vault"*). Gunakan ringkasan substantif masalah dan solusi teknis.
6. **Zero-Leakage Client Quarantine:** Jangan pernah mencatat data finansial, token rahasia, atau kredensial proyek klien ke dalam dokumentasi holding/global.
7. **LLM Council Gatekeeping:** Gunakan sidang 5 penasihat (`gro council "<dilemma>"`) untuk mengevaluasi trade-off arsitektur kritis sebelum memodifikasi basis kode inti.

---

## 🛠️ CLI Quick Reference (`gro`)

Perintah CLI terpadu `golden-rules-obsidian` / `gro`:

```bash
# 1. Arsipkan sesi aktif saat ini
python golden-rules-obsidian/scripts/cli.py archive --topic "Judul Substantif Sesi"

# 2. Cari keputusan arsitektur lampau
python golden-rules-obsidian/scripts/cli.py search "Kata Kunci Query" --limit 5

# 3. Bangun ulang Master Hub dan Sub-MOC
python golden-rules-obsidian/scripts/cli.py index

# 4. Audit integritas dan kesehatan berkas Vault
python golden-rules-obsidian/scripts/cli.py validate

# 5. Jalankan review dewan arsitektur 5 persona
python golden-rules-obsidian/scripts/cli.py council "Dilema atau keputusan teknis" --save
```

---

## 📁 Struktur Hirarki Vault

```
Vault/Lemonaru/
├── 00_Meta/
│   ├── Antigravity Logs/
│   │   ├── Index - Antigravity Logs.md    ← [Master Hub MOC]
│   │   ├── [Workspace A]/
│   │   │   ├── Index - [Workspace A].md   ← [Sub-Hub MOC]
│   │   │   └── YYYY-MM-DD - HH.mm - Sesi.md
│   │   └── [Workspace B]/
│   │       ├── Index - [Workspace B].md   ← [Sub-Hub MOC]
│   │       └── YYYY-MM-DD - HH.mm - Sesi.md
│   ├── Concepts/                          ← [Domain Concepts & Council Reviews]
│   └── Learnings/                         ← [Continuous Self-Improvement Logs]
└── 01_Projects/                           ← [Project PRDs & Implementation Plans]
```

---

## 👥 LLM Council Dialectic Methodology

Sidang 5 persona ahli mengevaluasi:
1. **System Architect (🏗️):** Batas modularitas & clean architecture.
2. **Knowledge Graph Engineer (🧠):** Kerapian wikilink & pencegahan amnesia konteks.
3. **Security Auditor (🛡️):** Karantina zero-leakage & isolasi kredensial.
4. **Pragmatic DX Advocate (⚡):** Kecepatan developer & anti-overengineering.
5. **Skeptic Red-Teamer (🔍):** Kerentanan data-loss, race condition & failure modes.
Diakhiri sintesis putusan **Chairman Final Verdict** beserta arahan tindakan konkret.
