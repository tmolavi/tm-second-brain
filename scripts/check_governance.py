#!/usr/bin/env python3
"""Governance, license, 5-language doc sync, and secret-scanning gate for tm-second-brain."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "SOURCES.md",
    "MODEL-REQUIREMENTS.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "pyproject.toml",
    "docs/en/GUIDE.md",
    "docs/fa/README.md",
    "docs/fa/GUIDE.md",
    "docs/tr/README.md",
    "docs/tr/GUIDE.md",
    "docs/az/README.md",
    "docs/az/GUIDE.md",
    "docs/ar/README.md",
    "docs/ar/GUIDE.md",
)

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def run_checks(repo_root: Path) -> list[str]:
    """Return a list of governance/security violations (empty if all pass)."""
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (repo_root / rel).is_file():
            errors.append(f"Missing required file: {rel}")

    license_text = (repo_root / "LICENSE").read_text(encoding="utf-8", errors="replace")
    if "MIT License" not in license_text:
        errors.append("LICENSE must be MIT License")

    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
    if "dependencies = []" not in pyproject:
        errors.append("pyproject.toml must keep core dependencies = []")

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith((".git/", ".pytest_cache/", "tests/", "tm_second_brain/privacy/")):
            continue
        if path.suffix in {".png", ".jpg", ".gif", ".gz", ".pyc"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pat in _SECRET_PATTERNS:
            if pat.search(text):
                errors.append(f"Potential secret detected in {rel}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = run_checks(root)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("PASS: All governance, license, 5-language doc, and secret checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
