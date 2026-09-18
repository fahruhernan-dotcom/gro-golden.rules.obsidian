"""
History Normalizer.
Transforms raw Antigravity database steps and metadata into normalized ChatSession, ChatMessage, and Workspace objects.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import ChatMessage, ChatSession, Workspace
from payload_decoder import extract_user_text_from_payload, extract_assistant_text_from_payload
from timestamp_parser import parse_timestamp, format_dt
from workspace_resolver import resolve_workspace
from title_sanitizer import extract_session_title
from affected_files import extract_affected_files

def normalize_database_record(
    db_path: Optional[Path] = None,
    meta: Optional[Dict[str, Any]] = None,
    metadata_blob: Optional[bytes] = None,
    steps: Optional[List[Any]] = None,
    trajectory_meta: Optional[Dict[str, Any]] = None,
    db_file: Optional[Path] = None
) -> Optional[ChatSession]:
    """
    Normalizes a single database conversation record into a ChatSession.
    """
    target_path = Path(db_file or db_path or "unknown.db")
    target_meta = meta or trajectory_meta
    steps_list = steps or []

    conversation_id = target_path.stem
    if target_meta and target_meta.get("trajectory_id"):
        conversation_id = target_meta["trajectory_id"]

    # 1. Resolve Workspace
    ws_uri = None
    if metadata_blob:
        blob_str = metadata_blob.decode("utf-8", errors="ignore")
        m = re.search(r"file:///[^\s\x00-\x1f\"']+", blob_str)
        if m:
            ws_uri = m.group(0)

    workspace_name, original_path = resolve_workspace(
        workspace_path_or_uri=ws_uri,
        metadata={"conversation_id": conversation_id}
    )

    # 2. Extract Messages and Timestamps
    messages: List[ChatMessage] = []
    payloads_for_files: List[bytes] = []
    session_start_epoch: Optional[int] = None
    session_end_epoch: Optional[int] = None

    current_user_text: Optional[str] = None
    current_user_ts: Optional[datetime] = None
    current_assistant_chunks: List[str] = []
    current_assistant_ts: Optional[datetime] = None

    # Compute safe fallback mtime from target_path
    try:
        file_mtime = target_path.stat().st_mtime if target_path.exists() else datetime.now().timestamp()
    except Exception:
        file_mtime = datetime.now().timestamp()

    for step in steps_list:
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

        # Step Type 14: User Input
        if stype == 14:
            # Commit pending previous turn
            if current_user_text is not None:
                messages.append(ChatMessage(
                    conversation_id=conversation_id,
                    workspace_id=workspace_name,
                    timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
                    role="user",
                    step_type=14,
                    content=current_user_text
                ))
                if current_assistant_chunks:
                    messages.append(ChatMessage(
                        conversation_id=conversation_id,
                        workspace_id=workspace_name,
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

        # Step Type 15: Assistant Response
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
            workspace_id=workspace_name,
            timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
            role="user",
            step_type=14,
            content=current_user_text
        ))
        if current_assistant_chunks:
            messages.append(ChatMessage(
                conversation_id=conversation_id,
                workspace_id=workspace_name,
                timestamp=current_assistant_ts.isoformat() if current_assistant_ts else format_dt(datetime.now())["iso"],
                role="assistant",
                step_type=15,
                content="\n\n".join(current_assistant_chunks)
            ))
        else:
            # Tool-only or ongoing interaction
            messages.append(ChatMessage(
                conversation_id=conversation_id,
                workspace_id=workspace_name,
                timestamp=current_user_ts.isoformat() if current_user_ts else format_dt(datetime.now())["iso"],
                role="assistant",
                step_type=15,
                content="Sesi interaksi / eksekusi tool otomatis."
            ))

    # Fallback timestamp if none parsed from protobuf
    if session_start_epoch is None:
        session_start_epoch = int(file_mtime)
    if session_end_epoch is None:
        session_end_epoch = session_start_epoch

    start_dt, _ = parse_timestamp(session_start_epoch)
    end_dt, _ = parse_timestamp(session_end_epoch)

    # 3. Extract Affected Files
    affected_files = extract_affected_files(payloads_for_files)

    # If no messages and no affected files, return None (empty session)
    if not messages and not affected_files:
        return None

    # 4. Extract Title
    first_prompt = messages[0].content if messages else None
    title = extract_session_title(
        native_title=None,
        first_user_prompt=first_prompt,
        fallback="Diskusi Antigravity"
    )

    return ChatSession(
        conversation_id=conversation_id,
        workspace_id=workspace_name,
        workspace_name=workspace_name,
        title=title,
        started_at=start_dt.isoformat(),
        ended_at=end_dt.isoformat(),
        messages=messages,
        affected_files=affected_files,
        metadata={
            "db_name": db_path.name,
            "original_workspace_path": original_path,
            "step_count": len(steps),
            "start_epoch": session_start_epoch
        }
    )
