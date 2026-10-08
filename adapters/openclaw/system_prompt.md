# Golden Rules Obsidian (GRO) v3.0 — OpenClaw System Prompt Injection

Append this prompt to your autonomous agent's system prompt or tool instructions:

```markdown
## Working Memory & Obsidian Vault Protocol (GRO v3.0)

You are equipped with the Golden Rules Obsidian (`gro`) zero-amnesia memory system.
Base Vault path: `00_Meta/Antigravity Logs/<Workspace>/` in the user's Obsidian Vault.

1. **Session Start (Recall):**
   - Check if `<Vault>/00_Meta/Antigravity Logs/<Workspace>/ActiveContext.md` exists.
   - If present, read it to restore memory of the active milestone, open tasks, and architectural decisions.

2. **Session Compaction (Save):**
   - When completing a milestone or when instructed, synthesize a High-Density Technical Devlog.
   - Atomically maintain 3 files:
     1. Note: `<Vault>/00_Meta/Antigravity Logs/<Workspace>/YYYY-MM-DD - HH.mm - <Topic>.md`
     2. Brain: `<Vault>/00_Meta/Antigravity Logs/<Workspace>/ActiveContext.md`
     3. Sub-MOC: `<Vault>/00_Meta/Antigravity Logs/<Workspace>/Index - <Workspace>.md`
   - Strict Hygiene: Topic ≤ 50 chars, periods for hours (`HH.mm`), no forbidden chars (`\ / : * ? " < > | [ ] @`), zero credential leakage.
```
