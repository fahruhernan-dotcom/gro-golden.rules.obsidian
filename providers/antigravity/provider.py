"""
Antigravity History Provider Implementation.
Adapts Antigravity IDE SQLite databases, protobuf streams, and metadata into canonical ChatSession objects.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, Iterable, Dict, Any, List

from core.models import ChatMessage, ChatSession, DiscoveryReport, InspectionReport
from core.history_provider import HistoryProvider
from core.config import DEFAULT_ANTIGRAVITY_ROOT, DEFAULT_CONVERSATIONS_DIR
from core.timestamp import parse_timestamp, format_dt
from core.sanitizer import extract_session_title

from .sqlite import SafeDatabaseReader, DatabaseReadError
from .discovery import AntigravityDiscovery
from .protobuf import extract_user_text_from_payload, extract_assistant_text_from_payload
from .workspace import resolve_workspace, extract_workspace_from_blob
from .affected_files import extract_affected_files


class AntigravityHistoryProvider(HistoryProvider):
    """
    Concrete HistoryProvider for Google Antigravity IDE storage.
    """

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = Path(root_dir) if root_dir else DEFAULT_ANTIGRAVITY_ROOT
        self.conv_dir = self.root_dir / "conversations"

    def discover(self, source_root: Optional[Path] = None) -> DiscoveryReport:
        target_root = Path(source_root) if source_root else self.root_dir
        return AntigravityDiscovery.discover(target_root)

    def inspect(self, target: Path) -> InspectionReport:
        target_file = Path(target)
        report = InspectionReport(
            file=str(target_file),
            name=target_file.name,
            exists=target_file.exists(),
            is_valid_source=False,
            readable=False,
            tables={},
            detected_fields={},
            error=None
        )

        if not target_file.exists():
            report.error = "File does not exist"
            return report

        try:
            with SafeDatabaseReader(target_file) as reader:
                report.is_valid_source = True
                report.readable = True
                tables = reader.list_tables()
                for tbl in tables:
                    try:
                        cur = reader.conn.cursor()
                        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                        report.tables[tbl] = cur.fetchone()[0]
                    except Exception:
                        report.tables[tbl] = 0

                report.detected_fields = {
                    "has_trajectory_meta": "trajectory_meta" in tables,
                    "has_steps": "steps" in tables,
                    "has_metadata_blob": "trajectory_metadata_blob" in tables
                }
        except DatabaseReadError as e:
            report.error = str(e)
        except Exception as e:
            report.error = f"Unexpected inspection error: {e}"

        return report

    def extract(
        self,
        source_dir: Optional[Path] = None,
        limit: Optional[int] = None
    ) -> Iterable[ChatSession]:
        target_dir = Path(source_dir) if source_dir else self.conv_dir
        if not target_dir.exists():
            return

        db_files = sorted(target_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        if limit and limit > 0:
            db_files = db_files[:limit]

        for db_file in db_files:
            session = self._extract_db_file(db_file)
            if session:
                yield session

    def extract_session(self, conversation_id: str) -> Optional[ChatSession]:
        if not conversation_id:
            # Pick the most recently modified database
            db_files = sorted(self.conv_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not db_files:
                return None
            return self._extract_db_file(db_files[0])

        db_path = self.conv_dir / f"{conversation_id}.db"
        if not db_path.exists():
            # Search recursively if needed
            matches = list(self.root_dir.rglob(f"{conversation_id}.db"))
            if matches:
                db_path = matches[0]
            else:
                return None

        return self._extract_db_file(db_path)

    def _extract_db_file(self, db_file: Path) -> Optional[ChatSession]:
        try:
            with SafeDatabaseReader(db_file) as reader:
                meta = reader.read_trajectory_meta()
                blob = reader.read_trajectory_metadata_blob()
                steps = list(reader.stream_steps(chunk_size=200))
        except DatabaseReadError:
            return None
        except Exception:
            return None

        return self._normalize_record(db_file, meta, blob, steps)

    def _normalize_record(
        self,
        db_path: Path,
        meta: Optional[Dict[str, Any]],
        metadata_blob: Optional[bytes],
        steps: List[Any]
    ) -> Optional[ChatSession]:
        conversation_id = db_path.stem
        if meta and meta.get("trajectory_id"):
            conversation_id = meta["trajectory_id"]

        # 1. Resolve Workspace
        ws_name, original_path = extract_workspace_from_blob(metadata_blob)
        if ws_name == "Unknown Workspace":
            ws_name, original_path = resolve_workspace(metadata={"conversation_id": conversation_id})

        # 2. Extract Messages and Timestamps
        messages: List[ChatMessage] = []
        payloads_for_files: List[bytes] = []
        session_start_epoch: Optional[int] = None
        session_end_epoch: Optional[int] = None

        current_user_text: Optional[str] = None
        current_user_ts: Optional[datetime] = None
        current_assistant_chunks: List[str] = []
        current_assistant_ts: Optional[datetime] = None

        try:
            file_mtime = db_path.stat().st_mtime if db_path.exists() else datetime.now().timestamp()
        except Exception:
            file_mtime = datetime.now().timestamp()

        for step in steps:
            if isinstance(step, (tuple, list)):
                if len(step) == 3:
                    idx, stype, payload = step
                elif len(step) >= 3:
                    idx, stype, payload = step[0], step[1], step[-1]
                else:
                    continue
            else:
                continue

            if not payload:
                continue

            payloads_for_files.append(payload)

            # Step 14: User Input
            if stype == 14:
                if current_user_text is not None:
                    messages.append(ChatMessage(
                        conversation_id=conversation_id,
                        workspace_id=ws_name,
                        timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
                        role="user",
                        step_type=14,
                        content=current_user_text
                    ))
                    if current_assistant_chunks:
                        messages.append(ChatMessage(
                            conversation_id=conversation_id,
                            workspace_id=ws_name,
                            timestamp=current_assistant_ts.isoformat() if current_assistant_ts else format_dt(datetime.now())["iso"],
                            role="assistant",
                            step_type=15,
                            content="\n\n".join(current_assistant_chunks)
                        ))
                    current_user_text = None
                    current_assistant_chunks = []

                u_texts, ts_epoch = extract_user_text_from_payload(payload)
                if ts_epoch:
                    dt_user, ep = parse_timestamp(ts_epoch)
                    if session_start_epoch is None:
                        session_start_epoch = ep
                    session_end_epoch = ep
                else:
                    dt_user, ep = parse_timestamp(file_mtime)

                current_user_ts = dt_user
                current_user_text = u_texts[0] if u_texts else "[Instruksi Sesi]"

            # Step 15: Assistant Response
            elif stype == 15:
                a_texts = extract_assistant_text_from_payload(payload)
                for at in a_texts:
                    if at not in current_assistant_chunks:
                        current_assistant_chunks.append(at)
                current_assistant_ts, _ = parse_timestamp(file_mtime)

        # Commit final turn
        if current_user_text is not None:
            messages.append(ChatMessage(
                conversation_id=conversation_id,
                workspace_id=ws_name,
                timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
                role="user",
                step_type=14,
                content=current_user_text
            ))
            if current_assistant_chunks:
                messages.append(ChatMessage(
                    conversation_id=conversation_id,
                    workspace_id=ws_name,
                    timestamp=current_assistant_ts.isoformat() if current_assistant_ts else format_dt(datetime.now())["iso"],
                    role="assistant",
                    step_type=15,
                    content="\n\n".join(current_assistant_chunks)
                ))
            else:
                messages.append(ChatMessage(
                    conversation_id=conversation_id,
                    workspace_id=ws_name,
                    timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
                    role="assistant",
                    step_type=15,
                    content="Sesi interaksi / eksekusi tool otomatis."
                ))

        if session_start_epoch is None:
            session_start_epoch = int(file_mtime)
        if session_end_epoch is None:
            session_end_epoch = session_start_epoch

        start_dt, _ = parse_timestamp(session_start_epoch)
        end_dt, _ = parse_timestamp(session_end_epoch)

        affected_files = extract_affected_files(payloads_for_files)

        if not messages and not affected_files:
            return None

        first_user_prompt = messages[0].content if messages else None
        title = extract_session_title(
            native_title=None,
            first_user_prompt=first_user_prompt,
            fallback="Diskusi Antigravity"
        )

        return ChatSession(
            conversation_id=conversation_id,
            workspace_id=ws_name,
            workspace_name=ws_name,
            title=title,
            started_at=start_dt.isoformat(),
            ended_at=end_dt.isoformat(),
            messages=messages,
            affected_files=affected_files,
            metadata={
                "source_db": db_path.name,
                "original_workspace_path": original_path
            }
        )
