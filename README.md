# 🧠 Golden Rules Obsidian (`gro`)

> **Your AI agent is brilliant, but it has severe short-term memory loss.**  
> `gro` is the zero-dependency, agent-native working memory engine that turns your Obsidian vault into a structured project brain — for **Google Antigravity**, **Claude Code**, **Cursor**, and **OpenClaw**.

[![CI](https://github.com/fahruhernan-dotcom/gro-golden.rules.obsidian/actions/workflows/ci.yml/badge.svg)](https://github.com/fahruhernan-dotcom/gro-golden.rules.obsidian/actions)
[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/fahruhernan-dotcom/gro-golden.rules.obsidian/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Zero-Dependency](https://img.shields.io/badge/dependencies-0%20(Pure%20Stdlib)-brightgreen.svg)](pyproject.toml)
[![Universal Multi-Agent](https://img.shields.io/badge/agents-Antigravity%20|%20Claude%20Code%20|%20Cursor%20|%20OpenClaw-purple.svg)](adapters/)

---

## 💀 The Relatable Nightmare

We've all been there:

You spend 4 hours in deep flow with an AI agent. You refactor the auth system, kill 8 subtle race conditions, and carefully document why SQLite WAL mode was chosen over Postgres for local caching.

Next morning, you open a new chat:

> **You:** *"Hey, let's continue with the auth middleware."*  
> **AI:** *"Sure! What tech stack are you using, and what does your project do?"* 🤦‍♂️

**Total Amnesia.**

---

## 🛑 Why Existing AI Memory Tools Suck

Every tool on the market promises "infinite memory", but they all make the same mistakes:

| ❌ What They Do | 💥 Why It Fails |
|---|---|
| **Heavy Background Daemons** | Runs a background Python process polling SQLite every 2 seconds. Eats your laptop battery, locks files, and crashes silently. |
| **Raw Chat Dumps** | Ingests 5,000 lines of *"Yes please"*, *"Run npm build"*, and raw stack traces. Your Obsidian Graph View becomes an unreadable hairball. |
| **Secondary LLM Token Tax** | Calls an external OpenAI/Anthropic API behind your back just to summarize your conversation. More latency, more bills, and random `401 Unauthorized` errors. |

---

## 💡 The "Aha!" Moment: Agent-Native Memory

Why run an external script to spy on your chat when **the AI you're already talking to already understands 100% of the context?**

With **GRO v3.0**, there is:
- **No background daemon.**
- **No secondary API keys.**
- **No external pip dependencies.**

**The AI you are chatting with is the memory engine.**

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🌅 MORNING: ZERO-AMNESIA RECALL (1 Second)                                  │
│                                                                             │
│ You: "/gro resume"                                                          │
│ AI : Reads <Workspace>/ActiveContext.md from your vault                      │
│                                                                             │
│ Result: AI instantly knows:                                                 │
│  ✓ What we shipped yesterday                                                │
│  ✓ Open TODOs & active blockers                                             │
│  ✓ Architectural rules & key file paths                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🚀 EVENING / MILESTONE COMPLETE: ATOMIC COMPACTION                          │
│                                                                             │
│ You: "/gro"                                                                 │
│ AI : In-memory compaction straight into Obsidian:                           │
│  ① High-Density Devlog note (Problem, Solution, Diffs, Lessons)             │
│  ② Updates ActiveContext.md (The single source of truth)                    │
│  ③ Links cleanly to your Workspace Sub-MOC                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌌 The Obsidian Graph: Hairball vs Constellation

Most tools ruin your Obsidian vault:

```text
❌ WITHOUT GRO (The Graph Hairball)        ✨ WITH GRO (2-Tier Hub-and-Spoke)
                                                
         *   *                                         [Master Hub]
       *   \ | /  *                                     /        \
      * -- (MESS) -- *                          [Project A]    [Project B]
       *   / | \  *                              /   |   \      /   |   \
         *   *                                  *    *    *    *    *    *
 (500 random unlinked chat dumps)           (Clean, organized solar systems)
```

In GRO, notes **only link upward** to their workspace index (`up: "[[Index - Project]]"`).  
Your graph stays pristine, clean, and effortlessly navigable.

---

## 🏛️ The 6 Golden Rules

1. **High-Density Devlogs, Not Chat Dumps:** Notes capture *Architectural Decisions, Code Deltas, and Lessons Learned*. Raw chat transcripts are collapsed neatly at the bottom.
2. **One Milestone, One Note:** Checkpoints are tied to logical milestones (e.g., *"Refactor Auth Layer"*), not arbitrary 10-message intervals.
3. **The Living Brain (`ActiveContext.md`):** One markdown dashboard per project that always mirrors current state, open tasks, and active design decisions.
4. **2-Tier Hub-and-Spoke:** Master Hub ➔ Workspace Index ➔ Milestone Notes. Never cross-link ad-hoc across workspaces.
5. **Deterministic File Hygiene:** `YYYY-MM-DD - HH.mm - Topic.md`. 100% Windows-safe, chronological, human-readable.
6. **Zero Token Tax:** The AI writes devlogs during the conversation using standard file tools. No third-party LLM calls, zero extra cost.

---

## ⚡ 10-Second Quickstart

GRO works across your favorite AI coding environments:

### 🛸 Google Antigravity
Already installed globally:
```bash
/gro resume    # Load yesterday's context
/gro           # Save current milestone
```

### ⚡ Claude Code
Drop the skill into your Claude skills directory:
```bash
mkdir -p ~/.claude/skills/gro
cp adapters/claude-code/SKILL.md ~/.claude/skills/gro/SKILL.md
```

### 🎯 Cursor IDE
Drop the rules into your project:
```bash
cp adapters/cursor/.cursorrules .cursorrules
```

### 🦾 OpenClaw / Autonomous Agents
Inject [`adapters/openclaw/system_prompt.md`](adapters/openclaw/system_prompt.md) directly into your agent's system instructions.

---

## 🧰 The Pure Python Stdlib CLI (Cold Path)

For deterministic bulk maintenance (re-indexing 20+ folders, validating 300+ wikilinks, or offline search), GRO includes a zero-dependency CLI using **Python Standard Library only**:

```bash
# Optional CLI install (0 external pip packages)
pip install -e . --no-deps
```

```bash
gro resume                 # Print active context of current workspace
gro resume --for-agent     # Output formatted markdown for agent prompt injection
gro index                  # Rebuild Master Hub and all Workspace Sub-MOCs
gro validate               # Instant health check: audit broken links & frontmatter
gro search "jwt auth"      # Lightning-fast keyword & metadata search across vault
gro pack                   # Export structured JSON context bundle
```

---

## 📁 Vault Structure at a Glance

```text
Your-Vault/
└── 00_Meta/
    └── Antigravity Logs/
        ├── Index - Antigravity Logs.md       ← [Master Hub]
        │
        ├── Project-Alpha/
        │   ├── ActiveContext.md              ← [Living Brain: Read at session start]
        │   ├── Index - Project-Alpha.md      ← [Workspace Sub-MOC]
        │   └── 2026-10-09 - 05.15 - Auth.md  ← [Atomic Devlog]
        │
        └── Project-Beta/
            ├── ActiveContext.md
            ├── Index - Project-Beta.md
            └── 2026-10-08 - 21.00 - Cache.md
```

---

## 📜 License

[MIT](LICENSE). Built for developers who love clean architecture, clean git history, and clean Obsidian graphs.
