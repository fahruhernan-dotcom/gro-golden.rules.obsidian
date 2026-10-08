---
name: gro
description: >
  Golden Rules Obsidian (`gro`) v3.0 — Agent-Native Working Memory & Living Brain System.
  Panggil /gro untuk: resume konteks aktif, simpan & padatkan sesi aktif (high-density technical devlog), search vault, atau council review secara native langsung oleh AI tanpa perantara skrip Python.
tags:
  - ai-memory
  - obsidian
  - knowledge-graph
  - working-memory
  - context-compaction
  - devlog
  - architecture
---

# 🧠 GRO — Golden Rules Obsidian (v3.0 Agent-Native)

> [!NOTE]
> **Arsitektur Agent-Native (Zero-Middleware):**
> Agen AI yang sedang mengobrol memiliki resolusi pemahaman semantik 100% atas percakapan aktif.
> Proses **Resume**, **Simpan (Compaction)**, dan **Search** dieksekusi **langsung oleh AI** menggunakan file tools bawaan, tanpa memanggil subprocess Python eksternal, tanpa mem-parse database SQLite lokal, dan tanpa panggilan LLM sekunder.

---

## ⚡ Routing Intent (`/gro`)

Ketika user memanggil `/gro` atau meminta aksi memori, agen AI langsung mengeksekusi aksi berikut secara native:

| Intent User | Aksi AI Native | Aksi Deterministik |
|---|---|---|
| `resume`, `konteks`, `apa yang terakhir?`, baru buka workspace | 📖 Baca & sajikan `<Workspace>/ActiveContext.md` | Fallback: baca 5 entri terakhir di `Index - <Workspace>.md` |
| `simpan`, `arsipkan`, `archive`, `log`, `padatkan sesi` | 💾 Sintesis & tulis 3 berkas vault secara langsung | (Opsional) Jalankan `gro validate` untuk audit kesehatan |
| `cari`, `search`, `pernah kita bahas X?` | 🔍 Cari histori via `grep_search` di direktori vault | Atau jalankan `gro search "query"` |
| `council`, `review`, `uji arsitektur` | 🏛️ Jalankan protokol 5 Persona Advisor + Chairman | Dokumentasikan ke vault jika diminta |
| `rebuild index`, `audit vault` | ⚙️ Jalankan perintah CLI pemeliharaan | Jalankan `gro index` / `gro validate` di terminal |

---

## 🧭 Konvensi Lokasi & Workspace

### 1. Deteksi Base Path Vault
Agen AI mendeteksi lokasi direktori catatan Antigravity Logs dengan urutan prioritas:
1. **Environment Variable:** `GRO_VAULT_ROOT` atau `OBSIDIAN_VAULT_ROOT` (jika disetel).
2. **Auto-Discovery Hirarki:** Cari folder yang memiliki `.obsidian` atau subfolder `00_Meta` dari workspace saat ini atau parent direktori di atasnya.
3. **Direktori Standar Pengguna:** `~/Documents/Obsidian/Vault` atau `~/Obsidian/Vault`.
4. **Fallback Proyek Lokal:** Jika tidak ditemukan vault Obsidian global, gunakan folder `Vault/00_Meta/Antigravity Logs/` di root workspace saat ini.

Subdirektori target:
`<Vault_Root>/00_Meta/Antigravity Logs/<Workspace>/`

### 2. Deteksi Workspace
Nama `<Workspace>` diambil secara otomatis dari nama folder root proyek/workspace yang sedang aktif (contoh: `my-saas-app`). Abaikan subfolder teknis internal seperti `src`, `core`, `.git`, `.agents`.

---

## 🚀 Alur Eksekusi Inti (Hot Path)

---

### Aksi 1: Resume (Recall Konteks Tanpa Amnesia)

**Kapan Dijalankan:** Saat user memanggil `/gro resume`, `"lanjutkan project"`, atau saat agen baru pertama kali aktif di workspace.

**Langkah Agen:**
1. Tentukan `<Workspace>` aktif.
2. Baca berkas living brain menggunakan `view_file`:
   ```
   <base_vault>/<Workspace>/ActiveContext.md
   ```
3. Jika berkas ditemukan, sajikan ke user secara ringkas:
   - 🎯 **Milestone & State Terakhir**
   - 📌 **Checklist Tugas Terbuka (Open TODOs)**
   - ⚙️ **Keputusan Arsitektur Kunci**
   - 📁 **File & Komponen Terakhir Diubah**
4. Jika `ActiveContext.md` belum ada, baca `<base_vault>/<Workspace>/Index - <Workspace>.md` dan sajikan ringkasan 5 sesi terakhir dari tabel Sub-MOC sebagai fallback.

---

