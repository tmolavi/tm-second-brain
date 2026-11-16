# Changelog

All notable changes to `tm-second-brain` will be documented in this file.

## [0.3.0] - 2026-11-16
### Added
- **Portable Agent Orchestration Skill (`tm-agent-orchestration`):** AutoSwarm-inspired multi-agent coordination protocol without introducing duplicate orchestration engines, competing model routers, or external dependencies.
- **Pure-Python Orchestration Engine (`tm_second_brain.orchestration`):**
  - `AgentOrchestrator`: Multi-agent delegation, parallel DAG execution, secret-redacted inter-agent envelopes, approval gates, and result aggregation.
  - `SessionJournal`: Durable session state persistence under `.tm-brain/orchestration_sessions/<session_id>.json` enabling resumption of interrupted sessions without duplicate side effects.
  - `TaskUnit`, `TaskEnvelope`, `ApprovalRequest`, `ExecutionRecord`, `AggregationResult`, `AgentRole`.
- **CLI Commands:** Added `tm-brain orchestrate list` and `tm-brain orchestrate status <session_id>`.
- **Ecosystem Rollout & Adapter Synchronization:**
  - Deployed `tm-agent-orchestration` to Antigravity (`~/.gemini/config/skills/`), Hermes Main (`~/.hermes/skills/`), Hermes Personal Desktop (`hermes-mac-distribution/skills/`), and Molavi Agentic OS (`skills/orchestration/`).
  - Added `record_orchestration_event()` to `HamzadBridge` for idempotent Hamzad Core event logging.
- **Acceptance Tests:** Added `tests/test_agent_orchestration.py` validating 10 required scenarios (52 total tests passing).
- **5-Language Documentation Synchronization:** Updated English, Persian, Turkish, Azerbaijani, and Arabic README and Guide documentation.

## [0.2.0] - 2026-11-14
### Added
- **Architecture Decision Record (ADR) & Rejected Decisions Ledger:** Added `DecisionLedger` (`tm_second_brain.learning.decision_ledger`) with append-only JSON persistence in `.tm-brain/decision-ledger.json` and automatic Markdown generation in `Decisions/DECISION_LEDGER.md`.
- **Doubt-Driven Rejection Tracking:** Explicit method `reject_proposal(...)` capturing technical context, rejected alternatives, physical evidence of failure, and anti-rationalization proof.
- **Unit & Acceptance Test Suite:** Added `tests/test_decision_ledger.py` bringing total passed tests to 42.

## [0.1.0] - 2026-11-12
### Added
- Phase 6 Intelligence Layer: `SQLiteFTSBackend` (WAL), `HybridRetrievalBackend`, optional disabled-by-default `QMDRetrievalAdapter` & `OllamaRetrievalAdapter`, `FeedbackManager` (L1→L2 gate), and `ActivityLogger`.
- Explicit 4-environment adapters: `HamzadBridge`, `MainHermesAdapter`, `HermesPersonalDesktopFinlandAdapter`, `HermesPersonalDesktopMacAdapter`.
- Phase 7 Multilingual Documentation: `README.md` + `GUIDE.md` in English, Persian (RTL), Istanbul Turkish, Azerbaijani Turkish, and Arabic (RTL).
- Phase 8 Release Readiness: `.github/workflows/ci.yml` (Linux/macOS/Windows), `scripts/check_governance.py`, `RELEASE-NOTES.md`.

## [0.1.0-alpha] - 2026-11-12
### Added
- Phase 1 & Phase 2 deliverables: `RESEARCH.md`, `LICENSE-AUDIT.md`, `FEATURE-MATRIX.md`, `ARCHITECTURE.md`, `ROADMAP.md`.
- Governance & compliance files: `LICENSE` (MIT), `THIRD_PARTY_NOTICES.md`, `SOURCES.md`, `MODEL-REQUIREMENTS.md`, `SECURITY.md`, `CONTRIBUTING.md`, `AGENTS.md`.
- Initial repository skeleton (`tm_second_brain/`, `vault-template/`, `skills/`, `docs/`, `tests/`, `examples/`).
