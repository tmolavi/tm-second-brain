# Release Notes — `v0.1.0`

**TM Second Brain (`tmolavi/tm-second-brain`)** — Open-Source, Model-Agnostic, Local-First Memory & Knowledge Infrastructure for AI Agents.

## Highlights
* **Pure-Python 3.10+ Stdlib Core (`dependencies = []`):** Runs offline at `$0.00` cost on Linux, macOS, and Windows.
* **Canonical Markdown + SQLite FTS5 (WAL):** Lifecycle states (`draft` → `active` → `superseded` → `archived`), provenance, conflict detection, and immutable `.tm-brain/corrections.jsonl` audit trail.
* **Hybrid Retrieval:** Built-in BM25 + wikilink graph boost + SQLite FTS5, with optional (disabled-by-default) QMD & Ollama adapters.
* **Governed Learning & Activity Logs:** `FEEDBACK.md` pattern scanner with L1 Draft → L2 Human Approval gates and secret-redacted `working-dir/agent-log/YYYY-MM.md`.
* **Four-Environment Isolation:** Dedicated adapters for `hamzad-core` (`HamzadBridge`), `main-hermes` (`MainHermesAdapter`), `hermes-personal-desktop-finland` (`HermesPersonalDesktopFinlandAdapter`), and `hermes-personal-desktop-mac` (`HermesPersonalDesktopMacAdapter`), plus 6 coding agent harnesses + Obsidian + stdio MCP.
* **Three Starter Vaults & 5-Language Docs:** `personal-knowledge`, `business-project`, `developer-agent`, with synchronized documentation in English, Persian, Istanbul Turkish, Azerbaijani Turkish, and Arabic.
