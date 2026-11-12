"""Canonical data models for TM Second Brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class MemoryScope(str, Enum):
    GENERAL = "general"
    PLATFORM = "platform"
    PROJECT = "project"


class ConfidenceLevel(str, Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class Provenance:
    """Origin and verification metadata for a memory record."""

    source_agent: str = "human"
    origin: str = "cli"
    verification: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)


@dataclass
class MemoryRecord:
    """Canonical representation of a memory note."""

    id: str
    title: str
    body: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    scope: MemoryScope = MemoryScope.PROJECT
    projects: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    provenance: Provenance = field(default_factory=Provenance)
    version: int = 1
    supersedes: str | None = None
    superseded_by: str | None = None
    private: bool = False
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    relative_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize record to a JSON-safe dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "status": self.status.value,
            "scope": self.scope.value,
            "projects": list(self.projects),
            "platforms": list(self.platforms),
            "confidence": self.confidence.value,
            "provenance": {
                "source_agent": self.provenance.source_agent,
                "origin": self.provenance.origin,
                "verification": self.provenance.verification,
                "created_at": self.provenance.created_at,
                "updated_at": self.provenance.updated_at,
            },
            "version": self.version,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "private": self.private,
            "tags": list(self.tags),
            "links": list(self.links),
            "relative_path": self.relative_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryRecord:
        """Deserialize record from a dictionary."""
        prov_raw = data.get("provenance") or {}
        prov = Provenance(
            source_agent=str(prov_raw.get("source_agent", "human")),
            origin=str(prov_raw.get("origin", "cli")),
            verification=prov_raw.get("verification"),
            created_at=str(prov_raw.get("created_at") or utc_now_iso()),
            updated_at=str(prov_raw.get("updated_at") or utc_now_iso()),
        )
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            body=str(data.get("body", "")),
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
            relative_path=str(data.get("relative_path", "")),
        )


@dataclass(frozen=True)
class ConflictCandidate:
    """Potential conflict detected against an existing active memory."""

    existing_id: str
    title: str
    similarity: float
    reason: str


@dataclass
class MemoryWriteResult:
    """Result of writing or correcting a memory."""

    record: MemoryRecord
    conflicts: list[ConflictCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SearchQuery:
    """Model-independent search query."""

    text: str
    project: str | None = None
    platforms: list[str] | None = None
    scopes: list[MemoryScope] | None = None
    include_superseded: bool = False
    include_private: bool = False
    limit: int = 10


@dataclass
class SearchResult:
    """Ranked search result returned by a RetrievalBackend."""

    record: MemoryRecord
    score: float
    matched_terms: list[str] = field(default_factory=list)
    backend: str = "bm25"


@dataclass(frozen=True)
class CorrectionEvent:
    """Immutable audit record for a memory correction."""

    timestamp: str
    old_id: str
    new_id: str
    reason: str
    source_agent: str
