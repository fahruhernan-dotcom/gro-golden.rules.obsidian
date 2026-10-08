---
name: gro
description: >
  Golden Rules Obsidian (`gro`) v3.0 — Universal Agent-Native Working Memory Engine for Claude Code.
  Provides zero-amnesia context recall via ActiveContext.md, high-density technical devlog compaction, and 2-tier MOC index management.
---

# 🧠 Golden Rules Obsidian (`gro`) for Claude Code

Universal Zero-Dependency Working Memory Protocol for Claude Code agents.
Zero Python dependencies required — uses Claude Code's native file read/write capabilities.

## Setup in Claude Code
Place or symlink this file to:
- Workspace: `.claude/skills/gro/SKILL.md`
- Global: `~/.claude/skills/gro/SKILL.md`

## 1. Recall Session Context
When asked to resume or continue:
```bash
# Read the workspace ActiveContext
cat "path/to/Vault/00_Meta/Antigravity Logs/<Workspace>/ActiveContext.md"
```
Or use Claude Code's file read tool directly.

## 2. Archive & Compact Session
When asked to save or archive (`/gro`):
1. **Synthesize:** Extract Problem, Solution, Architectural Decisions, Code Delta, and TODOs directly from the chat context.
2. **Write Devlog:** Create `<Vault>/00_Meta/Antigravity Logs/<Workspace>/YYYY-MM-DD - HH.mm - <Topic>.md`
3. **Update Living Context:** Update `<Vault>/00_Meta/Antigravity Logs/<Workspace>/ActiveContext.md`
4. **Update Sub-MOC:** Prepend a row to `<Vault>/00_Meta/Antigravity Logs/<Workspace>/Index - <Workspace>.md`

## 3. Maintenance Utility (Optional)
If Python is available:
```bash
gro index       # Rebuild Master Hub & Sub-MOC tables
gro validate    # Audit link and YAML frontmatter integrity
```
