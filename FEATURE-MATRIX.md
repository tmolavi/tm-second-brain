# Feature Matrix: Reference Repositories vs. TM Second Brain

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 1 & 2 — Feature Mapping  
> **Date:** 2026-11-12

---

## 1. Capability Comparison

Legend: **Full** = native, complete support · **Partial** = basic or manual · **Optional** = via external tool · **—** = not supported.

| Feature / Capability | `obsidian-skills` | `obsidian-mind` | `obsidian-claude-pkm` | `claudesidian` | `obsidian-agent-vault-template` | **`tm-second-brain` (Target)** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Obsidian-Native Formats (`.md`, `.base`, `.canvas`)** | **Full** | **Full** | Partial (`.md`) | Partial (`.md` + skills) | Partial (`.md`) | **Full** |
| **Persistent Cross-Session Memory** | — | **Full** (`brain/`, `memories/`) | Partial (`memory: project`) | Partial (Vault notes) | **Full** (`AGENT-RULES`, logs) | **Full** (Markdown + SQLite index) |
| **Memory Lifecycle (`draft`→`active`→`superseded`→`archived`)** | — | Partial (supersede marker) | — | — | Partial (`_archive/`) | **Full** |
| **Provenance & Confidence (`verified`/`inferred`/`unverified`)** | — | **Full** | — | — | Partial (inline dates) | **Full** |
| **Conflict Detection & Correction History** | — | Partial (`/om-correct`) | — | — | — | **Full** |
| **User-Approved Learning from Corrections** | — | — | — | — | **Full** (`FEEDBACK.md` + `skill_health.py`) | **Full** (L1 Draft → L2 Approval) |
| **Project-Scoped Memory Isolation** | — | **Full** (`scope`, `projects`) | Partial (`Projects/*/CLAUDE.md`) | — | Partial (`Areas/<project>/`) | **Full** |
| **Semantic & Hybrid Retrieval** | — | **Optional** (`qmd`) | — | — | — | **Full** (Built-in BM25 + Graph + Optional QMD/Ollama) |
| **Goal & Project Cascade Tracking** | — | Partial (`North Star`, `work/active`) | **Full** (3-Yr → Daily) | Partial (PARA) | Partial (`index.md` + `progress-log.md`) | **Full** |
| **Daily / Weekly / Monthly Reviews** | — | Partial (standup, weekly) | **Full** | Partial (daily, weekly) | Partial (weekly maintenance) | **Full** |
| **Knowledge Graph & Cross-Linking** | **Full** | **Full** | Partial | Partial | **Full** | **Full** |
| **Agent Activity Logs** | — | Partial (MCP read log) | — | — | **Full** (`agent-log/YYYY-MM.md`) | **Full** (Structured + Markdown) |
| **Export, Import & Safe Backup/Upgrade** | — | **Full** (`vault-manifest.json`, ShardMind) | **Full** (`/adopt`, `/upgrade`) | Partial (`/upgrade`) | — | **Full** |
| **Privacy Controls & Secret/PII Redaction** | — | Partial (`private` tag, `mcp_exposed_roots`) | — | — | Partial (`Private folders` rule) | **Full** (Policy + Regex/Secret Redactor) |
| **Claude Code Support** | **Full** | **Full** | **Full** | **Full** | **Full** | **Full** (Adapter) |
| **OpenAI Codex Support** | **Full** | **Full** | — | **Full** | **Full** | **Full** (Adapter) |
| **Gemini CLI Support** | — | **Full** | — | — | — | **Full** (Adapter) |
| **OpenCode Support** | **Full** | — | — | **Full** | — | **Full** (Adapter) |
| **Goose Support** | — | — | — | — | — | **Full** (Adapter) |
| **Antigravity Support** | — | Partial (`AGENTS.md`) | — | — | — | **Full** (Adapter) |
| **Hermes Agent Support** | — | — | — | — | — | **Full** (First-Class Adapter) |
| **Hamzad Ecosystem Interop (`MemoryService`)** | — | — | — | — | — | **Full** (First-Class Bridge) |
| **Cross-Platform (macOS, Linux, Windows)** | **Full** | **Full** (Node 22) | Partial (Bash hooks) | Partial (symlinks/bash) | **Full** | **Full** (Pure Python 3.10+ stdlib) |
| **Zero Mandatory API / Free-First** | **Full** | **Full** | **Full** | **Full** | **Full** | **Full** ($0.00 default) |
| **5-Language Documentation (`en`, `fa`, `tr`, `az`, `ar`)** | — | — (en, ja, zh, ko) | — | — | — | **Full** |

---

## 2. Key Differentiators of `tm-second-brain`

1. **Agent-Agnostic Pure-Python Core:** No Node 22 or POSIX-bash lock-in; works identically on Linux, macOS, and Windows.
2. **First-Class Hermes & Hamzad Bridge:** Interoperates with `molavi-agentic-os` (`MemoryInterface`) and Hamzad `MemoryService` without duplicating runtime state.
3. **Complete Epistemic + Lifecycle Engine:** Combines `obsidian-mind`'s provenance/confidence/scope model with explicit lifecycle states, conflict detection, and immutable correction history.
4. **Governed Self-Improvement:** Formalizes `obsidian-agent-vault-template`'s `FEEDBACK.md` loop under `TM-OPEN-SOURCE-STANDARD.md` L1/L2 human-approval gates.
5. **Multilingual & Local-First:** Full 5-language documentation (`en`, `fa`, `tr`, `az`, `ar`) and zero-cost default retrieval.
