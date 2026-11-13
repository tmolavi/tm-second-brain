"""Markdown + YAML frontmatter memory store (canonical local-first storage)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any

from ..core.contracts import PrivacyPolicy, RetrievalBackend
from ..core.models import (
    ConfidenceLevel,
    ConflictCandidate,
    CorrectionEvent,
    LifecycleStatus,
    MemoryRecord,
    MemoryScope,
    MemoryWriteResult,
    Provenance,
    SearchQuery,
    SearchResult,
    utc_now_iso,
)
from ..privacy.policy import DefaultPrivacyPolicy
from ..retrieval.bm25 import BM25RetrievalBackend, matches_filters, tokenize

_WINDOWS_RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", re.IGNORECASE)
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
_SLUG_MAX = 60


def sanitize_slug(raw: str) -> str:
    """Produce a cross-platform, Windows-safe filename slug."""
    cleaned = raw.strip().lower()
    cleaned = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "-", cleaned)
    cleaned = cleaned.replace("..", "-")
    cleaned = re.sub(r"[^a-z0-9\u0600-\u06ff_-]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-.")
    if not cleaned:
        cleaned = "memory"
    cleaned = cleaned[:_SLUG_MAX].rstrip("-.")
    if _WINDOWS_RESERVED.match(cleaned):
        cleaned = f"mem-{cleaned}"
    return cleaned or "memory"


def extract_wikilinks(text: str) -> list[str]:
    """Extract unique Obsidian [[wikilink]] targets from Markdown text."""
    seen: list[str] = []
    for match in _WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        if target and target not in seen:
            seen.append(target)
    return seen


def atomic_write_text(path: Path, content: str) -> None:
    """Write UTF-8 text atomically via temp file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def serialize_memory_markdown(record: MemoryRecord) -> str:
    """Serialize a MemoryRecord to Markdown with YAML frontmatter."""
    lines = ["---"]
    lines.append(f"id: {_yaml_scalar(record.id)}")
    lines.append(f"title: {_yaml_scalar(record.title)}")
    lines.append(f"status: {_yaml_scalar(record.status.value)}")
    lines.append(f"version: {record.version}")
    lines.append(f"scope: {_yaml_scalar(record.scope.value)}")

    for list_key, values in (
        ("projects", record.projects),
        ("platforms", record.platforms),
        ("tags", record.tags),
        ("links", record.links),
    ):
        if not values:
            lines.append(f"{list_key}: []")
        else:
            lines.append(f"{list_key}:")
            for item in values:
                lines.append(f"  - {_yaml_scalar(item)}")

    lines.append(f"confidence: {_yaml_scalar(record.confidence.value)}")
    lines.append(f"verification: {_yaml_scalar(record.provenance.verification)}")
    lines.append(f"source_agent: {_yaml_scalar(record.provenance.source_agent)}")
    lines.append(f"origin: {_yaml_scalar(record.provenance.origin)}")
    lines.append(f"created_at: {_yaml_scalar(record.provenance.created_at)}")
    lines.append(f"updated_at: {_yaml_scalar(record.provenance.updated_at)}")
    lines.append(f"supersedes: {_yaml_scalar(record.supersedes)}")
    lines.append(f"superseded_by: {_yaml_scalar(record.superseded_by)}")
    lines.append(f"private: {_yaml_scalar(record.private)}")
    lines.append("---")
    lines.append("")
    lines.append(record.body.rstrip())
    lines.append("")
    return "\n".join(lines)


def _parse_yaml_scalar(raw: str) -> Any:
    val = raw.strip()
    if val in ("null", "~", ""):
        return None
    if val == "true":
        return True
    if val == "false":
        return False
    if val == "[]":
        return []
    if val.startswith('"') and val.endswith('"'):
        return json.loads(val)
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    return val


