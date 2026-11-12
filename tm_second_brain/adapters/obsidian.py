"""Obsidian adapter: safe Markdown, YAML frontmatter, wikilinks, Bases, and Canvas."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..core.models import utc_now_iso
from ..memory.markdown_store import (
    atomic_write_text,
    extract_wikilinks,
    parse_memory_markdown,
)

_GENERIC_FM_RE = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$")


def _parse_generic_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse arbitrary YAML-like frontmatter without dropping unknown user keys."""
    m = _GENERIC_FM_RE.match(text)
    if not m:
        return {}, text
    raw_fm, body = m.group(1), m.group(2)
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw_fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key is not None:
            data[current_key].append(line[4:].strip().strip("\"'"))
            continue
        current_key = None
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v == "":
                data[k] = []
                current_key = k
            elif v == "[]":
                data[k] = []
            elif v == "true":
                data[k] = True
            elif v == "false":
                data[k] = False
            else:
                data[k] = v.strip("\"'")
    return data, body


def _dump_generic_frontmatter(data: dict[str, Any], body: str) -> str:
    if not data:
        return body
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            if not v:
                lines.append(f"{k}: []")
            else:
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {json.dumps(str(item), ensure_ascii=False)}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    lines.append("---")
    lines.append("")
    lines.append(body.lstrip("\r\n"))
    return "\n".join(lines)


class ObsidianAdapter:
    """Safe read/write adapter for Obsidian vaults (.md, .base, .canvas, wikilinks)."""

    def __init__(self, vault_root: Path | str) -> None:
        self.vault_root = Path(vault_root).resolve()
        self.backup_dir = self.vault_root / ".tm-brain" / "obsidian-backups"

    def _resolve_safe(self, rel_path: str | Path) -> Path:
        raw = Path(rel_path)
        if raw.is_absolute():
            raise ValueError(f"Absolute paths are not allowed: {rel_path}")
        target = (self.vault_root / raw).resolve()
        if target != self.vault_root and self.vault_root not in target.parents:
            raise ValueError(f"Path traversal blocked: {rel_path}")
        return target

    def _backup_if_exists(self, target: Path) -> Path | None:
        if not target.exists():
            return None
        rel = target.relative_to(self.vault_root).as_posix()
        ts = utc_now_iso().replace(":", "").replace("-", "")
        dest = self.backup_dir / ts / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(target.read_bytes())
        return dest

    def read_markdown(self, rel_path: str | Path) -> dict[str, Any]:
        """Read a Markdown note, returning frontmatter, body, and wikilinks."""
        target = self._resolve_safe(rel_path)
        text = target.read_text(encoding="utf-8")
        fm, body = _parse_generic_frontmatter(text)
        return {
            "path": target.relative_to(self.vault_root).as_posix(),
            "frontmatter": fm,
            "body": body,
            "wikilinks": extract_wikilinks(text),
        }

    def write_markdown(
        self,
        rel_path: str | Path,
        body: str,
        frontmatter: dict[str, Any] | None = None,
        *,
        backup_existing: bool = True,
    ) -> dict[str, Any]:
        """Safely write a Markdown note, backing up any existing file first."""
        target = self._resolve_safe(rel_path)
        backup_path: Path | None = None
        if target.exists() and backup_existing:
            backup_path = self._backup_if_exists(target)
        merged_fm = dict(frontmatter or {})
        content = _dump_generic_frontmatter(merged_fm, body)
        atomic_write_text(target, content)
        return {
            "path": target.relative_to(self.vault_root).as_posix(),
            "backup": str(backup_path) if backup_path else None,
        }

    def read_canvas(self, rel_path: str | Path) -> dict[str, Any]:
        """Read and validate an Obsidian JSON Canvas (.canvas) file."""
        target = self._resolve_safe(rel_path)
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
            raise ValueError(f"Invalid JSON Canvas structure in {rel_path}")
        return data

    def write_canvas(
        self, rel_path: str | Path, canvas_data: dict[str, Any], *, backup_existing: bool = True
    ) -> dict[str, Any]:
        """Safely write an Obsidian JSON Canvas (.canvas) file with backup."""
        if "nodes" not in canvas_data or "edges" not in canvas_data:
            raise ValueError("JSON Canvas must contain 'nodes' and 'edges' keys")
        target = self._resolve_safe(rel_path)
        backup_path = self._backup_if_exists(target) if target.exists() and backup_existing else None
        atomic_write_text(target, json.dumps(canvas_data, indent=2, ensure_ascii=False) + "\n")
        return {"path": target.relative_to(self.vault_root).as_posix(), "backup": str(backup_path) if backup_path else None}

    def read_base(self, rel_path: str | Path) -> str:
        """Read an Obsidian Bases (.base) file verbatim without altering its syntax."""
        target = self._resolve_safe(rel_path)
        return target.read_text(encoding="utf-8")

    def list_special_files(self) -> dict[str, list[str]]:
        """List preserved .base and .canvas files in the vault."""
        bases: list[str] = []
        canvases: list[str] = []
        for path in sorted(self.vault_root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.vault_root).as_posix()
            if rel.startswith((".git/", ".tm-brain/", ".obsidian/")):
                continue
            if path.suffix == ".base":
                bases.append(rel)
            elif path.suffix == ".canvas":
                canvases.append(rel)
        return {"bases": bases, "canvases": canvases}

    def scan_wikilinks(self) -> dict[str, list[str]]:
        """Return mapping of note relative path -> outgoing wikilinks."""
        graph: dict[str, list[str]] = {}
        for md in sorted(self.vault_root.rglob("*.md")):
            rel = md.relative_to(self.vault_root).as_posix()
            if rel.startswith((".git/", ".tm-brain/", ".obsidian/")):
                continue
            text = md.read_text(encoding="utf-8", errors="replace")
            graph[rel] = extract_wikilinks(text)
        return graph

    def is_memory_note(self, rel_path: str | Path) -> bool:
        """Check whether a Markdown note conforms to TM memory frontmatter."""
        target = self._resolve_safe(rel_path)
        try:
            parse_memory_markdown(target.read_text(encoding="utf-8"), str(rel_path))
            return True
        except Exception:
            return False
