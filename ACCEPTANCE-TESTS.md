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
| **AT-07** | **Multi-Agent Delegation** | Delegate tasks across two distinct agent roles, verifying role catalog assignment and context preservation. |
| **AT-08** | **Parallel Execution** | Concurrently execute independent DAG tasks via worker pool, verifying timestamp overlap and dependency satisfaction. |
| **AT-09** | **Inter-Agent Message Transfer** | Pass structured `TaskEnvelope` payloads between agents with automatic secret redaction (`[REDACTED_API_KEY]`). |
| **AT-10** | **Session Recovery (No Duplication)** | Abort/fail an execution, resume session from `.tm-brain/orchestration_sessions/`, verify already-completed tasks are skipped. |
| **AT-11** | **Approval Gate** | Tasks tagged `requires_approval=True` or `RiskLevel.HIGH` pause in `BLOCKED_ON_APPROVAL` until an explicit ticket approval is granted. |
| **AT-12** | **Result Aggregation & Conflict Detection** | Aggregate outputs from multiple agents, detect missing evidence artifacts, and flag contradictory keys (`verdict`, `score`). |
| **AT-13** | **Agent Fallback** | Detect an unavailable primary agent (`available=False`), reroute to `fallback_role_id`, and record the fallback event. |
| **AT-14** | **Zero Duplicate Engine** | Verify `AgentOrchestrator` reuses TM Second Brain standard storage without spawning separate daemon engines. |
| **AT-15** | **Adapter Compatibility** | Verify all 6 coding agent harnesses (`HarnessAdapter`) successfully export `tm-agent-orchestration`. |
| **AT-16** | **Credential & Memory Isolation** | Verify Main Hermes and Hermes Personal Desktop keep orchestration episodes strictly isolated with zero credential leakage. |

