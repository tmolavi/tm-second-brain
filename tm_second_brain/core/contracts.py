"""Abstract interfaces and integration contracts for TM Second Brain."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, Sequence, runtime_checkable

from .models import (
    ConfidenceLevel,
    MemoryRecord,
    MemoryScope,
    MemoryWriteResult,
    SearchQuery,
    SearchResult,
)


@runtime_checkable
class PrivacyPolicy(Protocol):
    """Enforces private-data exclusion and secret/PII redaction."""

    def is_private(self, record: MemoryRecord) -> bool: ...

    def redact(self, text: str) -> str: ...


@runtime_checkable
class RetrievalBackend(Protocol):
    """Pluggable, model-independent retrieval backend."""

    @property
    def name(self) -> str: ...

    def index(self, records: Sequence[MemoryRecord]) -> None: ...

    def query(self, query: SearchQuery) -> list[SearchResult]: ...


@runtime_checkable
class MemoryAPI(Protocol):
    """Stable, model-independent Second Brain memory contract."""

    def remember(
        self,
        title: str,
        body: str,
        *,
        scope: MemoryScope = MemoryScope.PROJECT,
        projects: list[str] | None = None,
        platforms: list[str] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED,
        verification: str | None = None,
        source_agent: str = "human",
        origin: str = "cli",
        private: bool = False,
        tags: list[str] | None = None,
    ) -> MemoryWriteResult: ...

    def recall(
        self,
        *,
        project: str | None = None,
        platforms: list[str] | None = None,
        include_private: bool = False,
        limit: int = 20,
    ) -> list[MemoryRecord]: ...

    def search(self, query: SearchQuery) -> list[SearchResult]: ...

    def get(self, memory_id: str, *, include_private: bool = False) -> MemoryRecord | None: ...

    def expand(
        self, memory_id: str, *, depth: int = 1, include_private: bool = False
    ) -> dict[str, Any]: ...

    def correct(
        self,
        target_id: str,
        new_title: str,
        new_body: str,
        *,
        reason: str,
        confidence: ConfidenceLevel = ConfidenceLevel.VERIFIED,
        verification: str | None = None,
        source_agent: str = "human",
    ) -> MemoryWriteResult: ...

    def archive(self, memory_id: str, *, reason: str = "") -> MemoryRecord: ...

    def health(self) -> dict[str, Any]: ...


@runtime_checkable
class BackupManager(Protocol):
    """Safe import/export and backup/restore contract."""

    def export_bundle(
        self, out_path: Path, *, include_private: bool = False
    ) -> dict[str, Any]: ...

    def import_bundle(
        self, bundle_path: Path, *, overwrite: bool = False
    ) -> dict[str, Any]: ...

    def create_backup(self, archive_path: Path) -> dict[str, Any]: ...

    def restore_backup(
        self, archive_path: Path, *, overwrite: bool = False
    ) -> dict[str, Any]: ...


@runtime_checkable
class HarnessAdapter(Protocol):
    """Contract for agent harness adapters (Claude, Codex, Gemini, OpenCode, Goose, Antigravity, Hermes)."""

    @property
    def harness_name(self) -> str: ...

    def render_instructions(self, vault_root: Path) -> str: ...

    def export_skill(self, skill_name: str, skill_markdown: str, out_dir: Path) -> Path: ...

    def build_mcp_config(self, vault_root: Path) -> dict[str, Any]: ...


@runtime_checkable
class HamzadMemoryBridge(Protocol):
    """Non-duplicating bridge to molavi-agentic-os MemoryInterface / Hamzad MemoryService."""

    def sync_episodes_to_vault(self, session_id: str, *, project: str) -> int: ...

    def recall_for_session(self, project: str, limit: int = 10) -> list[dict[str, Any]]: ...
