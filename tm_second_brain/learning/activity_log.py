"""Cross-agent activity logging with secret redaction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.models import utc_now_iso
from ..privacy.policy import DefaultPrivacyPolicy


class ActivityLogger:
    """Logs agent actions to working-dir/agent-log/YYYY-MM.md and .tm-brain/activity.jsonl."""

    def __init__(self, vault_root: Path | str) -> None:
        self.vault_root = Path(vault_root).resolve()
        self.log_dir = self.vault_root / "working-dir" / "agent-log"
        self.jsonl_path = self.vault_root / ".tm-brain" / "activity.jsonl"
        self.privacy = DefaultPrivacyPolicy()

    def log_action(
        self,
        *,
        environment: str,
        agent_id: str,
        action: str,
        summary: str,
        project: str | None = None,
    ) -> dict[str, Any]:
        """Append a redacted activity entry to both Markdown and JSONL logs."""
        now = utc_now_iso()
        month = now[:7]
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        safe_summary = self.privacy.redact(summary.strip())
        md_file = self.log_dir / f"{month}.md"
        if not md_file.exists():
            md_file.write_text(f"# Agent Activity Log ({month})\n\n", encoding="utf-8")

        proj_part = f" [{project}]" if project else ""
        md_line = f"- `{now}` | `{environment}` | `{agent_id}` | **{action}**{proj_part}: {safe_summary}\n"
        with md_file.open("a", encoding="utf-8") as handle:
            handle.write(md_line)

        record = {
            "timestamp": now,
            "environment": environment,
            "agent_id": agent_id,
            "action": action,
            "project": project,
            "summary": safe_summary,
        }
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        return record