### Aksi 2: Simpan (Native Session Compaction)

**Kapan Dijalankan:** Saat user memanggil `/gro`, `/gro simpan`, `"arsipkan sesi"`, atau saat milestone penting tercapai.

**Langkah Agen:** Agen AI mensintesis jalannya sesi saat ini langsung dari konteks percakapan di memori, lalu mengupdate **3 berkas** secara sinkron:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CREATE NOTE SESI        <Workspace>/YYYY-MM-DD - HH.mm - Topik.md        │
│ 2. REFRESH LIVING BRAIN    <Workspace>/ActiveContext.md                     │
│ 3. PREPEND SUB-MOC TABLE   <Workspace>/Index - <Workspace>.md               │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### ✅ Pre-Flight Validation Checklist (Wajib diverifikasi sebelum menulis)
- [ ] Format nama note: `YYYY-MM-DD - HH.mm - Topik.md` (gunakan titik bukan titik dua pada jam, contoh: `05.15`).
- [ ] Topik substantif (masalah & solusi teknis, bukan prompt mentah chat), ≤ 50 karakter.
- [ ] Bersihkan karakter terlarang Windows: `\ / : * ? " < > | [ ] @`.
- [ ] Frontmatter lengkap: `tags`, `date`, `time`, `status`, `workspace`, `conversation_id`, `up`, `sub_hub`.
- [ ] Wikilink `up` dan `sub_hub` menautkan ke `[[Index - <Workspace>]]`.
- [ ] Living brain `ActiveContext.md` diperbarui dengan capaian sesi ini dan tugas berikutnya.
- [ ] Sub-MOC `Index - <Workspace>.md` disisipi 1 baris di atas tabel dan counter `total_sessions` ditambah.

---

#### Template 1: Note Sesi (`YYYY-MM-DD - HH.mm - Topik.md`)
Tulis menggunakan `write_to_file`:

```markdown
---
tags:
  - type/ai-log
  - type/devlog
  - source/antigravity
  - workspace/<Workspace>
date: YYYY-MM-DD
time: "HH:mm"
status: archived
workspace: "<Workspace>"
conversation_id: "<UUID dari metadata sesi>"
part: 1
total_parts: 1
up: "[[Index - <Workspace>]]"
sub_hub: "[[Index - <Workspace>]]"
concepts:
  - "[[AI Agent Systems & Memory]]"
  - "[[Obsidian Working Memory & Rules]]"
---

# <Topik Substantif Sesi>

## 🎯 Ringkasan Eksekutif & Sasaran
- **Masalah/Permintaan:** <Deskripsi masalah atau tugas dari pengguna>
- **Solusi & Hasil Utama:** <Sintesis teknis padat solusi yang diimplementasikan>

## ⚙️ Keputusan Arsitektur & Teknis
- 💡 **Keputusan 1:** <Rasional teknis & kompromi>
- 💡 **Keputusan 2:** <Rasional teknis & kompromi>

## 💬 Poin Dialog Kunci
- **Poin #1:** <Fokus diskusi utama>
- **Poin #2:** <Temuan atau klarifikasi penting>

## 📌 Status & Langkah Selanjutnya
- [x] <Tugas yang berhasil diselesaikan pada sesi ini>
- [ ] <Tugas berikutnya yang masih tertunda>

## 📁 File yang Terpengaruh
- `<path/file_1.py>`
- `<path/file_2.md>`

## 📋 Metadata
- 🆔 **Conversation ID:** `<UUID>`
- 🏷️ **Workspace:** `<Workspace>`
- ⏱️ **Waktu:** `YYYY-MM-DD HH:mm`
- 💬 **Jumlah Pesan:** `<Jumlah turn>`
- 🔗 **Sub-Indeks:** [[Index - <Workspace>]]

> [!example]- 📖 Transkrip Dialog Lengkap
> (Sajikan ringkasan padat per turn dari pesan-pesan utama yang terjadi, dilipat rapi dalam callout)
```

---

#### Template 2: Living Brain (`ActiveContext.md`)
Tulis/timpa menggunakan `write_to_file` (Overwrite: true):

