# Changelog

All notable changes to `tm-second-brain` will be documented in this file.

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
