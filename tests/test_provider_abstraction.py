"""
Tests for Provider Abstraction Layer.
Proves that core (ArchiveEngine, MOCIndexer, VaultValidator) is truly agent-agnostic
by using a synthetic MockHistoryProvider (simulating a future Claude Code or Cursor provider).
"""

from pathlib import Path
from typing import Optional, Iterable, List
import pytest

from core.models import ChatMessage, ChatSession, DiscoveryReport, InspectionReport
from core.history_provider import HistoryProvider
from core.archive_engine import ArchiveEngine
from core.indexer import MOCIndexer
from core.validator import VaultValidator


class MockAgentHistoryProvider(HistoryProvider):
    """
    Simulates an alternative agent history source (e.g. Claude Code or Cursor transcript).
    Produces canonical ChatSession models without any Antigravity dependencies.
    """

    def __init__(self, agent_name: str = "claude-code"):
        self.agent_name = agent_name

    def discover(self, source_root: Optional[Path] = None) -> DiscoveryReport:
        return DiscoveryReport(
            root=str(source_root or "/tmp/mock"),
            exists=True,
            databases=[],
            conversation_stores=["session-claude-001.json"],
            total_files_scanned=1
        )

    def inspect(self, target: Path) -> InspectionReport:
        return InspectionReport(
            file=str(target),
            name=Path(target).name,
            exists=True,
            is_valid_source=True,
            readable=True,
            tables={"transcripts": 1}
        )

    def extract(
        self,
        source_dir: Optional[Path] = None,
        limit: Optional[int] = None
    ) -> Iterable[ChatSession]:
        sessions = [
            ChatSession(
                conversation_id="claude-session-101",
                workspace_id="ws-backend",
                workspace_name="Backend Service",
                title="Design Event Pipeline",
                started_at="2026-09-08T14:30:00+07:00",
                ended_at="2026-09-08T14:45:00+07:00",
                messages=[
                    ChatMessage(
                        conversation_id="claude-session-101",
                        workspace_id="ws-backend",
                        timestamp="2026-09-08T14:30:00+07:00",
                        role="user",
                        step_type="USER_INPUT",
                        content="Bagaimana rancangan event pipeline dengan Kafka?"
                    ),
                    ChatMessage(
                        conversation_id="claude-session-101",
                        workspace_id="ws-backend",
                        timestamp="2026-09-08T14:35:00+07:00",
                        role="assistant",
                        step_type="PLANNER_RESPONSE",
                        content="Berikut arsitektur event-driven pipeline menggunakan Kafka topic partitioned by workspace."
                    )
                ],
                affected_files=["src/pipeline/events.py", "config/kafka.yaml"]
            ),
            ChatSession(
                conversation_id="claude-session-102",
                workspace_id="ws-frontend",
                workspace_name="Frontend Portal",
                title="Refactor Theme Provider",
                started_at="2026-09-08T15:00:00+07:00",
                ended_at="2026-09-08T15:15:00+07:00",
                messages=[
                    ChatMessage(
                        conversation_id="claude-session-102",
                        workspace_id="ws-frontend",
                        timestamp="2026-09-08T15:00:00+07:00",
                        role="user",
                        step_type="USER_INPUT",
                        content="Refactor theme context ke Tailwind v4"
                    )
                ],
                affected_files=["src/theme/ThemeContext.tsx"]
            )
        ]
        if limit:
            sessions = sessions[:limit]
        for s in sessions:
            yield s

    def extract_session(self, conversation_id: str) -> Optional[ChatSession]:
        for s in self.extract():
            if s.conversation_id == conversation_id:
                return s
        return None


def test_mock_provider_conforms_to_interface():
    provider = MockAgentHistoryProvider()
    assert isinstance(provider, HistoryProvider)

    disc = provider.discover()
    assert disc.exists is True
    assert len(disc.conversation_stores) == 1

    session = provider.extract_session("claude-session-101")
    assert session is not None
    assert session.title == "Design Event Pipeline"
    assert session.workspace_name == "Backend Service"


def test_core_archives_mock_provider_sessions(temp_vault):
    """
    Verifies that core ArchiveEngine processes MockAgentHistoryProvider sessions
    without any Antigravity-specific code, creating proper Obsidian markdown notes.
    """
    provider = MockAgentHistoryProvider()
    engine = ArchiveEngine(logs_dir=temp_vault)

    for session in provider.extract():
        res = engine.save_session(session=session, dry_run=False, rebuild_mocs=False)
        assert res["status"] == "success"
        assert res["action"] == "CREATE"
        assert Path(res["target_file"]).exists()

    # Rebuild indexes using core MOCIndexer
    indexer = MOCIndexer(logs_dir=temp_vault)
    index_res = indexer.build_all()
    assert Path(index_res["main_moc"]).exists()
    assert len(index_res["sub_mocs"]) >= 2

    # Validate resulting vault
    validator = VaultValidator(logs_dir=temp_vault)
    val_report = validator.validate_all()
    assert val_report.status == "PASS"
    assert val_report.total_notes >= 2
