# Release Notes — `v0.3.0`

**TM Second Brain (`tmolavi/tm-second-brain`)** — AutoSwarm-Inspired Agent Orchestration Skill & Ecosystem Rollout.

## Highlights
* **Portable Agent Orchestration (`tm-agent-orchestration`):** Reusable skill enabling multi-agent delegation, parallel DAG execution, inter-agent structured envelopes, session recovery, tokenized approval gates, and result aggregation.
* **Pure-Python Engine (`tm_second_brain.orchestration`):** Zero external dependencies, stdlib Python 3.10+, thread-safe execution, and durable JSON session state persistence under `.tm-brain/orchestration_sessions/`.
* **Zero Duplication Guarantee:** Operates on top of existing Hamzad AI Gateway and Hermes command centers without spawning duplicate routers or competing orchestrators.
* **10/10 Acceptance Scenarios Passed:** Comprehensive test suite in `tests/test_agent_orchestration.py` (52 total passing tests).
* **Ecosystem Rollout:** Synchronously deployed to Antigravity, Hermes Main, Hermes Personal Desktop, and Molavi Agentic OS with strict environment isolation.
* **Synchronized Multilingual Documentation:** All 5 documentation languages (English, Persian, Turkish, Azerbaijani, Arabic) updated.

---

# Release Notes — `v0.1.0`

**TM Second Brain (`tmolavi/tm-second-brain`)** — Open-Source, Model-Agnostic, Local-First Memory & Knowledge Infrastructure for AI Agents.

## Highlights
* **Pure-Python 3.10+ Stdlib Core (`dependencies = []`):** Runs offline at `$0.00` cost on Linux, macOS, and Windows.
* **Canonical Markdown + SQLite FTS5 (WAL):** Lifecycle states (`draft` → `active` → `superseded` → `archived`), provenance, conflict detection, and immutable `.tm-brain/corrections.jsonl` audit trail.
* **Hybrid Retrieval:** Built-in BM25 + wikilink graph boost + SQLite FTS5, with optional (disabled-by-default) QMD & Ollama adapters.
* **Governed Learning & Activity Logs:** `FEEDBACK.md` pattern scanner with L1 Draft → L2 Human Approval gates and secret-redacted `working-dir/agent-log/YYYY-MM.md`.
* **Four-Environment Isolation:** Dedicated adapters for `hamzad-core` (`HamzadBridge`), `main-hermes` (`MainHermesAdapter`), `hermes-personal-desktop-finland` (`HermesPersonalDesktopFinlandAdapter`), and `hermes-personal-desktop-mac` (`HermesPersonalDesktopMacAdapter`), plus 6 coding agent harnesses + Obsidian + stdio MCP.
* **Three Starter Vaults & 5-Language Docs:** `personal-knowledge`, `business-project`, `developer-agent`, with synchronized documentation in English, Persian, Istanbul Turkish, Azerbaijani Turkish, and Arabic.
