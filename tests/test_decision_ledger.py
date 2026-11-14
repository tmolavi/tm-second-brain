"""Tests for Architecture Decision Record & Rejected Decision Ledger in TM Second Brain."""

import pytest
from pathlib import Path
from tm_second_brain.learning.decision_ledger import DecisionLedger, DecisionRecord

def test_decision_ledger_lifecycle(tmp_path: Path):
    ledger = DecisionLedger(tmp_path)
    
    # Record accepted decision
    accepted = ledger.record_decision(
        decision_id="ADR-001",
        title="Adopt Spec-Driven Development",
        status="ACCEPTED",
        context="Agents were writing code directly without verifiable boundary contracts.",
        decision="Enforce Spec-Driven Development gate before code modifications.",
        rationale="Eliminates hallucinations and scopes capabilities explicitly.",
        physical_evidence="100% test pass on mock capability contracts.",
        tags=["spec", "governance", "architecture"]
    )
    assert accepted.status == "ACCEPTED"
    assert accepted.decision_id == "ADR-001"

    # Record rejected decision
    rejected = ledger.reject_proposal(
        decision_id="ADR-002",
        title="Single Monolithic Agent Architecture",
        context="Proposal to merge reviewer, security, and developer agents into one prompt.",
        attempted_solution="Consolidate all roles into single 32k prompt.",
        rejection_reason="Adversarial separation lost; model failed to detect self-authored vulnerabilities.",
        physical_evidence="Eval suite showed 42% drop in security vulnerability detection.",
        tags=["personas", "review", "rejected"]
    )
    assert rejected.status == "REJECTED"
    assert rejected.rejection_reason is not None

    # Query
    all_recs = ledger.list_decisions()
    assert len(all_recs) == 2

    only_rejected = ledger.get_rejected()
    assert len(only_rejected) == 1
    assert only_rejected[0].decision_id == "ADR-002"

    # Check Markdown synchronization
    md_file = tmp_path / "Decisions" / "DECISION_LEDGER.md"
    assert md_file.exists()
    md_text = md_file.read_text(encoding="utf-8")
    assert "ADR-001" in md_text
    assert "ADR-002" in md_text
    assert "**REJECTED**" in md_text
