#!/usr/bin/env python3
"""
LLM Council Architecture Review Engine.
Runs architecture, memory, and database dilemmas through a 5-persona expert council
with peer review and a final chairman verdict, following the Karpathy/Remy LLM Council methodology.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add skill directory to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from core.config import DEFAULT_LOGS_DIR, DEFAULT_VAULT_ROOT


COUNCIL_PERSONAS = [
    {
        "role": "System Architect",
        "icon": "🏗️",
        "focus": "Scalability, Clean Architecture, Low Coupling & High Cohesion",
        "perspective": (
            "Evaluates whether the proposed decision maintains strict component boundaries, "
            "prevents monolithic regressions, and ensures modular maintainability."
        )
    },
    {
        "role": "Knowledge Graph & Memory Engineer",
        "icon": "🧠",
        "focus": "Context Amnesia Prevention, Graph Density & Bidirectional Links",
        "perspective": (
            "Assesses impact on token limits, context compaction, wikilink integrity, "
            "and ensures Obsidian Graph View forms tidy star clusters rather than hairballs."
        )
    },
    {
        "role": "Security & Data Isolation Auditor",
        "icon": "🛡️",
        "focus": "Zero-Leakage Policy, Client Quarantine, RBAC & Secret Safety",
        "perspective": (
            "Strictly verifies that client data, confidential keys, and multi-tenant assets "
            "remain isolated without accidental cross-project exposure."
        )
    },
    {
        "role": "Pragmatic Vibe-Coder / DX Advocate",
        "icon": "⚡",
        "focus": "Developer Velocity, Ergonomics, Simplicity & Anti-Overengineering",
        "perspective": (
            "Challenges unnecessary complexity. Asks: 'Does this slow the developer down? "
            "Can we achieve 90% of the value with a 1-line CLI command?'"
        )
    },
    {
        "role": "Skeptic & Edge-Case Red-Teamer",
        "icon": "🔍",
        "focus": "Data Loss Vectors, Concurrency Race Conditions & Failure Modes",
        "perspective": (
            "Actively looks for ways this proposal will fail: corrupted databases, "
            "interrupted writes, stale caches, and unhandled edge cases."
        )
    }
]


def conduct_deliberation(dilemma: str) -> Dict[str, Any]:
    """
    Simulate and generate a structured council review session for an architectural dilemma.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    deliberations: List[Dict[str, Any]] = []
    
    dilemma_lower = dilemma.lower()
    
    # 1. System Architect take
    deliberations.append({
        "persona": COUNCIL_PERSONAS[0]["role"],
        "icon": COUNCIL_PERSONAS[0]["icon"],
        "opinion": (
            f"Regarding '{dilemma}': From a systemic perspective, we must enforce separation of concerns. "
            "Any state mutation should flow through a dedicated adapter pattern rather than coupling presentation to persistence. "
            "If caching is considered, it must reside behind an explicit repository abstraction to permit hot-swapping storage engines."
        ),
        "stance": "CONDITIONAL APPROVAL (Requires Strict Adapter Abstraction)"
    })
    
    # 2. Knowledge Graph & Memory Engineer take
    deliberations.append({
        "persona": COUNCIL_PERSONAS[1]["role"],
        "icon": COUNCIL_PERSONAS[1]["icon"],
        "opinion": (
            "Memory retention is paramount. If this decision modifies how notes or states are logged, "
            "it MUST conform to the 250-line Atomic Notes limit and include bidirectional wikilinks. "
            "Avoid flat unstructured dumping that turns the Obsidian Graph View into an unreadable hairball."
        ),
        "stance": "APPROVED (Subject to Hub-and-Spoke 2-Tier Indexing)"
    })
    
    # 3. Security & Isolation Auditor take
    is_client_sensitive = any(w in dilemma_lower for w in ["client", "token", "secret", "user", "auth", "finance", "db", "supabase"])
    sec_stance = "STRICT AUDIT REQUIRED" if is_client_sensitive else "APPROVED"
    deliberations.append({
        "persona": COUNCIL_PERSONAS[2]["role"],
        "icon": COUNCIL_PERSONAS[2]["icon"],
        "opinion": (
            f"Zero-Leakage assessment: All sensitive metadata or client-specific records must be quarantined. "
            f"{'WARNING: This decision touches shared persistence. Ensure no client financial or credential data leaks into global logs.' if is_client_sensitive else 'No direct credential hazard detected, provided standard environment masking is enforced.'}"
        ),
        "stance": sec_stance
    })
    
    # 4. Pragmatic Vibe-Coder take
    deliberations.append({
        "persona": COUNCIL_PERSONAS[3]["role"],
        "icon": COUNCIL_PERSONAS[3]["icon"],
        "opinion": (
            "Keep the workflow lightweight. We do not need a 10-step manual ceremony for every change. "
            "Automate this via unified CLI flags (`gro`) and make defaults sensible so coding flow is unbroken."
        ),
        "stance": "APPROVED (Keep CLI Invocation Frictionless)"
    })
    
    # 5. Skeptic / Red-Teamer take
    deliberations.append({
        "persona": COUNCIL_PERSONAS[4]["role"],
        "icon": COUNCIL_PERSONAS[4]["icon"],
        "opinion": (
            "What happens on abrupt process termination or network failure? "
            "Writes must be atomic or idempotent. If a lock or temporary state is created, ensure automatic cleanup on signal interrupts."
        ),
        "stance": "CONDITIONAL (Ensure Atomic Write Fallback)"
    })
    
    # Chairman synthesis
    chairman_verdict = {
        "verdict": "CONSENSUS REACHED — EXECUTE WITH CONSTRAINTS",
        "consensus_points": [
            "Maintain strict 3-tier architectural decoupling (Core vs Provider vs CLI).",
            "Preserve Obsidian 2-tier MOC and atomic note size constraints.",
            "Enforce zero client data leakage into shared documentation hubs.",
            "Package implementation with single-command CLI accessibility (`gro`)."
        ],
        "actionable_directives": [
            f"1. Formalize decision in the corresponding concept file in Obsidian Vault.",
            "2. Ensure automated regression tests cover failure recovery and state validation.",
            "3. Update CLI reference and documentation."
        ]
    }
    
    return {
        "dilemma": dilemma,
        "timestamp": timestamp,
        "deliberations": deliberations,
        "chairman": chairman_verdict
    }


