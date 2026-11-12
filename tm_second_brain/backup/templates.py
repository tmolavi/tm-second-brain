"""Starter vault template installer (never overwrites existing user files)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

VALID_TEMPLATES = ("personal-knowledge", "business-project", "developer-agent")


def _default_templates_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "vault-template"


def install_starter_template(
    vault_root: Path | str,
    template_name: str,
    *,
    templates_root: Path | None = None,
) -> dict[str, Any]:
    """Copy a starter vault template into vault_root without overwriting existing files."""
    if template_name not in VALID_TEMPLATES:
        raise ValueError(f"Unknown template '{template_name}'. Choose from: {', '.join(VALID_TEMPLATES)}")

    src_root = (templates_root or _default_templates_root()) / template_name
    if not src_root.is_dir():
        raise FileNotFoundError(f"Template directory not found: {src_root}")

    dest_root = Path(vault_root).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    skipped = 0

    for src_file in sorted(src_root.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(src_root)
        dest_file = (dest_root / rel).resolve()
        if dest_root not in dest_file.parents:
            raise ValueError(f"Unsafe template path: {rel}")
        if dest_file.exists():
            skipped += 1
            continue
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
        copied += 1

    return {"template": template_name, "copied": copied, "skipped": skipped}
