# 🌟 Golden Rules Obsidian (`gro`)
### *Production-Grade Persistent Working Memory & Hub-and-Spoke Knowledge Architecture for Autonomous AI Coding Agents*

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg?style=for-the-badge&logo=python)](https://python.org)
[![Pytest Suite](https://img.shields.io/badge/Pytest-58%2F58%20Passing%20(100%25)-success.svg?style=for-the-badge&logo=pytest)](https://docs.pytest.org)
[![Architecture](https://img.shields.io/badge/Architecture-3--Tier%20Clean%20Decoupled-orange.svg?style=for-the-badge)](./core)
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](./LICENSE)

---

## ⚡ Executive Overview

**Golden Rules Obsidian (`gro`)** is an enterprise-grade, agent-agnostic memory engine and knowledge architecture designed for autonomous AI pair programmers (Google Antigravity, Claude Code, Cursor, OpenClaw, and Hermes). 

By transforming volatile LLM chat trajectories and runtime states into a self-organizing, **2-Tier Hub-and-Spoke Obsidian Vault**, `gro` solves the two greatest engineering bottlenecks in agentic development:
1. **Context Compaction Amnesia:** Critical instructions, technical schemas, and architectural trade-offs being silently erased when context windows reach their compaction thresholds.
2. **Graph View Hairballs:** Flat, chaotic file dumps that degrade Obsidian's knowledge graph into an unnavigable ball of mud.

---

## 💥 The Vibe-Coder Dilemma: Amnesia vs. Hairballs

When building complex systems with AI coding agents:
```
┌────────────────────────────────────────┐
│  AI Agent Long Session (>50,000 tokens) │
└───────────────────┬────────────────────┘
                    ▼
       ┌─────────────────────────┐
       │   Context Auto-Compact  │ ──► Amnesia: Lost instructions, forgotten schemas, hallucinated APIs
       └─────────────────────────┘
                    │
            Naive File Dump
                    ▼
       ┌─────────────────────────┐
       │  Obsidian Graph Chaos   │ ──► Hairball: 200+ disconnected nodes, broken links, zero MOC structure
       └─────────────────────────┘
```

**Golden Rules Obsidian** eliminates both failure modes through an automated, test-proven 3-tier architecture with proactive session chunking, semantic title sanitization, and 5-advisor peer review.

---

## 🏛️ The 7 Golden Rules

| # | Golden Rule | Principle & Implementation |
|---|:---|:---|
| **1** | **Atomic Notes** | Every `.md` note encapsulates exactly **one** cohesive milestone. Notes are bounded to a maximum of **250–300 Markdown lines** (~15–20 KB) or 8–10 user turns to preserve high semantic density. |
| **2** | **Proactive Turn-8 Checkpoints** | Long engineering sessions are automatically split into sequential episodic parts (`YYYY-MM-DD - HH.mm - Part 01 - [Topic].md`, `Part 02`, etc.) connected via bidirectional `prev_part` and `next_part` frontmatter links before token compaction can erase history. |
| **3** | **2-Tier Hub-and-Spoke MOC** | Master Index (`Index - Antigravity Logs.md`) only references Sub-Hubs (`Index - [Workspace].md`). Individual session notes link strictly to their Workspace Sub-Hub (`up: "[[Index - Workspace]]"`), never dumping directly to root. |
| **4** | **Star Graph Clusters** | Session notes automatically link domain concepts (`[[Database Architecture]]`, `[[DevOps VPS Ubuntu]]`), transforming the Obsidian Graph View into beautiful, logically clustered star constellations. |
| **5** | **Semantic Title Hygiene** | Strictly bans using raw user prompts (e.g. *"cek vault kita sampai mana"*) as note titles. Sanitizes filenames against Windows reserved words (`CON`, `PRN`, `AUX`) and generates high-fidelity technical summaries. |
| **6** | **Zero-Leakage Client Isolation** | Enforces a strict quarantine perimeter preventing client financial records, proprietary API tokens, and secret credentials from leaking into multi-tenant or holding-level knowledge hubs. |
| **7** | **LLM Council Gatekeeping** | High-stakes architectural dilemmas are reviewed by a 5-expert dialectic panel (System Architect, Memory Engineer, Security Auditor, Pragmatic DX Advocate, and Skeptic Red-Teamer) with a synthesized Chairman verdict before committing code. |

---

## 🏗️ 3-Tier Clean Architecture

```
golden-rules-obsidian/
│
├── 🧠 core/                       [TIER 1: AGENT-AGNOSTIC DOMAIN LOGIC]
│   ├── models.py                  (ChatMessage, ChatSession, Workspace, MOC dataclasses)
│   ├── history_provider.py        (Abstract interface for session ingest)
│   ├── archive_engine.py          (Idempotent save, update & dry-run processor)
│   ├── identity.py                (Session identity resolver & collision handling)
│   ├── indexer.py                 (2-tier MOC index builder with markdown tables)
│   ├── renderer.py                (Obsidian-compliant YAML frontmatter & callouts)
│   ├── sanitizer.py               (Windows-safe filename & wikilink cleaner)
│   ├── search.py                  (Fast multi-criteria vault search engine)
│   ├── validator.py               (Frontmatter schema, link integrity & broken link auditor)
│   ├── timestamp.py               (Robust multi-format parser: Unix, ISO8601, SQLite, Proto)
│   └── config.py                  (Path resolvers & environment configurations)
│
├── 🔌 providers/                  [TIER 2: ENGINE ADAPTERS]
│   ├── antigravity/               (Google Antigravity IDE Provider)
│   │   ├── provider.py            (Full AntigravityHistoryProvider implementation)
│   │   ├── sqlite.py              (Read-only SQLite connection & safe schema inspector)
│   │   ├── protobuf.py            (Varint payload decoder & message stream extractor)
│   │   ├── workspace.py           (Multi-platform workspace path to project mapper)
│   │   ├── discovery.py           (Safe DB discovery across workspace directories)
│   │   └── affected_files.py      (Diff & file mutation tracker)
│   └── (mock / openclaw / claude) (Extensible adapter contracts)
│
├── 💻 scripts/ & cli.py           [TIER 3: UNIFIED CLI & AUTOMATION]
│   ├── cli.py                     (Single-binary CLI: `golden-rules-obsidian` / `gro`)
│   ├── council.py                 (5-Persona LLM Council Deliberation Engine)
│   ├── archive_session.py         (Session archiver with proactive turn-8 chunking)
│   ├── build_index.py             (MOC regenerator)
│   ├── search_vault.py            (Vault search CLI)
│   └── validate_vault.py          (Vault health and schema checker)
│
└── 🧪 tests/                      [AUTOMATED REGRESSION SUITE]
    └── (58 passing tests across unit, integration, and fuzz scenarios)
```

---

## 🚀 Quickstart & Installation

### Option A: Standard Pip / UV Install
```bash
# Clone the repository
git clone https://github.com/fahruhernansakti/golden-rules-obsidian.git
cd golden-rules-obsidian

# Install in development mode with dev tools
pip install -e .[dev]

# Verify installation
gro --help
```

### Option B: Drop-in Agent Skill
Copy the entire `golden-rules-obsidian/` folder into your agent's skill directory:
- **Google Antigravity:** `.agents/skills/obsidian-vault/`
- **Claude Code:** `~/.claude/skills/obsidian-vault/`
- **Cursor / OpenClaw:** `.cursor/skills/golden-rules-obsidian/`

---

## 💻 Unified CLI Reference (`gro`)

```bash
# General Syntax
gro <subcommand> [flags]
```

### 1. `gro archive` — Archive Sesi Aktif
Simpan sesi percakapan LLM saat ini ke dalam Obsidian Vault lengkap dengan metadata frontmatter, file terpengaruh, dan transkrip terlipat:
```bash
# Otomatis deteksi sesi aktif dan arsipkan ke workspace yang tepat
gro archive

# Berikan judul substantif kustom
gro archive --topic "Refactoring Data Layer Supabase Dual Layer"

# Mode Dry-Run (simulasi tanpa menyentuh disk)
gro archive --dry-run
```

### 2. `gro search` — Pencarian Konteks Super Cepat
Temukan keputusan arsitektur dan potongan kode dari ratusan sesi lampau dalam hitungan milidetik:
```bash
# Cari kata kunci di seluruh vault
gro search "Supabase RLS"

# Filter berdasarkan workspace spesifik dan batas tanggal
gro search "migration" --workspace "EcommerceBackend" --after 2026-08-01

# Ekspor hasil pencarian ke JSON murni (cocok untuk piping ke agent LLM)
gro search "VPS Ubuntu" --json --limit 5
```

### 3. `gro index` — Rebuild 2-Tier Hub-and-Spoke MOC
Otomatis membangun ulang Master MOC dan seluruh Sub-Indeks Workspace dengan tabel ringkasan eksekutif:
```bash
gro index
```

### 4. `gro validate` — Audit Kesehatan & Integritas Vault
Audit 100% berkas Markdown, validasi frontmatter tags, cek broken wikilinks, dan verifikasi kepatuhan Golden Rules:
```bash
gro validate
```

### 5. `gro council` — Sidang 5 Penasihat Arsitektur (LLM Council)
Jalankan peninjauan dialektika 5 persona ahli terhadap dilema teknis sebelum mengambil keputusan besar:
```bash
gro council "Should we cache Supabase data in local SQLite or localStorage?"

# Simpan hasil telaah dewan langsung ke node Konsep Obsidian
gro council "Should we migrate from Next.js Pages to App Router?" --save
```

---

## 🧪 Test Suite & Quality Assurance

The engine is protected by **58 automated unit & integration tests** covering SQLite corruption recovery, protobuf decoding, Windows reserved filename edge-cases, MOC regeneration, and idempotent archiving:

```powershell
pytest tests -v
```

```
============================= test session starts =============================
collected 58 items

tests/test_core_identity.py::test_compute_stable_identity_primary PASSED [  1%]
tests/test_core_identity.py::test_compute_stable_identity_fallback_hash PASSED [  3%]
tests/test_discovery.py::test_discover_antigravity_files PASSED          [ 12%]
tests/test_idempotency.py::test_idempotent_archive_updates_existing_note PASSED [ 15%]
tests/test_indexes.py::test_build_all_indexes PASSED                     [ 20%]
tests/test_sanitizer.py::test_sanitize_windows_reserved_names PASSED     [ 36%]
tests/test_search.py::test_search_by_query_in_content PASSED             [ 48%]
tests/test_sqlite_reader.py::test_reader_read_only_enforcement PASSED   [ 55%]
tests/test_timestamp.py::test_parse_protobuf_timestamp_dict PASSED      [ 74%]
tests/test_validator.py::test_validator_pass_on_clean_vault PASSED      [ 84%]
tests/test_validator.py::test_validator_fails_on_broken_links PASSED    [ 89%]
tests/test_workspace.py::test_resolve_from_windows_path PASSED          [ 93%]

============================= 58 passed in 1.29s ==============================
```

---

## 👨‍💻 Author & Attribution

**Fahrurosadi Hernan**  
*Full Stack Developer | AI Agent System Architect | Workflow Automation Specialist*  
- 📍 Surakarta, Central Java, Indonesia  
- 📧 [fahruhernansakti@gmail.com](mailto:fahruhernansakti@gmail.com)  
- 🔗 [LinkedIn Profile](https://www.linkedin.com/in/fahrurosadi-hernan-b983a4158)  
- 💼 [GitHub Profile](https://github.com/fahruhernansakti)

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.
