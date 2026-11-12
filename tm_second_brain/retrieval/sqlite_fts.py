"""Rebuildable local SQLite FTS5 retrieval cache (WAL mode, zero external deps)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

from ..core.contracts import PrivacyPolicy
from ..core.models import MemoryRecord, SearchQuery, SearchResult
from ..privacy.policy import DefaultPrivacyPolicy
from .bm25 import matches_filters, tokenize


class SQLiteFTSBackend:
    """Rebuildable SQLite FTS5 cache at .tm-brain/index.db supporting concurrent readers."""

    def __init__(self, db_path: Path | str, *, privacy: PrivacyPolicy | None = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._privacy = privacy or DefaultPrivacyPolicy()
        self._records: dict[str, MemoryRecord] = {}
        self._init_db()

    @property
    def name(self) -> str:
        return "sqlite-fts5"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    title,
                    tags,
                    body
                )
                """
            )
            conn.commit()

    def index(self, records: Sequence[MemoryRecord]) -> None:
        self._records = {r.id: r for r in records}
        with self._connect() as conn:
            conn.execute("DELETE FROM memories_fts")
            conn.executemany(
                "INSERT INTO memories_fts (id, title, tags, body) VALUES (?, ?, ?, ?)",
                [(r.id, r.title, " ".join(r.tags), r.body) for r in records],
            )
            conn.commit()

    def query(self, query: SearchQuery) -> list[SearchResult]:
        terms = tokenize(query.text)
        if not terms or not self._records:
            return []
        fts_expr = " OR ".join(f'"{t}"' for t in terms)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, bm25(memories_fts) AS rank FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts_expr, max(query.limit * 3, 20)),
            ).fetchall()

        results: list[SearchResult] = []
        for mem_id, rank in rows:
            rec = self._records.get(mem_id)
            if rec is None:
                continue
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
            # SQLite bm25() returns negative values where more negative = better match
            score = round(max(0.001, -float(rank)), 6)
            results.append(
                SearchResult(
                    record=rec,
                    score=score,
                    matched_terms=terms,
                    backend=self.name,
                )
            )
        return results[: query.limit]
