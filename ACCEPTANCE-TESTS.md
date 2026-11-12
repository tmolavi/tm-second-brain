# Acceptance Tests Specification (`ACCEPTANCE-TESTS.md`)

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 3 — Interfaces & Integration Contracts  
> **Test Runner:** `pytest` (`tests/test_acceptance.py`)

---

## 1. Required Acceptance Test Scenarios

| ID | Category | Scenario & Verification Criteria |
|---|---|---|
| **AT-01** | **Model Switching** | Swap `RetrievalBackend` between `BM25RetrievalBackend` and a mock semantic `RetrievalBackend` (e.g. `MockSemanticBackend`) on the same `MarkdownMemoryStore` without changing caller code or mutating Markdown files. Both backends return relevant results via `MemoryAPI.search()`. |
| **AT-02** | **Offline Operation** | Execute `init`, `remember`, `recall`, `search`, `correct`, `expand`, `backup`, and `health` with zero network access and zero API keys configured (`$0.00` cost, stdlib only). |
| **AT-03** | **Memory Persistence** | Write memories, close/re-instantiate `MarkdownMemoryStore` from disk, and verify all frontmatter fields (`id`, `status`, `scope`, `projects`, `confidence`, `provenance`, `version`, `supersedes`, `superseded_by`), body, and correction history persist across restarts; also verify project isolation (`project="alpha"` never leaks to `project="beta"`). |
| **AT-04** | **Privacy & Redaction** | 1) Memories with `private: true` or inside `private_paths` are excluded from `recall()`, `search()`, and `export_bundle()` by default, and only returned when `include_private=True`.<br>2) Secrets (`sk-...`, `ghp_...`, `AIza...`) are redacted by `PrivacyPolicy.redact()`. |
| **AT-05** | **Recovery (Backup & Restore)** | Create memories and user notes, run `create_backup()`, simulate accidental deletion of a memory file, run `restore_backup()`, verify SHA-256 integrity and that the deleted memory is recovered while existing untouched user files are preserved. |
| **AT-06** | **Environment Isolation (Hamzad / Main Hermes / Desktop)** | Verify `HamzadBridge`, `MainHermesAdapter` (`finland-server`), and `HermesPersonalDesktopAdapter` (`mac-local`) operate independently: episodes/KV stored in one environment do not leak into another; `HamzadBridge` syncs idempotently without duplicating `MemoryService` or mutating external state; controlled exchange redacts secrets and excludes `private: true`. |
