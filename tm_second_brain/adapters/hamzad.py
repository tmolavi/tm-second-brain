"""Non-duplicating bridge to Hamzad MemoryService / molavi-agentic-os MemoryInterface."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol, runtime_checkable

from ..core.models import ConfidenceLevel, MemoryScope
from ..memory.markdown_store import MarkdownMemoryStore


@runtime_checkable
class ExternalMemoryService(Protocol):
    """Duck-typed contract matching molavi-agentic-os MemoryInterface / Hamzad MemoryService."""

    def store_episode(self, session_id: str, agent_id: str, entry: dict[str, Any]) -> None: ...

    def get_episodes(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]: ...

    def set_key(self, namespace: str, key: str, value: Any) -> None: ...

    def get_key(self, namespace: str, key: str) -> Any | None: ...


class HamzadBridge:
    """Synchronizes episodes and memories with Hamzad MemoryService without duplicating storage."""

    def __init__(self, store: MarkdownMemoryStore, service: ExternalMemoryService) -> None:
        self.store = store
        self.service = service

    def _episode_ref_tag(self, session_id: str, agent_id: str, entry: dict[str, Any]) -> str:
        canonical = json.dumps({"session": session_id, "agent": agent_id, "entry": entry}, sort_keys=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        return f"hamzad-ref:{digest}"

    def sync_episodes_to_vault(
        self,
        session_id: str,
        *,
        project: str,
        limit: int = 20,
        supersede_conflicts: bool = False,
    ) -> dict[str, int]:
        """Idempotently sync episodes from Hamzad MemoryService into the Markdown vault."""
        episodes = self.service.get_episodes(session_id, limit=limit)
        existing_records = self.store.recall(project=project, include_private=True, limit=1000)
        existing_refs = {tag for r in existing_records for tag in r.tags if tag.startswith("hamzad-ref:")}

        synced = 0
        skipped = 0
        conflicts_detected = 0

        for ep in episodes:
            agent_id = str(ep.get("agent_id", "hamzad"))
            entry = ep.get("entry") or {}
            ref_tag = self._episode_ref_tag(session_id, agent_id, entry)
            if ref_tag in existing_refs:
                skipped += 1
                continue

            title = str(entry.get("title") or f"Hamzad episode ({session_id})")
            raw_body = str(entry.get("content") or json.dumps(entry, ensure_ascii=False))
            safe_body = self.store.privacy.redact(raw_body)

            write_res = self.store.remember(
                title,
                safe_body,
                scope=MemoryScope.PROJECT,
                projects=[project],
                confidence=ConfidenceLevel.INFERRED,
                source_agent=f"hamzad:{agent_id}",
                origin=f"hamzad-session:{session_id}",
                tags=["hamzad-sync", ref_tag],
            )
            if write_res.conflicts:
                conflicts_detected += len(write_res.conflicts)
                if supersede_conflicts:
                    target_id = write_res.conflicts[0].existing_id
                    self.store.correct(
                        target_id,
                        title,
                        safe_body,
                        reason=f"Superseded by Hamzad sync ({session_id})",
                        confidence=ConfidenceLevel.INFERRED,
                        source_agent=f"hamzad:{agent_id}",
                    )
            existing_refs.add(ref_tag)
            synced += 1

        return {"synced": synced, "skipped": skipped, "conflicts": conflicts_detected}

    def recall_for_session(self, project: str, limit: int = 10) -> list[dict[str, Any]]:
        """Expose non-private, project-isolated vault memories to Hamzad without mutating prod DB."""
        records = self.store.recall(project=project, include_private=False, limit=limit)
        return [
            {
                "id": r.id,
                "title": r.title,
                "content": self.store.privacy.redact(r.body),
                "confidence": r.confidence.value,
                "scope": r.scope.value,
                "tags": r.tags,
            }
            for r in records
        ]

    def push_memory_to_hamzad_kv(self, namespace: str, memory_id: str) -> bool:
        """Push a single non-private vault memory into Hamzad KV store."""
        rec = self.store.get(memory_id, include_private=False)
        if rec is None:
            return False
        self.service.set_key(
            namespace,
            rec.id,
            {
                "title": rec.title,
                "body": self.store.privacy.redact(rec.body),
                "confidence": rec.confidence.value,
                "version": rec.version,
            },
        )
        return True

    def record_orchestration_event(
        self,
        session_id: str,
        agent_id: str,
        task_name: str,
        outcome: dict[str, Any],
    ) -> None:
        """Record an orchestration event from Hamzad into vault with provenance and privacy redaction."""
        safe_outcome = self.store.privacy.redact(json.dumps(outcome, ensure_ascii=False))
        self.store.remember(
            f"Hamzad Orchestration: {task_name}",
            safe_outcome,
            scope=MemoryScope.PROJECT,
            projects=["hamzad-core"],
            confidence=ConfidenceLevel.INFERRED,
            source_agent=f"hamzad:{agent_id}",
            origin=f"hamzad-orchestration:{session_id}",
            tags=["hamzad-sync", "orchestration", f"session:{session_id}"],
        )

