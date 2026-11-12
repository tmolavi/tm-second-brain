"""Hybrid retrieval combining BM25/FTS5, wikilink graph boost, and optional semantic backends."""

from __future__ import annotations

from typing import Sequence

from ..core.contracts import PrivacyPolicy, RetrievalBackend
from ..core.models import MemoryRecord, SearchQuery, SearchResult
from ..privacy.policy import DefaultPrivacyPolicy
from .bm25 import BM25RetrievalBackend


class HybridRetrievalBackend:
    """Combines lexical BM25, wikilink graph centrality, and optional semantic backends."""

    def __init__(
        self,
        *,
        lexical: RetrievalBackend | None = None,
        semantic: RetrievalBackend | None = None,
        privacy: PrivacyPolicy | None = None,
    ) -> None:
        self._privacy = privacy or DefaultPrivacyPolicy()
        self._lexical: RetrievalBackend = lexical or BM25RetrievalBackend(self._privacy)
        self._semantic: RetrievalBackend | None = semantic
        self._in_degree: dict[str, int] = {}

    @property
    def name(self) -> str:
        if self._semantic is not None:
            return f"hybrid({self._lexical.name}+{self._semantic.name})"
        return f"hybrid({self._lexical.name}+graph)"

    def index(self, records: Sequence[MemoryRecord]) -> None:
        self._lexical.index(records)
        if self._semantic is not None:
            self._semantic.index(records)

        in_deg: dict[str, int] = {}
        title_to_id = {r.title.lower(): r.id for r in records}
        for rec in records:
            for link in rec.links:
                target_id = title_to_id.get(link.lower(), link)
                in_deg[target_id] = in_deg.get(target_id, 0) + 1
        self._in_degree = in_deg

    def query(self, query: SearchQuery) -> list[SearchResult]:
        lex_hits = self._lexical.query(query)
        sem_hits = self._semantic.query(query) if self._semantic is not None else []

        merged: dict[str, SearchResult] = {}
        for hit in lex_hits:
            graph_boost = 1.0 + min(0.5, 0.1 * self._in_degree.get(hit.record.id, 0))
            merged[hit.record.id] = SearchResult(
                record=hit.record,
                score=round(hit.score * graph_boost, 6),
                matched_terms=list(hit.matched_terms),
                backend=self.name,
            )

        for hit in sem_hits:
            if hit.record.id in merged:
                existing = merged[hit.record.id]
                existing.score = round(existing.score + hit.score, 6)
                existing.matched_terms = sorted(set(existing.matched_terms + hit.matched_terms))
            else:
                merged[hit.record.id] = SearchResult(
                    record=hit.record,
                    score=hit.score,
                    matched_terms=list(hit.matched_terms),
                    backend=self.name,
                )

        ranked = sorted(merged.values(), key=lambda r: -r.score)
        return ranked[: query.limit]
