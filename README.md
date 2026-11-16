🌐 **English** | [فارسی](docs/fa/README.md) | [Türkçe](docs/tr/README.md) | [Azərbaycan dili](docs/az/README.md) | [العربية](docs/ar/README.md)

# TM Second Brain (`tm-second-brain`)

> **An original, modular, multilingual, agent-agnostic Second Brain and Persistent Memory system for the TM / Molavi Agentic OS ecosystem.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](pyproject.toml)
[![Dependencies: Zero](https://img.shields.io/badge/runtime%20deps-zero%20(stdlib)-success.svg)](pyproject.toml)

---

## 1. Overview & Key Capabilities

`tm-second-brain` gives AI coding agents and human teams a **local-first, Markdown-canonical persistent memory** that works completely offline at **$0.00 cost** on macOS, Linux, and Windows:

* **Persistent Cross-Session Memory:** Markdown + YAML frontmatter (`mem_<YYYYMMDD>_<hash>`) with lifecycle states (`draft` → `active` → `superseded` → `archived`).
* **Provenance, Conflict Detection & Correction History:** Never silently overwrites facts; supersedes prior versions with immutable `.tm-brain/corrections.jsonl` audit logs.
* **Project-Scoped & Environment Isolation:** Strict isolation across projects and between **Hamzad Core**, **Main Hermes** (Finland server), and **Hermes Personal Desktop** (Mac local).
* **Zero-Cost Offline Retrieval:** Built-in Python BM25 + wikilink graph expansion (`expand`), with pluggable `RetrievalBackend` for optional QMD or Ollama.
* **Portable Agent Orchestration (`tm-agent-orchestration`):** AutoSwarm-inspired multi-agent delegation, parallel DAG execution, secret-redacted task envelopes, durable session recovery, and tokenized approval gates.
* **Privacy & Secret Redaction:** `private: true` / `private_paths` exclusion and automatic redaction of API keys/tokens across MCP, exports, and bridges.
* **Safe Backup, Restore & Starter Vaults:** SHA-256 verified `.tar.gz` backups with pre-restore snapshots and three ready-to-use Obsidian vault templates.

---

## 2. Three Starter Vault Templates

| Template | Best For | Key Structure |
|---|---|---|
| `personal-knowledge` | Personal PKM | PARA (`00_Inbox`–`04_Archive`), `Daily Notes/`, private `02_Areas/Personal/` |
| `business-project` | Teams & Goals | 3-Year → Weekly Goal Cascade, `Projects/`, `Meetings/`, `Decisions/`, `Home.base` |
| `developer-agent` | Engineers & AI Agents | `brain/` (`North Star`, `Key Decisions`, `Patterns`, `Gotchas`), `Skills/`, `Knowledge Graph.canvas` |

---

## 3. Ecosystem & Adapter Support

* **Flagship Operating Ecosystem:** Native memory & knowledge engine for [**TM Molavi Agentic OS**](https://github.com/tmolavi/molavi-agentic-os) (`pip install molavi-agentic-os`).
* **Obsidian:** Safe `.md` read/write (auto-backup before overwrite), YAML frontmatter, wikilinks, `.base` and `.canvas` preservation.
* **First-Class TM Targets (Independently Isolated):**
  * **Hamzad Core** (`HamzadBridge` for `MemoryService` / `MemoryInterface`, non-duplicating)
  * **Main Hermes** (`MainHermesAdapter`, production server)
  * **Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`, Mac local + controlled exchange)
* **Coding Agents:** OpenAI Codex, Claude Code, Gemini CLI, OpenCode, Goose, Antigravity + stdio **MCP Server** (`tm-brain mcp`).

---

## 4. Quick Start

```bash
# Initialize a vault with a starter template (never overwrites existing files)
python3 -m tm_second_brain.cli --vault ./my-vault init --template developer-agent

# Store and search memories offline ($0.00)
python3 -m tm_second_brain.cli --vault ./my-vault remember \
  --title "Use WAL mode" --body "Enable SQLite WAL for concurrent readers." --project core
python3 -m tm_second_brain.cli --vault ./my-vault search "WAL" --project core

# Install an agent adapter (codex | claude-code | gemini-cli | opencode | goose | antigravity)
python3 -m tm_second_brain.cli --vault ./my-vault install-adapter codex

# Multi-Agent Orchestration session inspection
python3 -m tm_second_brain.cli --vault ./my-vault orchestrate list

# Create a SHA-256 verified backup
python3 -m tm_second_brain.cli --vault ./my-vault backup ./vault-backup.tar.gz
```

---

## 5. Architecture, Skills & Model Requirements

* **Agent Skills:** [`skills/tm-agent-orchestration/SKILL.md`](skills/tm-agent-orchestration/SKILL.md) — portable AutoSwarm-inspired multi-agent coordination.
* **Architecture & Contracts:** [`ARCHITECTURE.md`](ARCHITECTURE.md), [`API-SPEC.md`](API-SPEC.md), [`ADAPTER-CONTRACTS.md`](ADAPTER-CONTRACTS.md), [`INTEGRATION-SPEC.md`](INTEGRATION-SPEC.md)
* **Model & Cost Transparency:** [`MODEL-REQUIREMENTS.md`](MODEL-REQUIREMENTS.md) ($0.00 default, zero mandatory API keys)
* **License:** MIT License — [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)

---

## 6. Comprehensive Guides & Publications

* **Molavi.pro (English Guide):** [What Is TM Second Brain? A Complete Guide to Persistent Memory for Humans and AI Agents](https://molavi.pro/notes/tm-second-brain-persistent-memory)
* **Inten (Sales OS & Architecture Guide):** [Why Your AI Sales & Engineering Stack Forgets Everything Overnight—And How TM Second Brain Fixes It at $0.00](https://inten.asia/blog/tm-second-brain-persistent-memory-en)
