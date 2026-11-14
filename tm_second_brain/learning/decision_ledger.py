"""Architecture Decision Record (ADR) and Rejected Decisions Ledger.

Inspired by addyosmani/agent-skills rejected ledgers and standard ADR patterns,
this module persists architectural choices, alternatives considered, physical
evidence, and explicit rejection rationales into persistent vault memory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..core.models import utc_now_iso
from ..memory.markdown_store import atomic_write_text


@dataclass
class DecisionRecord:
    """An architectural decision record with evidence and rejection rationale."""

    decision_id: str
    title: str
    status: str  # ACCEPTED | REJECTED | DEPRECATED | SUPERSEDED
    context: str
    decision: str
    rationale: str
    rejection_reason: str | None = None
    physical_evidence: str | None = None
    created_at: str = ""
    tags: list[str] | None = None


class DecisionLedger:
    """Manages persistent ADRs and Rejected Decisions in vault storage."""

    def __init__(self, vault_root: Path | str, *, ledger_file: str = "decision-ledger.json") -> None:
        self.vault_root = Path(vault_root).resolve()
        self.ledger_path = self.vault_root / ".tm-brain" / ledger_file
        self.docs_path = self.vault_root / "Decisions"

    def _load_data(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        try:
            return json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_data(self, records: list[dict[str, Any]]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.ledger_path, json.dumps(records, indent=2, ensure_ascii=False))

    def record_decision(
        self,
        decision_id: str,
        title: str,
        status: str,
        context: str,
        decision: str,
        rationale: str,
        rejection_reason: str | None = None,
        physical_evidence: str | None = None,
        tags: list[str] | None = None,
    ) -> DecisionRecord:
        records = self._load_data()
        rec = DecisionRecord(
            decision_id=decision_id,
            title=title,
            status=status.upper(),
            context=context,
            decision=decision,
            rationale=rationale,
            rejection_reason=rejection_reason,
            physical_evidence=physical_evidence,
            created_at=utc_now_iso(),
            tags=tags or [],
        )

        # Replace existing or append
        existing_idx = next((i for i, r in enumerate(records) if r.get("decision_id") == decision_id), None)
        rec_dict = asdict(rec)
        if existing_idx is not None:
            records[existing_idx] = rec_dict
        else:
            records.append(rec_dict)

        self._save_data(records)
        self.sync_to_markdown()
        return rec

    def reject_proposal(
        self,
        decision_id: str,
        title: str,
        context: str,
        attempted_solution: str,
        rejection_reason: str,
        physical_evidence: str,
        tags: list[str] | None = None,
    ) -> DecisionRecord:
        """Explicitly record a rejected decision with physical failure evidence."""
        return self.record_decision(
            decision_id=decision_id,
            title=title,
            status="REJECTED",
            context=context,
            decision=attempted_solution,
            rationale="Rejected under physical evidence & doubt-driven review.",
            rejection_reason=rejection_reason,
            physical_evidence=physical_evidence,
            tags=tags,
        )

    def list_decisions(self, status: str | None = None) -> list[DecisionRecord]:
        records = self._load_data()
        if status:
            records = [r for r in records if r.get("status") == status.upper()]
        return [
            DecisionRecord(
                decision_id=r["decision_id"],
                title=r["title"],
                status=r["status"],
                context=r["context"],
                decision=r["decision"],
                rationale=r["rationale"],
                rejection_reason=r.get("rejection_reason"),
                physical_evidence=r.get("physical_evidence"),
                created_at=r.get("created_at", ""),
                tags=r.get("tags", []),
            )
            for r in records
        ]

    def get_rejected(self) -> list[DecisionRecord]:
        return self.list_decisions(status="REJECTED")

    def sync_to_markdown(self) -> None:
        """Generate human-readable Decisions/DECISION_LEDGER.md."""
        self.docs_path.mkdir(parents=True, exist_ok=True)
        md_file = self.docs_path / "DECISION_LEDGER.md"
        records = self.list_decisions()

        lines = [
            "# Architecture Decision Record (ADR) & Rejected Proposals Ledger",
            "",
            "Persistent audit trail of accepted and rejected technical choices.",
            "",
            "| ID | Title | Status | Rationale / Rejection Reason | Evidence |",
            "|:---|:---|:---:|:---|:---|",
        ]

        for r in records:
            reason = r.rejection_reason if r.status == "REJECTED" else r.rationale
            lines.append(f"| `{r.decision_id}` | {r.title} | **{r.status}** | {reason} | {r.physical_evidence or 'N/A'} |")

        lines.append("")
        atomic_write_text(md_file, "\n".join(lines))
