"""
Antigravity Storage Discovery Engine.
Inspects local filesystem for conversation databases, metadata, and protobuf stores.
Read-only and safe.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.models import DiscoveryReport
from core.config import DEFAULT_ANTIGRAVITY_ROOT


class AntigravityDiscovery:
    """
    Scans Antigravity storage directory and returns a structured DiscoveryReport.
    """

    @classmethod
    def discover(cls, source_root: Optional[Path] = None) -> DiscoveryReport:
        root = Path(source_root) if source_root else DEFAULT_ANTIGRAVITY_ROOT

        report = DiscoveryReport(
            root=str(root),
            exists=root.exists(),
            databases=[],
            wal_shm_files=[],
            json_files=[],
            jsonl_files=[],
            proto_files=[],
            conversation_stores=[],
            workspace_metadata_sources=[],
            total_files_scanned=0,
            newest_timestamp=None,
            oldest_timestamp=None
        )

        if not root.exists():
            return report

        timestamps: List[datetime] = []

        for item in root.rglob("*"):
            if not item.is_file():
                continue

            report.total_files_scanned += 1
            rel_str = str(item.relative_to(root))
            suffix = item.suffix.lower()

            try:
                mtime = item.stat().st_mtime
                dt = datetime.fromtimestamp(mtime)
                timestamps.append(dt)
            except Exception:
                pass

            # Detect databases
            if suffix in (".db", ".sqlite", ".sqlite3"):
                report.databases.append(rel_str)
                if "conversations" in rel_str.lower():
                    report.conversation_stores.append(rel_str)

            # Detect WAL / SHM
            elif suffix in (".db-wal", ".db-shm", ".sqlite-wal", ".sqlite-shm"):
                report.wal_shm_files.append(rel_str)

            # Detect Protobuf
            elif suffix in (".pb", ".proto", ".bin"):
                report.proto_files.append(rel_str)

            # Detect JSON / JSONL
            elif suffix == ".json":
                report.json_files.append(rel_str)
                if "workspace" in item.name.lower() or "metadata" in item.name.lower():
                    report.workspace_metadata_sources.append(rel_str)
            elif suffix == ".jsonl":
                report.jsonl_files.append(rel_str)

        if timestamps:
            report.newest_timestamp = max(timestamps).isoformat()
            report.oldest_timestamp = min(timestamps).isoformat()

        return report
