# API Specification (`API-SPEC.md`)

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 3 — Interfaces & Integration Contracts  
> **Stability:** `v1alpha1` (Pure Python 3.10+ Standard Library, Model-Independent)

---

## 1. Design Invariants

1. **Model-Independent:** `MemoryAPI` and `RetrievalBackend` take plain Python types (`str`, `dict`, `dataclass`) and **never** import or require an LLM SDK, embedding model, or agent runtime.
2. **Offline-First & $0.00 Default:** All core operations (`remember`, `recall`, `search`, `correct`, `archive`, `expand`, `backup`, `restore`) work offline using local Markdown files and deterministic BM25 + graph traversal.
3. **Privacy-Enforced at Every Boundary:** Every read, search, export, and cross-project recall passes through `PrivacyPolicy` before returning content.
4. **Non-Destructive Corrections:** Updates to factual knowledge create a superseding version (`supersedes` / `superseded_by`) and append to the correction history rather than silently overwriting.

---

## 2. Core Data Types (`tm_second_brain.core.models`)

| Type | Values / Fields | Description |
|---|---|---|
| `LifecycleStatus` | `draft`, `active`, `superseded`, `archived` | Explicit memory lifecycle state. |
| `MemoryScope` | `general`, `platform`, `project` | Isolation boundary for cross-project recall. |
| `ConfidenceLevel` | `verified`, `inferred`, `unverified` | Epistemic confidence level. |
| `Provenance` | `source_agent`, `origin`, `verification`, `created_at`, `updated_at` | Origin and verification metadata. |
| `MemoryRecord` | `id`, `title`, `body`, `status`, `scope`, `projects`, `platforms`, `confidence`, `provenance`, `version`, `supersedes`, `superseded_by`, `private`, `tags`, `links` | Canonical in-memory & on-disk representation. |
| `SearchQuery` | `text`, `project`, `platforms`, `scopes`, `include_superseded`, `include_private`, `limit` | Model-independent query object. |
| `SearchResult` | `record`, `score`, `matched_terms`, `backend` | Ranked retrieval result. |

---

## 3. Stable Memory API (`MemoryAPI` Protocol)

Defined in `tm_second_brain/core/contracts.py`:

```python
class MemoryAPI(Protocol):
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
    ) -> MemoryWriteResult: ...

    def recall(
        self,
        *,
        project: str | None = None,
        platforms: list[str] | None = None,
        include_private: bool = False,
        limit: int = 20,
    ) -> list[MemoryRecord]: ...

    def search(self, query: SearchQuery) -> list[SearchResult]: ...

    def get(self, memory_id: str, *, include_private: bool = False) -> MemoryRecord | None: ...

    def expand(self, memory_id: str, *, depth: int = 1, include_private: bool = False) -> dict[str, Any]: ...

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
    ) -> MemoryWriteResult: ...

    def archive(self, memory_id: str, *, reason: str = "") -> MemoryRecord: ...

    def health(self) -> dict[str, Any]: ...
```

### 3.1 `MemoryWriteResult` & Conflict Detection
`remember(...)` returns `MemoryWriteResult(record, conflicts, warnings)`:
* If active memories in the same scope/project share high lexical/title overlap, `conflicts` lists candidate `ConflictCandidate(existing_id, title, similarity, reason)`.
* Callers can then invoke `correct(target_id, ...)` to supersede cleanly.

---

## 4. Pluggable Retrieval Backend (`RetrievalBackend` Protocol)

```python
class RetrievalBackend(Protocol):
    @property
    def name(self) -> str: ...

    def index(self, records: Sequence[MemoryRecord]) -> None: ...

    def query(self, query: SearchQuery) -> list[SearchResult]: ...
```

* **Model-Switching Guarantee:** Swapping `BM25RetrievalBackend` (default, `$0.00`, offline) for `QMDRetrievalBackend` or `OllamaRetrievalBackend` requires **zero changes** to `MemoryAPI` callers or stored Markdown files.

---

## 5. CLI Contract (`tm-brain`)

| Command | Purpose | Permission Level |
|---|---|---|
| `tm-brain init <vault>` | Initialize a new vault without overwriting existing user files | L1/L2 |
| `tm-brain remember` | Store a new memory with scope, confidence, provenance | L1 |
| `tm-brain recall` | Retrieve project-isolated active memories | L0 |
| `tm-brain search <query>` | Hybrid/BM25 search respecting privacy policy | L0 |
| `tm-brain correct <id>` | Supersede an existing memory and log correction history | L1 |
| `tm-brain backup <out>` | Create SHA-256 verified `.tar.gz` backup | L0/L1 |
| `tm-brain restore <archive>` | Restore backup safely without clobbering newer files unless `--force` | L2 |
| `tm-brain export <out.json>` | Export non-private memories (or `--include-private` explicitly) | L0/L2 |
| `tm-brain import-bundle <in.json>` | Import portable memory bundle idempotently | L1/L2 |
| `tm-brain health` | Verify vault integrity, index status, and privacy rules | L0 |
