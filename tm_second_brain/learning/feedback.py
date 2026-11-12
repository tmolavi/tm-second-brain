"""Feedback pattern detection and L1 Draft -> L2 User-Approved skill learning."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..core.models import utc_now_iso
from ..memory.markdown_store import atomic_write_text
from ..privacy.policy import DefaultPrivacyPolicy

_RULE_RE = re.compile(r"\*\*Proposed rule change:\*\*\s*(.+)", re.IGNORECASE)
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*(\w+)", re.IGNORECASE)


@dataclass
class LearningProposal:
    """L1 Draft proposal awaiting explicit L2 human approval."""

    proposal_id: str
    skill_name: str
    proposed_rule: str
    occurrences: int
    status: str = "l1_draft"  # l1_draft | l2_approved | rejected
    created_at: str = ""
    approved_by: str | None = None
    approved_at: str | None = None


class FeedbackManager:
    """Manages FEEDBACK.md logs, pattern detection, and L2-approved SKILL.md promotions."""

    def __init__(self, vault_root: Path | str, *, skills_dir: str = "Skills") -> None:
        self.vault_root = Path(vault_root).resolve()
        self.skills_path = self.vault_root / skills_dir
        self.proposals_file = self.vault_root / ".tm-brain" / "learning-proposals.json"
        self.privacy = DefaultPrivacyPolicy()

    def log_feedback(
        self,
        skill_name: str,
        outcome: str,
        *,
        correction: str = "",
        proposed_rule: str = "none",
    ) -> Path:
        """Append a structured feedback entry to Skills/<skill>/FEEDBACK.md."""
        skill_dir = self.skills_path / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        fb_path = skill_dir / "FEEDBACK.md"
        if not fb_path.exists():
            atomic_write_text(fb_path, f"# Feedback Log: {skill_name}\n\n")

        safe_outcome = self.privacy.redact(outcome.strip())
        safe_corr = self.privacy.redact(correction.strip())
        safe_rule = self.privacy.redact(proposed_rule.strip())
        date_str = utc_now_iso()[:10]
        entry = (
            f"### {date_str} — {safe_outcome}\n"
            f"- **Status:** open\n"
            f"- **Correction:** {safe_corr or 'none'}\n"
            f"- **Proposed rule change:** {safe_rule or 'none'}\n\n"
        )
        existing = fb_path.read_text(encoding="utf-8")
        atomic_write_text(fb_path, existing + entry)
        return fb_path

    def _load_proposals(self) -> list[LearningProposal]:
        if not self.proposals_file.exists():
            return []
        raw = json.loads(self.proposals_file.read_text(encoding="utf-8"))
        return [LearningProposal(**item) for item in raw]

    def _save_proposals(self, proposals: list[LearningProposal]) -> None:
        self.proposals_file.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(
            self.proposals_file,
            json.dumps([asdict(p) for p in proposals], indent=2, ensure_ascii=False) + "\n",
        )

    def scan_patterns(self, *, min_occurrences: int = 2) -> list[LearningProposal]:
        """Detect repeated open rule proposals (>= min_occurrences) and emit L1 drafts."""
        if not self.skills_path.exists():
            return []

        existing = {p.proposal_id: p for p in self._load_proposals()}
        new_drafts: list[LearningProposal] = []

        for skill_dir in sorted(p for p in self.skills_path.iterdir() if p.is_dir()):
            fb_path = skill_dir / "FEEDBACK.md"
            if not fb_path.exists():
                continue
            text = fb_path.read_text(encoding="utf-8", errors="replace")
            blocks = re.split(r"^### ", text, flags=re.MULTILINE)[1:]
            counts: dict[str, int] = {}
            for block in blocks:
                st_m = _STATUS_RE.search(block)
                if not st_m or st_m.group(1).lower() != "open":
                    continue
                rl_m = _RULE_RE.search(block)
                if not rl_m:
                    continue
                rule = rl_m.group(1).strip()
                if rule.lower() in ("none", "n/a", ""):
                    continue
                counts[rule] = counts.get(rule, 0) + 1

            for rule, count in counts.items():
                if count < min_occurrences:
                    continue
                pid = "prop_" + hashlib.sha256(f"{skill_dir.name}:{rule}".encode("utf-8")).hexdigest()[:10]
                if pid in existing:
                    continue
                prop = LearningProposal(
                    proposal_id=pid,
                    skill_name=skill_dir.name,
                    proposed_rule=rule,
                    occurrences=count,
                    status="l1_draft",
                    created_at=utc_now_iso(),
                )
                existing[pid] = prop
                new_drafts.append(prop)

        self._save_proposals(list(existing.values()))
        return new_drafts

    def approve_proposal(self, proposal_id: str, *, approver: str = "human") -> dict[str, Any]:
        """L2 Human Approval Gate: promote an L1 draft rule into SKILL.md."""
        proposals = self._load_proposals()
        target = next((p for p in proposals if p.proposal_id == proposal_id), None)
        if target is None:
            raise KeyError(f"Proposal not found: {proposal_id}")
        if target.status == "l2_approved":
            return {"proposal_id": proposal_id, "status": "already_approved"}

        skill_dir = self.skills_path / target.skill_name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            atomic_write_text(skill_md, f"# {target.skill_name}\n\n## Learned Rules\n")

        # Backup SKILL.md before mutating
        backup_dir = self.vault_root / ".tm-brain" / "skill-backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = utc_now_iso().replace(":", "").replace("-", "")
        (backup_dir / f"{target.skill_name}_{ts}_SKILL.md").write_text(
            skill_md.read_text(encoding="utf-8"), encoding="utf-8"
        )

        content = skill_md.read_text(encoding="utf-8")
        if "## Learned Rules" not in content:
            content = content.rstrip() + "\n\n## Learned Rules\n"
        content = content.rstrip() + f"\n- {target.proposed_rule} *(approved by {approver}, {utc_now_iso()[:10]})*\n"
        atomic_write_text(skill_md, content)

        # Mark matching open entries in FEEDBACK.md as promoted
        fb_path = skill_dir / "FEEDBACK.md"
        if fb_path.exists():
            fb_text = fb_path.read_text(encoding="utf-8")
            fb_text = fb_text.replace(
                f"- **Status:** open\n",
                "- **Status:** promoted\n",
            )
            atomic_write_text(fb_path, fb_text)

        target.status = "l2_approved"
        target.approved_by = approver
        target.approved_at = utc_now_iso()
        self._save_proposals(proposals)
        return {"proposal_id": proposal_id, "status": "l2_approved", "skill_md": str(skill_md)}