def parse_memory_markdown(text: str, relative_path: str = "") -> MemoryRecord:
    """Parse a Markdown note with YAML frontmatter into a MemoryRecord."""
    if not text.startswith("---"):
        raise ValueError("Missing YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("Malformed YAML frontmatter")

    fm_lines = parts[1].splitlines()
    body = parts[2].lstrip("\r\n").rstrip()
    data: dict[str, Any] = {}
    current_list_key: str | None = None

    for line in fm_lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list_key is not None:
            data[current_list_key].append(_parse_yaml_scalar(line[4:]))
            continue
        current_list_key = None
        if ":" in line:
            key, raw_val = line.split(":", 1)
            key = key.strip()
            raw_val = raw_val.strip()
            if raw_val == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = _parse_yaml_scalar(raw_val)

    prov = Provenance(
        source_agent=str(data.get("source_agent") or "human"),
        origin=str(data.get("origin") or "cli"),
        verification=data.get("verification"),
        created_at=str(data.get("created_at") or utc_now_iso()),
        updated_at=str(data.get("updated_at") or utc_now_iso()),
    )
    return MemoryRecord(
        id=str(data["id"]),
        title=str(data["title"]),
        body=body,
        status=LifecycleStatus(data.get("status", LifecycleStatus.ACTIVE.value)),
        scope=MemoryScope(data.get("scope", MemoryScope.PROJECT.value)),
        projects=list(data.get("projects") or []),
        platforms=list(data.get("platforms") or []),
        confidence=ConfidenceLevel(data.get("confidence", ConfidenceLevel.UNVERIFIED.value)),
        provenance=prov,
        version=int(data.get("version", 1)),
        supersedes=data.get("supersedes"),
        superseded_by=data.get("superseded_by"),
        private=bool(data.get("private", False)),
        tags=list(data.get("tags") or []),
        links=list(data.get("links") or []),
        relative_path=relative_path,
    )


class MarkdownMemoryStore:
    """Canonical Markdown-backed implementation of MemoryAPI."""

    def __init__(
        self,
        vault_root: Path | str,
        *,
        retrieval_backend: RetrievalBackend | None = None,
        privacy_policy: PrivacyPolicy | None = None,
    ) -> None:
        self.vault_root = Path(vault_root).resolve()
        self.memories_dir = self.vault_root / "memories"
        self.meta_dir = self.vault_root / ".tm-brain"
        self.corrections_log = self.meta_dir / "corrections.jsonl"
        self.privacy: PrivacyPolicy = privacy_policy or DefaultPrivacyPolicy()
        self._backend: RetrievalBackend = retrieval_backend or BM25RetrievalBackend(self.privacy)
        self.ensure_layout()

    def ensure_layout(self) -> None:
        """Create required vault directories without overwriting existing user files."""
        for sub in ("general", "platform", "projects", "private"):
            (self.memories_dir / sub).mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def set_retrieval_backend(self, backend: RetrievalBackend) -> None:
        """Hot-swap the retrieval backend at runtime (model-switching guarantee)."""
        self._backend = backend

    def _new_id(self, title: str) -> str:
        date_part = utc_now_iso()[:10].replace("-", "")
        digest = hashlib.sha256(f"{title}:{uuid.uuid4().hex}".encode("utf-8")).hexdigest()[:12]
        return f"mem_{date_part}_{digest}"

    def _target_path(self, record: MemoryRecord) -> Path:
        slug = sanitize_slug(record.title)
        filename = f"{record.id}__{slug}.md"
        if record.private:
            rel = Path("memories") / "private" / filename
        elif record.scope == MemoryScope.PROJECT:
            proj = sanitize_slug(record.projects[0]) if record.projects else "default"
            rel = Path("memories") / "projects" / proj / filename
        elif record.scope == MemoryScope.PLATFORM:
            rel = Path("memories") / "platform" / filename
        else:
            rel = Path("memories") / "general" / filename

        target = (self.vault_root / rel).resolve()
        if self.vault_root not in target.parents:
            raise ValueError("Path traversal detected")
        return target

    def _load_all_records(self) -> list[MemoryRecord]:
        records: list[MemoryRecord] = []
        if not self.memories_dir.exists():
            return records
        for md_file in sorted(self.memories_dir.rglob("*.md")):
            rel = md_file.relative_to(self.vault_root).as_posix()
            try:
                rec = parse_memory_markdown(md_file.read_text(encoding="utf-8"), relative_path=rel)
                records.append(rec)
            except Exception:
                continue
        return records

    def _detect_conflicts(
        self, title: str, scope: MemoryScope, projects: list[str]
    ) -> list[ConflictCandidate]:
        new_tokens = set(tokenize(title))
        if not new_tokens:
            return []
        conflicts: list[ConflictCandidate] = []
        for existing in self._load_all_records():
            if existing.status != LifecycleStatus.ACTIVE or existing.scope != scope:
                continue
            if scope == MemoryScope.PROJECT and not set(projects).intersection(existing.projects):
                continue
            old_tokens = set(tokenize(existing.title))
            if not old_tokens:
                continue
            jaccard = len(new_tokens & old_tokens) / len(new_tokens | old_tokens)
            if jaccard >= 0.55:
                conflicts.append(
                    ConflictCandidate(
                        existing_id=existing.id,
                        title=existing.title,
                        similarity=round(jaccard, 3),
                        reason="High title/topic overlap in same scope",
                    )
                )
        return conflicts

    def _write_record(self, record: MemoryRecord, path: Path | None = None) -> MemoryRecord:
        if self.privacy:
            record.title = self.privacy.redact(record.title)
            record.body = self.privacy.redact(record.body)
        target = path or (
            self.vault_root / record.relative_path
            if record.relative_path
            else self._target_path(record)
        )
        record.relative_path = target.relative_to(self.vault_root).as_posix()
        atomic_write_text(target, serialize_memory_markdown(record))
        return record

    def remember(
        self,
        title: str,
        body: str,
        *,
        scope: MemoryScope = MemoryScope.PROJECT,
        projects: list[str] | None = None,
        platforms: list[str] | None = None,
        confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED,
        verification: str | None = None,
        source_agent: str = "human",
        origin: str = "cli",
        private: bool = False,
        tags: list[str] | None = None,
    ) -> MemoryWriteResult:
        proj_list = list(projects or [])
        plat_list = list(platforms or [])
        warnings: list[str] = []

        if scope == MemoryScope.PROJECT and not proj_list:
            proj_list = ["default"]
            warnings.append("Project scope without projects list; defaulted to ['default'].")
        if confidence == ConfidenceLevel.VERIFIED and not verification:
            confidence = ConfidenceLevel.INFERRED
            warnings.append("Downgraded confidence from verified to inferred (no verification given).")

        conflicts = self._detect_conflicts(title, scope, proj_list)
        now = utc_now_iso()
        record = MemoryRecord(
            id=self._new_id(title),
            title=title.strip(),
            body=body.strip(),
            status=LifecycleStatus.ACTIVE,
            scope=scope,
            projects=proj_list,
            platforms=plat_list,
            confidence=confidence,
            provenance=Provenance(
                source_agent=source_agent,
                origin=origin,
                verification=verification,
                created_at=now,
                updated_at=now,
            ),
            version=1,
            private=private,
            tags=list(tags or []),
            links=extract_wikilinks(body),
        )
        self._write_record(record)
        return MemoryWriteResult(record=record, conflicts=conflicts, warnings=warnings)

    def recall(
        self,
        *,
        project: str | None = None,
        platforms: list[str] | None = None,
        include_private: bool = False,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        filtered = [
            rec
            for rec in self._load_all_records()
            if matches_filters(
                rec,
                project=project,
                platforms=platforms,
                include_private=include_private,
                privacy=self.privacy,
            )
        ]
        filtered.sort(key=lambda r: r.provenance.updated_at, reverse=True)
        return filtered[:limit]

    def search(self, query: SearchQuery) -> list[SearchResult]:
        records = self._load_all_records()
        self._backend.index(records)
        return self._backend.query(query)

    def get(self, memory_id: str, *, include_private: bool = False) -> MemoryRecord | None:
        for rec in self._load_all_records():
            if rec.id == memory_id:
                if not include_private and self.privacy.is_private(rec):
                    return None
                return rec
        return None

    def expand(
        self, memory_id: str, *, depth: int = 1, include_private: bool = False
    ) -> dict[str, Any]:
        all_records = [
            r
            for r in self._load_all_records()
            if include_private or not self.privacy.is_private(r)
        ]
        by_id = {r.id: r for r in all_records}
        by_title = {r.title.lower(): r for r in all_records}
        root = by_id.get(memory_id)
        if root is None:
            return {"root": None, "neighbors": []}

        visited = {root.id}
        frontier = [root]
        neighbors: list[MemoryRecord] = []

        for _ in range(max(1, depth)):
            next_frontier: list[MemoryRecord] = []
            for node in frontier:
                for link in node.links:
                    target = by_id.get(link) or by_title.get(link.lower())
                    if target and target.id not in visited:
                        visited.add(target.id)
                        neighbors.append(target)
                        next_frontier.append(target)
                for candidate in all_records:
                    if candidate.id in visited:
                        continue
                    if node.id in candidate.links or node.title in candidate.links:
                        visited.add(candidate.id)
                        neighbors.append(candidate)
                        next_frontier.append(candidate)
            frontier = next_frontier

        return {"root": root, "neighbors": neighbors}

    def correct(
        self,
        target_id: str,
        new_title: str,
        new_body: str,
        *,
        reason: str,
        confidence: ConfidenceLevel = ConfidenceLevel.VERIFIED,
        verification: str | None = None,
        source_agent: str = "human",
    ) -> MemoryWriteResult:
        old = self.get(target_id, include_private=True)
        if old is None:
            raise KeyError(f"Memory not found: {target_id}")

        now = utc_now_iso()
        new_record = MemoryRecord(
            id=self._new_id(new_title),
            title=new_title.strip(),
            body=new_body.strip(),
            status=LifecycleStatus.ACTIVE,
            scope=old.scope,
            projects=list(old.projects),
            platforms=list(old.platforms),
            confidence=confidence,
            provenance=Provenance(
                source_agent=source_agent,
                origin=old.provenance.origin,
                verification=verification,
                created_at=now,
                updated_at=now,
            ),
            version=old.version + 1,
            supersedes=old.id,
            private=old.private,
            tags=list(old.tags),
            links=extract_wikilinks(new_body),
        )
        self._write_record(new_record)

        old.status = LifecycleStatus.SUPERSEDED
        old.superseded_by = new_record.id
        old.provenance = Provenance(
            source_agent=old.provenance.source_agent,
            origin=old.provenance.origin,
            verification=old.provenance.verification,
            created_at=old.provenance.created_at,
            updated_at=now,
        )
        self._write_record(old, path=self.vault_root / old.relative_path)

        safe_reason = self.privacy.redact(reason) if self.privacy else reason
        event = CorrectionEvent(
            timestamp=now,
            old_id=old.id,
            new_id=new_record.id,
            reason=safe_reason,
            source_agent=source_agent,
        )
        with self.corrections_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.__dict__, ensure_ascii=False) + "\n")

        return MemoryWriteResult(record=new_record)

    def archive(self, memory_id: str, *, reason: str = "") -> MemoryRecord:
        rec = self.get(memory_id, include_private=True)
        if rec is None:
            raise KeyError(f"Memory not found: {memory_id}")
        rec.status = LifecycleStatus.ARCHIVED
        rec.provenance = Provenance(
            source_agent=rec.provenance.source_agent,
            origin=rec.provenance.origin,
            verification=rec.provenance.verification or (reason or None),
            created_at=rec.provenance.created_at,
            updated_at=utc_now_iso(),
        )
        return self._write_record(rec, path=self.vault_root / rec.relative_path)

    def health(self) -> dict[str, Any]:
        records = self._load_all_records()
        return {
            "vault_root": str(self.vault_root),
            "backend": self._backend.name,
            "total_memories": len(records),
            "active_memories": sum(1 for r in records if r.status == LifecycleStatus.ACTIVE),
            "superseded_memories": sum(1 for r in records if r.status == LifecycleStatus.SUPERSEDED),
            "private_memories": sum(1 for r in records if self.privacy.is_private(r)),
            "offline_ready": True,
        }