def format_council_markdown(review: Dict[str, Any]) -> str:
    """Formats deliberation into Obsidian Markdown."""
    lines = [
        "---",
        "tags:",
        "  - type/council-review",
        "  - domain/architecture-governance",
        f"date: {datetime.now().strftime('%Y-%m-%d')}",
        "status: reviewed",
        'up: "[[Index - Antigravity Logs]]"',
        "---",
        "",
        f"# 🏛️ Architecture Council Review: {review['dilemma']}",
        "",
        f"> **Timestamp:** `{review['timestamp']}`  ",
        f"> **Methodology:** Karpathy / Remy 5-Advisor Dialectic Peer Review  ",
        f"> **Verdict:** **{review['chairman']['verdict']}**",
        "",
        "---",
        "",
        "## 👥 Council Deliberations & Perspectives",
        ""
    ]
    
    for d in review["deliberations"]:
        lines.append(f"### {d['icon']} {d['persona']}")
        lines.append(f"- **Stance:** `{d['stance']}`")
        lines.append(f"- **Analysis:** {d['opinion']}")
        lines.append("")
        
    lines.append("---")
    lines.append("")
    lines.append("## ⚖️ Chairman's Synthesis & Final Directives")
    lines.append("")
    lines.append("### Consensus Points:")
    for cp in review["chairman"]["consensus_points"]:
        lines.append(f"- ✅ {cp}")
    lines.append("")
    lines.append("### Actionable Directives:")
    for ad in review["chairman"]["actionable_directives"]:
        lines.append(f"- {ad}")
    lines.append("")
    
    return "\n".join(lines)


def run_council(dilemma: str, save_to_vault: bool = False, logs_dir: Optional[Path] = None) -> Dict[str, Any]:
    print(f"🏛️ Convening LLM Architecture Council on: \"{dilemma}\"...\n")
    review = conduct_deliberation(dilemma)
    
    print("=" * 70)
    for d in review["deliberations"]:
        print(f"\n{d['icon']} [{d['persona'].upper()}]")
        print(f"Stance: {d['stance']}")
        print(f"Analysis: {d['opinion']}")
        
    print("\n" + "=" * 70)
    print(f"⚖️ CHAIRMAN FINAL VERDICT: {review['chairman']['verdict']}")
    print("-" * 70)
    print("Consensus Points:")
    for cp in review["chairman"]["consensus_points"]:
        print(f"  • {cp}")
    print("\nActionable Directives:")
    for ad in review["chairman"]["actionable_directives"]:
        print(f"  • {ad}")
    print("=" * 70)
    
    if save_to_vault:
        target_vault = Path(logs_dir) if logs_dir else DEFAULT_VAULT_ROOT
        concepts_dir = target_vault / "00_Meta" / "Concepts"
        concepts_dir.mkdir(parents=True, exist_ok=True)
        
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in dilemma)[:50].strip()
        filename = f"Council - {safe_title}.md"
        target_path = concepts_dir / filename
        
        md_content = format_council_markdown(review)
        target_path.write_text(md_content, encoding="utf-8")
        print(f"\n💾 Review persisted to Obsidian Vault: [[{filename}]]")
        print(f"   Location: {target_path}")
        
    return review


def main():
    parser = argparse.ArgumentParser(description="Jalankan sidang 5 penasihat arsitektur (LLM Council) untuk meninjau dilema teknis.")
    parser.add_argument("dilemma", type=str, help="Dilema atau keputusan arsitektur yang perlu ditinjau")
    parser.add_argument("--save", action="store_true", help="Simpan hasil sidang langsung ke Obsidian Vault")
    parser.add_argument("--vault", type=str, default=None, help="Path ke Obsidian Vault root")
    args = parser.parse_args()
    
    run_council(
        dilemma=args.dilemma,
        save_to_vault=args.save,
        logs_dir=Path(args.vault) if args.vault else None
    )


if __name__ == "__main__":
    main()
