# Roadmap: TM Second Brain

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Standard:** [`TM-OPEN-SOURCE-STANDARD.md`](../molavi-agentic-os/TM-OPEN-SOURCE-STANDARD.md)  
> **Date:** 2026-11-12

---

## Phase 1: Repository & License Audit *(Completed)*
- [x] Clone and inspect all 5 reference repositories (`kepano/obsidian-skills`, `breferrari/obsidian-mind`, `ballred/obsidian-claude-pkm`, `heyitsnoah/claudesidian`, `louisfb01/obsidian-agent-vault-template`).
- [x] Complete `RESEARCH.md` with architecture, workflows, reusable patterns, and limitations.
- [x] Complete `LICENSE-AUDIT.md` verifying MIT compatibility and excluding Apache-2.0 sub-components (`skill-creator`).
- [x] Author `THIRD_PARTY_NOTICES.md` and `SOURCES.md`.

## Phase 2: Technical Architecture & Feature Mapping *(Completed)*
- [x] Complete `FEATURE-MATRIX.md` comparing all 5 references against `tm-second-brain`.
- [x] Complete `ARCHITECTURE.md` defining the 3-layer local-first Python + Markdown design.
- [x] Establish initial repository structure (`tm_second_brain/`, `vault-template/`, `skills/`, `docs/`, `tests/`, `examples/`).

## Phase 3: Define Interfaces & Integration Contracts *(Completed)*
- [x] Define Python abstract base classes / protocols in `tm_second_brain/core/contracts.py`:
  - `MemoryAPI`, `RetrievalBackend`, `PrivacyPolicy`, `BackupManager`, `HarnessAdapter`, `HamzadMemoryBridge`.
- [x] Define canonical schemas and contracts: `API-SPEC.md`, `ADAPTER-CONTRACTS.md`, `MEMORY-SCHEMA.md`, `INTEGRATION-SPEC.md`, `ACCEPTANCE-TESTS.md`.

## Phase 4: Build Minimal Working Core *(Completed)*
- [x] Implement `tm_second_brain/core/` (`models.py`, `contracts.py`), `tm_second_brain/privacy/policy.py`, `tm_second_brain/retrieval/bm25.py`, `tm_second_brain/memory/markdown_store.py`, and `tm_second_brain/backup/archive.py`.
- [x] Implement `tm_second_brain/cli.py` (`init`, `remember`, `recall`, `search`, `correct`, `backup`, `restore`, `export`, `import-bundle`, `health`).
- [x] Verify with `pytest` (`tests/test_acceptance.py` AT-01..AT-05 + `tests/test_unit_core.py`, 10/10 passing).
- [ ] Populate `vault-template/` starter vault (PARA + Goal Cascade + `AGENT-RULES.md`) in Phase 5 alongside Obsidian/harness adapters.

## Phase 5: Implement Obsidian & Agent Adapters *(Completed)*
- [x] Obsidian adapter (`tm_second_brain/adapters/obsidian.py`): safe `.md` read/write with backup-before-overwrite, YAML frontmatter, wikilinks, `.base` & `.canvas` preservation.
- [x] Separate first-class bridges: **Hamzad Core** (`HamzadBridge`), **Main Hermes** (`MainHermesAdapter`), and **Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`).
- [x] Coding agent harness adapters (`Codex`, `Claude Code`, `Gemini CLI`, `OpenCode`, `Goose`, `Antigravity`) + stdio **MCP Server** (`tm-brain mcp`).
- [x] Three starter vault templates (`personal-knowledge`, `business-project`, `developer-agent`) + `tm-brain init --template`.
- [x] Synchronized 5-language documentation (`README.md` + `docs/{fa,tr,az,ar}/README.md`).

## Phase 6: Implement Memory, Retrieval & Feedback Systems *(Completed)*
- [x] Hybrid retrieval (`HybridRetrievalBackend`: BM25 + wikilink graph boost + `SQLiteFTSBackend` WAL cache) + optional (disabled-by-default) QMD & Ollama adapters.
- [x] Feedback pattern scanner (`FeedbackManager`) & L1 Draft → L2 User-Approved learning gate.
- [x] Cross-agent activity logger (`ActivityLogger`: `working-dir/agent-log/YYYY-MM.md` + `.tm-brain/activity.jsonl`).
- [x] Explicit 4-environment Hermes/Hamzad isolation (`hamzad-core`, `main-hermes`, `hermes-personal-desktop-finland`, `hermes-personal-desktop-mac`).

## Phase 7: Add Multilingual Documentation *(Completed)*
- [x] Synchronized `README.md` + comprehensive `GUIDE.md` across all 5 required languages:
  - English (`README.md`, `docs/en/GUIDE.md`)
  - Persian (`docs/fa/README.md`, `docs/fa/GUIDE.md`, RTL)
  - Istanbul Turkish (`docs/tr/README.md`, `docs/tr/GUIDE.md`)
  - Azerbaijani Turkish (`docs/az/README.md`, `docs/az/GUIDE.md`)
  - Arabic (`docs/ar/README.md`, `docs/ar/GUIDE.md`, RTL)

## Phase 8: Automated Tests, Security Review & Release *(Completed — `v0.1.0` Ready)*
- [x] Cross-platform `pytest` suite (acceptance, isolation, security, templates, Phase 6 intelligence, governance).
- [x] Automated CI (`.github/workflows/ci.yml`) on Linux, macOS, and Windows (Python 3.10–3.13).
- [x] Security & governance gate (`scripts/check_governance.py`) + [`RELEASE-NOTES.md`](RELEASE-NOTES.md).
