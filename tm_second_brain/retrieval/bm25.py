"""Zero-dependency offline BM25 retrieval backend."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Sequence

from ..core.contracts import PrivacyPolicy
from ..core.models import (
    LifecycleStatus,
    MemoryRecord,
    MemoryScope,
    SearchQuery,
    SearchResult,
)
from ..privacy.policy import DefaultPrivacyPolicy

_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-\u0600-\u06FF]+")


def tokenize(text: str) -> list[str]:
    """Tokenize Unicode/ASCII text into lowercase terms."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def matches_filters(
    record: MemoryRecord,
    *,
    project: str | None = None,
    platforms: list[str] | None = None,
    scopes: list[MemoryScope] | None = None,
    include_superseded: bool = False,
    include_private: bool = False,
    privacy: PrivacyPolicy | None = None,
) -> bool:
    """Shared filter enforcing lifecycle, privacy, and project-scoped isolation."""
    policy = privacy or DefaultPrivacyPolicy()
    if not include_private and policy.is_private(record):
        return False
    if record.status == LifecycleStatus.ARCHIVED:
        return False
    if not include_superseded and record.status == LifecycleStatus.SUPERSEDED:
        return False
    if scopes and record.scope not in scopes:
        return False
    if project is not None and record.scope == MemoryScope.PROJECT:
        if project not in record.projects:
            return False
    if platforms:
        if record.scope == MemoryScope.PLATFORM and record.platforms:
            if not set(platforms).intersection(record.platforms):
                return False
    return True


class BM25RetrievalBackend:
    """Pure-Python offline BM25Okapi retrieval backend ($0.00 cost)."""

    def __init__(self, privacy: PrivacyPolicy | None = None) -> None:
        self._privacy = privacy or DefaultPrivacyPolicy()
        self._records: list[MemoryRecord] = []
        self._doc_tokens: list[list[str]] = []
        self._doc_freqs: Counter[str] = Counter()
        self._avgdl: float = 0.0

    @property
    def name(self) -> str:
        return "bm25"

    def index(self, records: Sequence[MemoryRecord]) -> None:
        """Index memory records in memory."""
        self._records = list(records)
        self._doc_tokens = []
        self._doc_freqs = Counter()

        for rec in self._records:
            combined = f"{rec.title} {' '.join(rec.tags)} {rec.body}"
            tokens = tokenize(combined)
            self._doc_tokens.append(tokens)
            for term in set(tokens):
                self._doc_freqs[term] += 1

        total_len = sum(len(t) for t in self._doc_tokens)
        self._avgdl = (total_len / len(self._doc_tokens)) if self._doc_tokens else 1.0

    def query(self, query: SearchQuery) -> list[SearchResult]:
        """Score and return matching records ordered by BM25 relevance."""
        q_terms = tokenize(query.text)
        if not q_terms or not self._records:
            return []

        n_docs = len(self._records)
        k1 = 1.5
        b = 0.75
        results: list[SearchResult] = []

        for rec, doc_tokens in zip(self._records, self._doc_tokens):
            if not matches_filters(
                rec,
                project=query.project,
                platforms=query.platforms,
                scopes=query.scopes,
                include_superseded=query.include_superseded,
                include_private=query.include_private,
                privacy=self._privacy,
            ):
                continue

            tf = Counter(doc_tokens)
            dl = len(doc_tokens) or 1
            score = 0.0
            matched: list[str] = []

            for term in q_terms:
                if term not in tf:
                    continue
                matched.append(term)
                df = self._doc_freqs.get(term, 0)
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                freq = tf[term]
                denom = freq + k1 * (1.0 - b + b * (dl / self._avgdl))
                score += idf * ((freq * (k1 + 1.0)) / denom)

            if score > 0.0:
                results.append(
                    SearchResult(
                        record=rec,
                        score=round(score, 6),
                        matched_terms=sorted(set(matched)),
                        backend=self.name,
                    )
                )

        results.sort(key=lambda r: (-r.score, r.record.provenance.updated_at), reverse=False)
        return results[: query.limit]