```markdown
---
tags:
  - type/active-context
  - type/working-memory
  - workspace/<Workspace>
workspace: "<Workspace>"
last_updated: "YYYY-MM-DD HH:mm"
status: active
up: "[[Index - <Workspace>]]"
---

# 🧠 Active Context: <Workspace>

> [!tip] 💡 Living Working Memory
> Berkas ini menyimpan state aktif, keputusan kunci, dan tugas tertunda untuk workspace **<Workspace>**.
> Dibaca langsung oleh pengembang atau AI Agent menggunakan `/gro resume`.

## 🎯 Milestone Terkini & Status
- **Sesi Terakhir:** [[YYYY-MM-DD - HH.mm - Topik]] (`YYYY-MM-DD HH:mm`)
- **Ringkasan Capaian:** <Ringkasan 1-2 kalimat hasil sesi terakhir>
- **Status Proyek:** 🟢 Aktif / In Progress

## 📌 Checklist Tugas & Langkah Selanjutnya (Next Actions)
- [x] <Tugas selesai>
- [ ] <Tugas berikutnya yang prioritas>
- [ ] <Tugas berikutnya>

## ⚙️ Keputusan Arsitektur Kunci
- 💡 <Keputusan arsitektur yang aktif berlaku>

## 📁 File & Komponen Kunci Terakhir Diubah
- `<path/file_terakhir_1>`
- `<path/file_terakhir_2>`

## 📜 Riwayat Sesi Terbaru
| Tanggal | Sesi | Ringkasan |
|---|---|---|
| `YYYY-MM-DD HH:mm` | [[YYYY-MM-DD - HH.mm - Topik]] | <Ringkasan padat> |
```

---

#### Template 3: Sub-MOC Update (`Index - <Workspace>.md`)
Gunakan `replace_file_content` untuk:
1. Menambahkan baris sesi terbaru tepat di bawah header tabel markdown:
   ```markdown
   | `YYYY-MM-DD HH:mm` | [[YYYY-MM-DD - HH.mm - Topik]] | <Topik> | <Ringkasan 1 baris> |
   ```
2. Meng-increment angka `total_sessions` di frontmatter dan info callout (misal: `40` → `41`).

---

### Aksi 3: Search (Pencarian Histori Cepat)

**Langkah Agen:**
1. Gunakan `grep_search` pada direktori `<base_vault>/<Workspace>/` (atau seluruh vault jika lintas workspace).
2. Baca file yang relevan menggunakan `view_file`.
3. Sintesis jawaban faktual berdasarkan histori riil yang tercatat di vault.

---

### Aksi 4: Council Review (Sidang Arsitektur 5 Persona)

**Kapan Dijalankan:** Saat menghadapi keputusan besar (database, security, breaking change) atau user memanggil `/gro council`.

**5 Archetype Deliberasi:**
1. 🛡️ **Contrarian (Red Team):** Menyerang asumsi terkuat, mencari fatal flaw & edge cases.
2. 🔬 **First Principles (Axiomatic):** Menelanjangi cargo-cult, mereduksi ke batas komputasi & esensi masalah.
3. 🚀 **Expansionist (Value Multiplier):** Mengidentifikasi 10x upside, skalabilitas, dan leverage jangka panjang.
4. 👁️ **Outsider (Beginner's Mind):** Mengevaluasi kesederhanaan, mendeteksi over-engineering & friksi pengguna.
5. ⚙️ **Executor (Field Commander):** Menilai kelayakan implementasi hari ini, friksi operasional, dan roadmap konkret.

**Sintesis Chairman:**
Menyimpulkan dengan format: Verdict (Approved/Rejected/Modified), Concessions, Non-Negotiables, dan 1 Langkah Konkret.

---

## 🛠️ Python CLI: Cold Path & Maintenance Toolkit

Skrip Python (`gro` CLI) **TIDAK** digunakan untuk live chat session compaction. Skrip Python difungsikan sebagai **Maintenance & Vault Audit Utility**:

```bash
gro index       # Rebuild massal Master Hub & seluruh Sub-MOCs (jika terjadi inkonsistensi)
gro validate    # Audit kesehatan vault, skema YAML frontmatter, dan deteksi broken links
gro search "q"  # Quick keyword lookup dari terminal
```

---

## 🏛️ The 7 Golden Rules v3.0

1. **High-Density Technical Devlogs:** Bukan dump chat mentah. Catat Problem, Solusi, Keputusan, dan TODOs. Transkrip mentah dilipat rapi di bawah.
2. **Cohesive Milestone Checkpoints:** Satu catatan mewakili satu pencapaian logis yang utuh.
3. **Living Project Brain (`ActiveContext.md`):** Satu berkas sumber kebenaran status proyek yang selalu sinkron.
4. **2-Tier Hub-and-Spoke MOC:** Devlog hanya menautkan ke Sub-MOC Workspace (`up: "[[Index - Workspace]]"`).
5. **Semantic Title Hygiene:** Judul substantif, bersih dari prompt mentah dan karakter ilegal Windows.
6. **Zero-Leakage Client Quarantine:** Dilarang mencatat auth token, API key, atau rahasia ke dalam vault.
7. **Agent-Native First:** Sintesis semantik dikerjakan langsung oleh AI; kode Python bertugas untuk audit struktural.
