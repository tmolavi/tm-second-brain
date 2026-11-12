"""Optional semantic retrieval adapters (QMD & Ollama) — disabled by default, zero auto-install."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Sequence

from ..core.contracts import PrivacyPolicy
from ..core.models import MemoryRecord, SearchQuery, SearchResult
from ..privacy.policy import DefaultPrivacyPolicy
from .bm25 import matches_filters


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class QMDRetrievalAdapter:
    """Optional QMD (@tobilu/qmd) adapter. Disabled by default; never installs qmd or models."""

    def __init__(
        self,
        vault_root: Path | str,
        *,
        index_name: str = "tm-second-brain",
        enabled: bool = False,
        privacy: PrivacyPolicy | None = None,
    ) -> None:
        self.vault_root = Path(vault_root).resolve()
        self.index_name = index_name
        self.enabled = enabled
        self._privacy = privacy or DefaultPrivacyPolicy()
        self._by_path: dict[str, MemoryRecord] = {}

    @property
    def name(self) -> str:
        return "qmd"

    def is_available(self) -> bool:
        return self.enabled and shutil.which("qmd") is not None

    def index(self, records: Sequence[MemoryRecord]) -> None:
        self._by_path = {r.relative_path: r for r in records if r.relative_path}

    def query(self, query: SearchQuery) -> list[SearchResult]:
        if not self.is_available() or not query.text.strip():
            return []
        try:
            proc = subprocess.run(
                ["qmd", "--index", self.index_name, "search", query.text, "--json"],
                cwd=str(self.vault_root),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                return []
            items = json.loads(proc.stdout)
        except Exception:
            return []

        results: list[SearchResult] = []
        for item in items if isinstance(items, list) else []:
            rel = str(item.get("path") or item.get("file") or "")
            rec = self._by_path.get(rel)
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
            results.append(
                SearchResult(
                    record=rec,
                    score=float(item.get("score", 0.5)),
                    matched_terms=["qmd"],
                    backend=self.name,
                )
            )
        return results[: query.limit]


class OllamaRetrievalAdapter:
    """Optional Ollama HTTP embeddings adapter. Disabled by default; never installs Ollama or weights."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "nomic-embed-text",
        enabled: bool = False,
        privacy: PrivacyPolicy | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.enabled = enabled
        self._privacy = privacy or DefaultPrivacyPolicy()
        self._records: list[MemoryRecord] = []
        self._vectors: dict[str, list[float]] = {}

    @property
    def name(self) -> str:
        return "ollama"

    def _embed(self, text: str) -> list[float] | None:
        if not self.enabled:
            return None
        payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                vec = data.get("embedding")
                return [float(x) for x in vec] if isinstance(vec, list) else None
        except Exception:
            return None

    def index(self, records: Sequence[MemoryRecord]) -> None:
        self._records = list(records)
        if not self.enabled:
            return
        for rec in self._records:
            if self._privacy.is_private(rec):
                continue
            if rec.id not in self._vectors:
                vec = self._embed(f"{rec.title}\n{rec.body}")
                if vec is not None:
                    self._vectors[rec.id] = vec

    def query(self, query: SearchQuery) -> list[SearchResult]:
        if not self.enabled or not query.text.strip():
            return []
        q_vec = self._embed(query.text)
        if q_vec is None:
            return []

        results: list[SearchResult] = []
        for rec in self._records:
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
            r_vec = self._vectors.get(rec.id)
            if r_vec is None:
                continue
            sim = _cosine_similarity(q_vec, r_vec)
            if sim > 0.0:
                results.append(
                    SearchResult(
                        record=rec,
                        score=round(sim, 6),
                        matched_terms=["embedding"],
                        backend=self.name,
                    )
                )
        results.sort(key=lambda r: -r.score)
        return results[: query.limit]
