# Security & Privacy Policy

## 1. Permission Hierarchy (L0–L3)
`tm-second-brain` follows the TM Open Source Standard four-tier permission model:
* **L0 (Read-Only):** Search, recall, graph expansion, health checks, privacy audits.
* **L1 (Draft & Recommend):** Proposing skill/rule updates from `FEEDBACK.md`, drafting review summaries.
* **L2 (Human Approval Required):** Modifying canonical `SKILL.md` / `AGENTS.md` rules, overwriting/archiving user notes, or exporting/syncing outside the vault.
* **L3 (Pre-Authorized Automation):** Scheduled vault hygiene scans with deterministic audit logs.

## 2. Privacy Controls & Sensitive-Data Exclusion
* Notes tagged `private: true` in YAML frontmatter or stored under `private_paths` are excluded from cross-repo MCP responses and external LLM calls.
* Built-in secret redaction strips API keys (`sk-*`, `ghp_*`, `AIza*`, `xoxb-*`), bearer tokens, and private keys before logging or external dispatch.
* Path traversal (`..`) and Windows reserved filenames (`CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`) are blocked at write time.

## 3. Reporting Vulnerabilities
Please open a private security advisory or contact the maintainer (`tmolavi`) before public disclosure.
