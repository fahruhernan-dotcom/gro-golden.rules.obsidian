"""
Archive Engine for Persistent Obsidian Memory System.
Coordinates identity resolution, markdown rendering, idempotent file writing,
episodic chunking with capacity bounds, MOC rebuilding, and automatic Self-Improvement experience logging.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import ChatSession
from .identity import SessionIdentityResolver
from .renderer import render_session_markdown
from .sanitizer import make_session_filename, extract_session_title
from .timestamp import parse_timestamp, format_dt
from .indexer import MOCIndexer
try:
    from .self_improvement import SelfImprovementEngine
except ImportError:
    SelfImprovementEngine = None

try:
    from .config import DEFAULT_LOGS_DIR
except ImportError:
    from core.config import DEFAULT_LOGS_DIR

MAX_USER_TURNS_PER_NOTE: int = 8  # Proactive Turn-8 Checkpoint Threshold (Council Amendment)
MAX_LINES_PER_NOTE: int = 300

# Universal Domain Concept Rules for Automatic Star Graph Clustering
CONCEPT_RULES: Dict[str, List[str]] = {
    "Architecture & System Design": ["architecture", "modular", "clean architecture", "system design", "pattern", "domain", "spec"],
    "Database & Persistence": ["database", "schema", "postgres", "postgresql", "sql", "migration", "supabase", "sqlite", "orm", "crud", "query"],
    "DevOps & Cloud Infrastructure": ["docker", "vps", "deployment", "kubernetes", "ci/cd", "nginx", "server", "linux", "cloud", "aws", "gcp"],
    "Frontend UX & Design Systems": ["react", "frontend", "css", "tailwind", "ui", "ux", "component", "responsive", "design system", "next.js", "vite"],
    "API & Service Integration": ["api", "rest", "graphql", "endpoint", "webhook", "grpc", "integration", "payload"],
    "Security, Auth & RBAC": ["auth", "security", "jwt", "oauth", "encryption", "rbac", "permissions", "secret", "isolation"],
    "AI Agent Systems & Memory": ["agent", "llm", "memory", "prompts", "council", "context", "token", "vector", "reasoning", "antigravity"],
    "Obsidian Working Memory & Rules": ["vault", "atomic notes", "graph-native", "memory rules", "chunking", "part 0", "moc", "turn-8", "gro"]
}


class ArchiveEngine:
    """
    Coordinates idempotent archiving of ChatSession objects into Obsidian Vault.
    Natively enforces capacity bounds per markdown file and creates atomic episodic parts.
    """

    def __init__(self, logs_dir: Optional[Path] = None, max_turns: int = MAX_USER_TURNS_PER_NOTE):
        self.logs_dir = Path(logs_dir) if logs_dir else DEFAULT_LOGS_DIR
        self.max_turns = max_turns

    @classmethod
    def detect_concepts(cls, session: ChatSession) -> List[str]:
        """Infers concept links based on messages, titles, and affected files."""
        text_corpus = (
            session.title + " " +
            " ".join(session.affected_files) + " " +
            " ".join([m.content for m in session.messages[:15]])
        ).lower()

        matched = []
        for concept, keywords in CONCEPT_RULES.items():
            if any(k in text_corpus for k in keywords):
                matched.append(concept)
        return matched

    @classmethod
    def chunk_session(
        cls,
        session: ChatSession,
        max_turns: int = MAX_USER_TURNS_PER_NOTE
    ) -> List[ChatSession]:
        """
        Splits a long ChatSession into atomic, capacity-controlled Part chunks.
        """
        user_indices = [i for i, m in enumerate(session.messages) if m.role == "user"]
        if len(user_indices) <= max_turns:
            session.part = 1
            session.total_parts = 1
            if not session.concepts:
                session.concepts = cls.detect_concepts(session)
            return [session]

        chunks: List[ChatSession] = []
        num_turns = len(user_indices)

        for chunk_idx, start_pos in enumerate(range(0, num_turns, max_turns)):
            end_turn_pos = min(start_pos + max_turns, num_turns)
            msg_start_idx = user_indices[start_pos]
            msg_end_idx = user_indices[end_turn_pos] if end_turn_pos < num_turns else len(session.messages)

            chunk_messages = session.messages[msg_start_idx:msg_end_idx]
            if not chunk_messages:
                continue

            part_num = chunk_idx + 1
            first_user_in_chunk = next((m.content for m in chunk_messages if m.role == "user"), None)
            sub_title = extract_session_title(first_user_prompt=first_user_in_chunk, fallback=session.title)
            
            if "Part " not in session.title:
                part_title = f"Part {part_num:02d} - {sub_title}"
            else:
                part_title = f"{session.title} - Part {part_num:02d}"

            chunk_session_obj = ChatSession(
                conversation_id=session.conversation_id,
                workspace_id=session.workspace_id,
                workspace_name=session.workspace_name,
                title=part_title,
                started_at=chunk_messages[0].timestamp if chunk_messages else session.started_at,
                ended_at=chunk_messages[-1].timestamp if chunk_messages else session.ended_at,
                part=part_num,
                total_parts=1,
                prev_part=None,
                next_part=None,
                concepts=[],
                messages=chunk_messages,
                affected_files=[f for f in session.affected_files],
                metadata=dict(session.metadata)
            )
            chunk_session_obj.concepts = cls.detect_concepts(chunk_session_obj)
            chunks.append(chunk_session_obj)

        total_parts = len(chunks)
        for i, c in enumerate(chunks):
            c.total_parts = total_parts
            if i > 0:
                c.prev_part = chunks[i-1].title
            if i < total_parts - 1:
                c.next_part = chunks[i+1].title

        return chunks

    def save_session(
        self,
        session: ChatSession,
        dry_run: bool = False,
        rebuild_mocs: bool = True
    ) -> Dict[str, Any]:
        """
        Saves or updates a ChatSession note in the vault idempotently,
        auto-chunking into atomic parts if capacity threshold is reached.
        """
        user_turn_count = len([m for m in session.messages if m.role == "user"])

        # Auto-chunking if exceeding capacity
        if user_turn_count > self.max_turns:
            parts = self.chunk_session(session, self.max_turns)
            results = []
            for part_session in parts:
                res = self._save_single_session(part_session, dry_run=dry_run, rebuild_mocs=False)
                results.append(res)

            if rebuild_mocs and not dry_run:
                MOCIndexer.build_all_indexes(logs_dir=self.logs_dir)

            return {
                "status": "success",
                "action": "CHUNKED_PARTS",
                "conversation_id": session.conversation_id,
                "workspace": session.workspace_name,
                "total_parts": len(parts),
                "parts": results,
                "messages_count": len(session.messages),
                "affected_files_count": len(session.affected_files)
            }

        # Single note execution
        if not session.concepts:
            session.concepts = self.detect_concepts(session)
        return self._save_single_session(session, dry_run=dry_run, rebuild_mocs=rebuild_mocs)

    def _save_single_session(
        self,
        session: ChatSession,
        dry_run: bool = False,
        rebuild_mocs: bool = True
    ) -> Dict[str, Any]:
        ws_name = session.workspace_name or "Unknown Workspace"
        ws_dir = self.logs_dir / ws_name

        existing_parts = SessionIdentityResolver.find_session_parts(
            logs_dir=self.logs_dir,
            conversation_id=session.conversation_id,
            workspace_name=ws_name
        )
        existing_note = None
        for p_num, p_path in existing_parts:
            if p_num == session.part:
                existing_note = p_path
                break

        if not existing_note and len(existing_parts) == 1 and session.part == 1:
            existing_note = existing_parts[0][1]

        dt_start, _ = parse_timestamp(session.started_at)
        formatted_dt = format_dt(dt_start)
        base_name = make_session_filename(
            date_str=formatted_dt["date"],
            time_file_part=formatted_dt["file_time"],
            title=session.title
        )

        target_file, action_type = SessionIdentityResolver.resolve_target_file(
            target_folder=ws_dir,
            base_filename=base_name,
            session=session,
            existing_note=existing_note
        )

        md_content = render_session_markdown(session)

        if dry_run:
            return {
                "status": "dry-run",
                "action": action_type,
                "conversation_id": session.conversation_id,
                "workspace": ws_name,
                "target_file": str(target_file),
                "messages_count": len(session.messages),
                "affected_files_count": len(session.affected_files)
            }

        ws_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(md_content, encoding="utf-8")

        if SelfImprovementEngine:
            try:
                learnings = SelfImprovementEngine.analyze_session(session.messages, ws_name)
                if learnings:
                    SelfImprovementEngine.record_global_learning(
                        learnings=learnings,
                        workspace_name=ws_name,
                        session_title=session.title
                    )
            except Exception as e:
                print(f"[Warning] Gagal mencatat self-improvement: {e}")

        if rebuild_mocs:
            MOCIndexer.build_all_indexes(logs_dir=self.logs_dir)

        return {
            "status": "success",
            "action": action_type,
            "conversation_id": session.conversation_id,
            "workspace": ws_name,
            "target_file": str(target_file),
            "messages_count": len(session.messages),
            "affected_files_count": len(session.affected_files)
        }
