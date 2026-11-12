"""Governance, license, and 5-language documentation verification tests."""

from __future__ import annotations

from pathlib import Path
from scripts.check_governance import run_checks


def test_governance_and_secret_scan() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    errors = run_checks(repo_root)
    assert errors == [], f"Governance errors: {errors}"
