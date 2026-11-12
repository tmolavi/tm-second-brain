"""Automated acceptance tests (AT-01 through AT-05) for TM Second Brain."""

from __future__ import annotations

import json
import tarfile
from pathlib import Path
from typing import Sequence

from tm_second_brain.backup.archive import VaultBackupManager
from tm_second_brain.core.models import (
    ConfidenceLevel,
    LifecycleStatus,
    MemoryRecord,
    MemoryScope,
    SearchQuery,
    SearchResult,
)
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore
from tm_second_brain.privacy.policy import DefaultPrivacyPolicy


class MockSemanticBackend:
    """Simulated semantic RetrievalBackend for model-switching tests."""

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    @property
    def name(self) -> str:
        return "mock-semantic"

    def index(self, records: Sequence[MemoryRecord]) -> None:
        self._records = list(records)

    def query(self, query: SearchQuery) -> list[SearchResult]:
        # Simulate semantic match even without exact keyword overlap
        hits = [
            SearchResult(record=r, score=0.95, matched_terms=["semantic"], backend=self.name)
            for r in self._records
            if r.status == LifecycleStatus.ACTIVE and not r.private
        ]
        return hits[: query.limit]


def test_at01_model_switching(tmp_path: Path) -> None:
    """AT-01: Swap RetrievalBackend without changing caller code or vault files."""
    store = MarkdownMemoryStore(tmp_path)
    store.remember(
        "SQLite WAL concurrency",
        "Enable WAL mode so concurrent readers do not block.",
        scope=MemoryScope.PROJECT,
        projects=["alpha"],
        confidence=ConfidenceLevel.VERIFIED,
        verification="pytest",
    )

    bm25_hits = store.search(SearchQuery(text="concurrent readers", project="alpha"))
    assert len(bm25_hits) == 1
    assert bm25_hits[0].backend == "bm25"

    store.set_retrieval_backend(MockSemanticBackend())
    sem_hits = store.search(SearchQuery(text="database locking behavior", project="alpha"))
    assert len(sem_hits) == 1
    assert sem_hits[0].backend == "mock-semantic"


def test_at02_offline_operation(tmp_path: Path) -> None:
    """AT-02: Full lifecycle operates offline with zero network/API keys."""
    store = MarkdownMemoryStore(tmp_path)
    w = store.remember(
        "Offline BM25 default",
        "Core search works completely offline with Python stdlib.",
        scope=MemoryScope.GENERAL,
    )
    assert w.record.id.startswith("mem_")
    hits = store.search(SearchQuery(text="offline stdlib"))
    assert len(hits) == 1
    health = store.health()
    assert health["offline_ready"] is True
    assert health["active_memories"] == 1


def test_at03_persistence_and_project_isolation(tmp_path: Path) -> None:
    """AT-03: Memories persist across store restarts and isolate by project."""
    store1 = MarkdownMemoryStore(tmp_path)
    store1.remember("Alpha secret rule", "Only for project alpha.", scope=MemoryScope.PROJECT, projects=["alpha"])
    store1.remember("Beta secret rule", "Only for project beta.", scope=MemoryScope.PROJECT, projects=["beta"])
    store1.remember("Global rule", "Applies everywhere.", scope=MemoryScope.GENERAL)

    # Re-instantiate from disk
    store2 = MarkdownMemoryStore(tmp_path)
    alpha_memories = store2.recall(project="alpha")
    alpha_titles = {m.title for m in alpha_memories}
    assert "Alpha secret rule" in alpha_titles
    assert "Global rule" in alpha_titles
    assert "Beta secret rule" not in alpha_titles


def test_at04_privacy_and_redaction(tmp_path: Path) -> None:
    """AT-04: Private notes are excluded by default and secrets are redacted."""
    store = MarkdownMemoryStore(tmp_path)
    store.remember(
        "Personal medical note",
        "Private health details.",
        scope=MemoryScope.GENERAL,
        private=True,
    )
    store.remember(
        "Public note with leaked token",
        "Accidentally pasted sk-1234567890abcdef1234567890 in notes.",
        scope=MemoryScope.GENERAL,
        private=False,
    )

    recalled = store.recall()
    assert all(m.title != "Personal medical note" for m in recalled)
    assert len(store.recall(include_private=True)) == 2

    bundle_path = tmp_path / "export.json"
    backup_mgr = VaultBackupManager(store)
    res = backup_mgr.export_bundle(bundle_path, include_private=False)
    assert res["count"] == 1
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert "sk-1234567890abcdef1234567890" not in bundle["records"][0]["body"]
    assert "[REDACTED_API_KEY]" in bundle["records"][0]["body"]

    policy = DefaultPrivacyPolicy()
    assert "[REDACTED_GITHUB_TOKEN]" in policy.redact("token=ghp_abcdefghijklmnopqrstuvwxyz123456")


def test_at05_recovery_backup_and_restore(tmp_path: Path) -> None:
    """AT-05: Backup with SHA-256 verification restores deleted memories without clobbering existing files."""
    store = MarkdownMemoryStore(tmp_path)
    m1 = store.remember("Critical decision", "Keep Markdown canonical.", scope=MemoryScope.GENERAL).record
    m2 = store.remember("Second decision", "Never overwrite user notes.", scope=MemoryScope.GENERAL).record

    backup_mgr = VaultBackupManager(store)
    archive_path = tmp_path / "vault-backup.tar.gz"
    bak_info = backup_mgr.create_backup(archive_path)
    assert bak_info["file_count"] >= 2
    assert tarfile.is_tarfile(archive_path)

    # Simulate accidental deletion of m1 and modification check on m2
    m1_file = tmp_path / m1.relative_path
    m1_file.unlink()
    assert store.get(m1.id) is None

    restore_info = backup_mgr.restore_backup(archive_path, overwrite=False)
    assert restore_info["restored"] == 1
    assert restore_info["skipped"] >= 1
    assert store.get(m1.id) is not None
    assert store.get(m2.id) is not None
