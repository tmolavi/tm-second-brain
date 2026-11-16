"""Durable session journal and state recovery for TM Agent Orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..memory.markdown_store import atomic_write_text
from .models import ExecutionRecord, OrchestrationTaskStatus, TaskUnit


class SessionJournal:
    """Persists and recovers multi-agent orchestration sessions."""

    def __init__(self, vault_root: Path) -> None:
        self.vault_root = Path(vault_root)
        self.sessions_dir = self.vault_root / ".tm-brain" / "orchestration_sessions"

    def ensure_storage(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def save_session(
        self,
        session_id: str,
        tasks: list[TaskUnit],
        *,
        metadata: dict[str, Any] | None = None,
        records: list[ExecutionRecord] | None = None,
    ) -> Path:
        """Persist session state to a durable JSON file."""
        self.ensure_storage()
        file_path = self._session_file(session_id)
        payload = {
            "session_id": session_id,
            "metadata": metadata or {},
            "tasks": [t.to_dict() for t in tasks],
            "records": [r.to_dict() for r in records or []],
        }
        atomic_write_text(file_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return file_path

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        """Load session state from disk if it exists."""
        file_path = self._session_file(session_id)
        if not file_path.is_file():
            return None
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all persisted sessions with high-level summaries."""
        if not self.sessions_dir.is_dir():
            return []
        summaries = []
        for p in sorted(self.sessions_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                tasks = data.get("tasks", [])
                completed = sum(1 for t in tasks if t.get("status") == OrchestrationTaskStatus.COMPLETED.value)
                summaries.append({
                    "session_id": data.get("session_id", p.stem),
                    "total_tasks": len(tasks),
                    "completed_tasks": completed,
                    "metadata": data.get("metadata", {}),
                    "path": str(p),
                })
            except Exception:
                continue
        return summaries

    def get_resumable_state(self, session_id: str) -> tuple[dict[str, TaskUnit], list[TaskUnit]]:
        """Load session and separate completed tasks from uncompleted/interrupted tasks.

        Returns:
            (completed_tasks_map, tasks_to_resume)
        """
        data = self.load_session(session_id)
        if not data:
            raise KeyError(f"Session '{session_id}' not found in journal.")

        completed_map: dict[str, TaskUnit] = {}
        pending_list: list[TaskUnit] = []

        for raw in data.get("tasks", []):
            task = TaskUnit.from_dict(raw)
            if task.status == OrchestrationTaskStatus.COMPLETED:
                completed_map[task.task_id] = task
            else:
                # Mark failed or running tasks as pending for re-execution
                if task.status in (OrchestrationTaskStatus.RUNNING, OrchestrationTaskStatus.FAILED):
                    task.status = OrchestrationTaskStatus.PENDING
                pending_list.append(task)

        return completed_map, pending_list
