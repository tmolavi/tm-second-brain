# Integration & Backup Specification (`INTEGRATION-SPEC.md`)

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 3 — Interfaces & Integration Contracts

---

## 1. Hamzad `MemoryService` & `molavi-agentic-os` Integration (Non-Duplication)

### 1.1 Constraint
`tm-second-brain` **must not** duplicate Hamzad's runtime `MemoryService` or modify existing Hamzad, Hermes, or `molavi-agentic-os` installations.

### 1.2 Interoperability Contract
In `molavi-agentic-os/molavi_agentic_os/memory/base.py`, `MemoryInterface` defines four methods:
* `store_episode(session_id: str, agent_id: str, entry: Dict[str, Any]) -> None`
* `get_episodes(session_id: str, limit: int = 20) -> List[Dict[str, Any]]`
* `set_key(namespace: str, key: str, value: Any) -> None`
* `get_key(namespace: str, key: str) -> Optional[Any]`

`tm-second-brain` integrates via an optional **`HamzadMemoryBridge`** adapter:
* **Episode → Vault Sync (Opt-In):** Reads episodic entries or key-value facts from an injected `MemoryInterface` / Hamzad `MemoryService` client and writes durable, human-readable Markdown memories into `tm-second-brain` with `source_agent="hamzad"`.
* **Vault → Hamzad Recall (Opt-In):** Exposes `MemoryAPI.recall(project=...)` results formatted as `MemoryInterface` episode/key payloads so Hamzad agents can consume vault knowledge without migrating Hamzad's production database.
* **Zero Destructive Migration:** Hamzad's SQLite/PostgreSQL state remains untouched; bridging is additive and idempotent via `memory_id` / `external_ref` deduplication.

---

## 2. Main Hermes vs. Hermes Personal Desktop (Separate Targets)

`MainHermesAdapter` and `HermesPersonalDesktopAdapter` are **separate** adapters with independent `HermesEnvironmentConfig`s:
* **Main Hermes (`env:main-hermes`, `host:finland-server`):** Integrates with the production Hermes runtime without replacing Hamzad `MemoryService`, preserving its operational identity, tools, and workflows.
* **Hermes Personal Desktop (`env:hermes-personal-desktop`, `host:mac-local`):** Independent personal Mac environment. Memories are namespaced (`desktop-hermes:<ns>`) and tagged `env:hermes-personal-desktop` so they never leak into `Main Hermes` or `Hamzad Core`.
* **Controlled Knowledge Exchange:** `HermesPersonalDesktopAdapter.export_controlled_exchange(project)` exports only non-private, secret-redacted records with explicit `source_environment` provenance.
* **No Production Disruption:** Neither adapter modifies `/Users/taghimolavi/hamzad/isolated_hermes` or live server/desktop installations.

---

## 3. Safe Import / Export & Backup / Restore Contract

### 3.1 Portable Bundle Export / Import (`JSON` + Markdown)
* **Export (`export_bundle`):** Serializes non-private memories (by default; `include_private=False`) into a versioned JSON bundle (`schema_version: "1.0"`, `exported_at`, `records[]`, `sha256`).
* **Import (`import_bundle`):** Validates schema, enforces Windows-safe slugs and path-traversal checks, and skips existing identical `id`s (idempotent) unless `overwrite=True`.

### 3.2 Full Vault Backup & Restore (`.tar.gz`)
* **Backup (`create_backup`):** Archives Markdown notes, `memories/`, and `.tm-brain/corrections.jsonl` into a `.tar.gz` archive accompanied by a `backup-manifest.json` containing per-file SHA-256 checksums.
* **Restore (`restore_backup`):**
  1. Verifies every archive member path (rejects absolute paths and `..` traversal) and checks SHA-256 integrity before extracting.
  2. By default (`overwrite=False`), **preserves existing user files** and only restores missing files; `overwrite=True` creates a pre-restore safety snapshot first.

---

## 4. Multi-Agent Orchestration & AutoSwarm Pattern Integration

### 4.1 Zero-Duplication Orchestration Contract
`tm-agent-orchestration` does **not** create a second Hermes or duplicate Hamzad AI Gateway/Model Router. It defines portable task execution contracts:
* **Delegation Contract (`TaskUnit`):** Encapsulates goal, action, assigned agent role, inputs, expected artifacts, dependencies, and risk level.
* **Redacted Inter-Agent Envelopes (`TaskEnvelope`):** Passes structured messages between agents with automatic secret redaction via `PrivacyPolicy`.
* **Durable Session Recovery (`SessionJournal`):** Persists session checkpoints into `.tm-brain/orchestration_sessions/<session_id>.json`. Interrupted runs resume without re-executing already completed tasks.
* **Approval Gates:** High-risk tasks pause execution in `BLOCKED_ON_APPROVAL` and require tokenized operator approval before proceeding.
* **Result Aggregation:** Evaluates tangible evidence against Foreman rules, flags contradictory outputs across agents, and produces a consolidated synthesis.

---

## 5. License Verification Against Actual Source Files

* **Core (`tm_second_brain/`):** 100% original Python 3.10+ standard library code under **MIT License** (`LICENSE`).
* **Dependencies (`pyproject.toml`):** `dependencies = []` (zero runtime third-party packages). Dev-only optional dependencies are `pytest>=8.0` (MIT) and `ruff>=0.6.0` (MIT).
* **Upstream References (`THIRD_PARTY_NOTICES.md`):** All 5 audited repositories (`obsidian-skills`, `obsidian-mind`, `obsidian-claude-pkm`, `claudesidian`, `obsidian-agent-vault-template`) have MIT root licenses; `claudesidian`'s nested Apache-2.0 `skill-creator` is explicitly excluded.
