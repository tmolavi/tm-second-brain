# Research Audit: Reference Repositories

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 1 — Repository & License Audit  
> **Date:** 2026-11-12  
> **Purpose:** Comprehensive technical and architectural audit of five reference Obsidian + AI agent repositories to inform an original, modular, multilingual, agent-agnostic Second Brain and Persistent Memory system.

---

## 1. Executive Summary

Five open-source repositories were cloned and inspected in full (source code, directory layout, manifests, scripts, hooks, skills, and licenses):

1. [`kepano/obsidian-skills`](https://github.com/kepano/obsidian-skills) — Official Obsidian Agent Skills specification & plugin pack.
2. [`breferrari/obsidian-mind`](https://github.com/breferrari/obsidian-mind) — Multi-agent persistent memory vault with TypeScript lifecycle hooks, QMD semantic search, and an `om` MCP server.
3. [`ballred/obsidian-claude-pkm`](https://github.com/ballred/obsidian-claude-pkm) — Zero-dependency bash/Markdown goal-cascade accountability system (3-year → yearly → project → monthly → weekly → daily).
4. [`heyitsnoah/claudesidian`](https://github.com/heyitsnoah/claudesidian) — PARA-based Obsidian + Claude Code starter kit with thinking/writing modes and optional Gemini Vision / Firecrawl integrations.
5. [`louisfb01/obsidian-agent-vault-template`](https://github.com/louisfb01/obsidian-agent-vault-template) — Agent-agnostic vault template featuring `AGENT-RULES.md`, `FEEDBACK.md` skill self-improvement loops, `working-dir/agent-log/`, and `skill_health.py`.

**Key Conclusion:** None of the five repositories alone satisfies the requirements of `tm-second-brain` (cross-platform Python/Markdown core, first-class Hermes & Hamzad interoperability, 5-language documentation, explicit memory lifecycle with conflict history and user-approved learning, project-scoped isolation, and privacy/PII redaction). Instead, `tm-second-brain` will synthesize their strongest patterns into an **original MIT-licensed architecture** while avoiding their limitations.

---

## 2. Per-Repository Audit

### 2.1 `kepano/obsidian-skills`

* **URL:** <https://github.com/kepano/obsidian-skills>
* **License:** MIT (`Copyright (c) 2026 Steph Ango (@kepano)`)
* **Stack & Dependencies:** Pure Markdown (`SKILL.md` + `references/`), JSON plugin manifests (`.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, `plugins/obsidian/plugin.json`), and `scripts/bump.sh`. No runtime dependencies in the repo itself; `obsidian-cli` and `obsidian-headless` skills target Obsidian 1.12+.
* **Directory Structure:**
  * `plugins/obsidian/skills/`: `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`, `obsidian-headless`, `defuddle`, `knap`.
  * Plugin marketplace descriptors for `.agents`, `.claude-plugin`, `.cursor-plugin`.
* **Architecture & Features:**
  * Follows the open [Agent Skills specification](https://agentskills.io/specification).
  * Provides authoritative reference specs for Obsidian Flavored Markdown (wikilinks, embeds, callouts, YAML properties), Obsidian Bases (`.base` database views), JSON Canvas (`.canvas`), Obsidian CLI, Obsidian Headless, Defuddle (clean web-to-markdown), and Knap (JSON/CSV template rendering).
* **Reusable Concepts:**
  * Standard `SKILL.md` + `references/` layout.
  * Cross-harness plugin marketplace manifests.
  * Exact Obsidian syntax conventions (`.md`, `.base`, `.canvas`).
* **Limitations:**
  * Purely a skill/reference pack—no memory engine, no vault structure, no lifecycle hooks, no semantic search, no privacy controls.
* **Integration Strategy:** **Adopt specification & interoperate** via our Obsidian adapter; reference/attribute upstream concepts rather than duplicating Obsidian docs.

---

### 2.2 `breferrari/obsidian-mind`

* **URL:** <https://github.com/breferrari/obsidian-mind>
* **License:** MIT (`Copyright (c) 2026 Brenno Ferrari`)
* **Stack & Dependencies:** Node.js 22+ (TypeScript executed via `--experimental-strip-types`), Obsidian 1.12+ CLI, optional `@tobilu/qmd` (local hybrid search with `embeddinggemma-300M`, `qmd-query-expansion-1.7B`, `Qwen3-Reranker-0.6B`), optional `shardmind` installer/upgrader.
* **Directory Structure:**
  * `AGENTS.md`, `Home.md`, `vault-manifest.json`, `.mcp.json`.
  * Domain folders: `brain/` (`North Star.md`, `Memories.md`, `Key Decisions.md`, `Patterns.md`, `Gotchas.md`), `work/` (`active/`, `archive/`, `incidents/`, `1-1/`, `meetings/`), `org/` (`people/`, `teams/`), `perf/` (`Brag Doc.md`, `competencies/`, `evidence/`), `bases/`, `templates/`, `reference/`, `thinking/`.
  * Agent wiring: `.claude/` (`scripts/`, `commands/`, `agents/`, `rules/`, `skills/`), `.codex/hooks.json`, `.gemini/settings.json` + `.gemini/commands/*.toml`, `.shardmind/`.
* **Architecture & Features:**
  * **"Procedural code owns the environment; the agent owns content."** Deterministic scripts handle validation, classification, budget-capped `SessionStart` injection, and `PostToolUse` checks.
  * **Cross-Repo `om` MCP Server (`.claude/scripts/om-mcp.mjs` + `lib/memory-write.ts`):** Exposes `search`, `expand`, `recall`, `remember`, `record_work`, `reason`, `health`.
  * **Epistemic Memory Contract:** Every memory carries `confidence` (`verified | inferred | unverified`), `scope` (`general | platform | project`), `projects`, `platforms`, `verification`, `generality`, server-derived `origin`, and Windows-safe filename sanitization. Corrections supersede rather than overwrite.
  * **Multi-Agent Support:** Claude Code (full + mod), Codex CLI (`.codex/hooks.json`), Gemini CLI (`.gemini/settings.json` + TOML command wrappers), plus `AGENTS.md` size-capped (<22 KB) for Antigravity/Grok.
  * **Token Efficiency:** Tiered loading, injection-size meter, listing collapse, and budget degradation.
* **Reusable Concepts:**
  * Epistemic memory contract (`confidence`, `scope`, `verification`, `origin`, supersede-on-correction).
  * `vault-manifest.json` separating `infrastructure` vs `user_content_roots` for safe upgrades.
  * `mcp_exposed_roots` / `private` tag exclusion.
  * Cross-repo MCP tool surface (`search`, `expand`, `recall`, `remember`, `record_work`, `health`).
* **Limitations:**
  * Tightly coupled to Node 22 `--experimental-strip-types` and Claude Code `.claude/` directory conventions (Codex/Gemini point into `.claude/scripts/`).
  * Heavy engineering-manager/work-performance persona (`perf/Brag Doc.md`, `1-1/`, `incidents/`), less general for personal/research/multi-domain PKM.
  * No Hermes, Goose, OpenCode, or Hamzad integration.
  * Requires Node 22+ and external `qmd` for semantic search; no pure-Python core.
  * Lacks 5-language documentation (`en`, `fa`, `tr`, `az`, `ar`).
* **Integration Strategy:** **Rewrite core patterns in pure Python** (epistemic contract, supersede history, MCP surface, manifest-driven safe upgrades) and **integrate QMD as an optional retrieval backend**.

---

### 2.3 `ballred/obsidian-claude-pkm`

* **URL:** <https://github.com/ballred/obsidian-claude-pkm>
* **License:** MIT (`Copyright (c) 2024 Obsidian Claude PKM Contributors`)
* **Stack & Dependencies:** Zero external dependencies; Bash scripts (`.claude/hooks/*.sh`, `scripts/setup.sh`, `scripts/customize.sh`) + Windows `scripts/setup.bat` + Markdown.
* **Directory Structure:**
  * `vault-template/`: `CLAUDE.md`, `Goals/` (`0. Three Year Goals.md` → `3. Weekly Review.md`), `Projects/*/CLAUDE.md`, `Daily Notes/`, `Templates/`, `Archives/`, `.claude/` (`agents/`, `skills/`, `hooks/`, `rules/`, `output-styles/coach.md`).
* **Architecture & Features:**
  * **The Goal Cascade:** Connects 3-Year Vision → Yearly Goals → Projects → Monthly Goals → Weekly Review → Daily Tasks.
  * **Review Cadence:** `/daily` (morning/evening), `/weekly`, `/monthly`, `/review` (auto-router), `/project`, `/goal-tracking`.
  * **BYOV (`/adopt`):** Adapts to an existing vault's folder structure (PARA, Zettelkasten, LYT) without forcing a migration.
  * **Safe `/upgrade`:** Timestamped backup + diff review without touching user content.
  * **Hooks:** `session-init.sh` (surfaces "ONE Big Thing", days since weekly review, active project count), `auto-commit.sh`, `skill-discovery.sh`.
* **Reusable Concepts:**
  * Goal-to-daily-task cascade (`3-Year → Yearly → Monthly → Weekly → Daily`).
  * `/adopt` (Bring Your Own Vault) pattern—essential for preserving user data.
  * Safe backup-and-diff upgrade workflow.
* **Limitations:**
  * Claude Code–only (`CLAUDE.md`, `.claude/`).
  * Relies on POSIX `bash`, `grep`, `sed`, `date` differences between macOS and Linux; Windows support is only a setup `.bat` script, while hooks are `.sh`.
  * No semantic search, no knowledge graph auditing beyond basic link checks, no provenance/confidence model, no privacy redaction.
* **Integration Strategy:** **Reuse workflow concepts** (goal cascade, daily/weekly/monthly review templates, BYOV `/adopt` UX) implemented in cross-platform Python.

---

### 2.4 `heyitsnoah/claudesidian`

* **URL:** <https://github.com/heyitsnoah/claudesidian>
* **License:** MIT (`Copyright (c) 2025 Noah Brier / Alephic`). Bundles `kepano/obsidian-skills` (`LICENSE-kepano`, MIT) and `anthropics/skills/skill-creator` (`LICENSE.txt`, Apache-2.0 + `NOTICE.md`).
* **Stack & Dependencies:** Node.js (`pnpm@9.15.4`), `@modelcontextprotocol/sdk`, `@google/generative-ai` (optional Gemini Vision MCP), optional `firecrawl` scripts, ESLint/Prettier, `uv`/Python for `quick_validate.py`.
* **Directory Structure:**
  * PARA layout: `00_Inbox/`, `01_Projects/`, `02_Areas/`, `03_Resources/`, `04_Archive/`, `05_Attachments/`, `06_Metadata/` (`Templates/`, `Reference/`).
  * `.agents/skills/` as canonical skill location, symlinked into `.claude/skills/` and `.pi/skills/`.
  * `.scripts/` (`firecrawl-*.sh`, `fix-renamed-links.js`, `update-attachment-links.js`, `vault-stats.sh`).
* **Architecture & Features:**
  * **Thinking Mode vs. Writing Mode:** Explicit separation between exploratory questioning/synthesis and deliverable drafting.
  * **PARA Organization:** Clean numbered folders for Projects, Areas, Resources, Archive, plus Inbox and Attachments.
  * **Multi-harness Skill Symlinks:** `.agents/skills/` canonical directory symlinked to `.claude/skills/` and `.pi/skills/`.
  * **Optional Multimodal & Web Capture:** Gemini Vision MCP server (`.claude/mcp-servers/gemini-vision.mjs`) and Firecrawl batch scraping.
* **Reusable Concepts:**
  * `.agents/skills/` as a canonical skill directory (though symlinks can break on Windows without Developer Mode, so a Python/CLI sync/copy or native discovery adapter is safer cross-platform).
  * Thinking vs. Writing mode distinction.
  * Attachment/link maintenance utilities (`fix-renamed-links`, orphan attachment detection).
* **Limitations:**
  * Heavy Node/pnpm dev tooling (`eslint`, `prettier`, `typescript-eslint`) for what is primarily a Markdown vault.
  * Symlink-based multi-agent sharing is fragile on Windows.
  * Bundles Apache-2.0 `skill-creator` inside an MIT repo (requires careful `NOTICE.md` handling).
  * No persistent memory lifecycle, conflict detection, or semantic search.
* **Integration Strategy:** **Reuse PARA template option & Thinking/Writing workflow concepts**; avoid bundling Apache-2.0 `skill-creator` or Node/pnpm toolchain overhead.

---

### 2.5 `louisfb01/obsidian-agent-vault-template`

* **URL:** <https://github.com/louisfb01/obsidian-agent-vault-template>
* **License:** MIT (`Copyright (c) 2026 Louis-François Bouchard`). Adapts note spec from `eugeniughelbur/obsidian-second-brain` (`AI-FIRST.md`) and skill health concepts from `warpdotdev/common-skills` (MIT).
* **Stack & Dependencies:** Zero mandatory dependencies. Python 3 standard library only for `Skills/vault-maintenance/scripts/skill_health.py`. Pure Markdown + `.obsidian/` core plugin config.
* **Directory Structure:**
  * `START-HERE.md`, `AGENT-RULES.md`, `AGENTS.md`, `CLAUDE.md` (pointers to `AGENT-RULES.md`).
  * `Skills/` (`Skills Index.md`, `example-voice/`, `html-prototypes/`, `scheduled-runs/`, `vault-maintenance/`), each with `SKILL.md` + `FEEDBACK.md`.
  * `Areas/` (`Personal/`, `Professional/example-project/` with `index.md` + `progress-log.md`).
  * `working-dir/` (`agent-log/YYYY-MM.md`, task scratch folders), `Templates/`, `_archive/`.
* **Architecture & Features:**
  * **Single Contract (`AGENT-RULES.md`):** `CLAUDE.md` and `AGENTS.md` are 1-line pointers so every agent obeys the same rules.
  * **Feedback-Driven Skill Improvement (`FEEDBACK.md`):** Every skill logs run outcomes and user corrections; repeated corrections become *promotion candidates* for `SKILL.md` (with user approval).
  * **Cross-Agent Activity Log (`working-dir/agent-log/YYYY-MM.md`):** One line per agent run so Claude, Codex, and scheduled tasks see each other's actions.
  * **Project Resumability (`index.md` + `progress-log.md`):** New sessions resume from two files.
  * **Privacy & Ownership Rules (§2):** Private folders (`Areas/Personal/`) never copied to public drafts/prompts; `raw/` is read-only; generated files are rebuilt, not hand-edited.
  * **`skill_health.py`:** Pure-Python stdlib script that lints skills and scans local Claude Code / Codex session logs for user correction patterns while redacting/skipping private paths.
* **Reusable Concepts:**
  * `AGENT-RULES.md` + thin harness pointers (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`).
  * `FEEDBACK.md` per-skill correction log + promotion-candidate workflow.
  * `working-dir/agent-log/YYYY-MM.md` shared activity log.
  * `index.md` + `progress-log.md` project resumability.
  * Pure-Python stdlib `skill_health.py` pattern (extended to all 7 target harnesses + user approval gate).
  * Explicit ownership & private-folder boundaries.
* **Limitations:**
  * Purely manual/convention-based; no programmatic memory store, no semantic/hybrid search, no MCP server, no conflict resolution or confidence scoring, no export/backup CLI, no Hermes/Hamzad/Goose/OpenCode/Antigravity adapters.
* **Integration Strategy:** **Adopt and formalize** the `AGENT-RULES.md` contract, `FEEDBACK.md` promotion loop, `agent-log`, and `index.md` + `progress-log.md` patterns into our Python core + Markdown vault schema.

---

## 3. Cross-Repository Synthesis: Reuse vs. Rewrite vs. Integrate

| Capability | Source Pattern(s) | Decision | Rationale |
|---|---|---|---|
| Obsidian Markdown, Bases, Canvas conventions | `obsidian-skills` | **Integrate (Spec)** | Standardize on Obsidian formats; invoke `obsidian` CLI optionally. |
| Epistemic memory (`confidence`, `scope`, `origin`, supersede) | `obsidian-mind` | **Rewrite (Python)** | Port concepts to pure Python 3.10+ for cross-platform, zero-Node-dep core. |
| `vault-manifest.json` + safe upgrade / BYOV `/adopt` | `obsidian-mind`, `obsidian-claude-pkm` | **Rewrite (Python)** | Essential for preserving user data on install/upgrade across OSes. |
| Goal Cascade & Daily/Weekly/Monthly Reviews | `obsidian-claude-pkm` | **Reuse (Templates)** | Incorporate into vault templates & review workflows. |
| PARA + Work/Personal Areas structure | `claudesidian`, `obsidian-agent-vault-template` | **Reuse (Templates)** | Offer modular vault profiles (PARA, Work/Goals, Minimal). |
| `AGENT-RULES.md` + `FEEDBACK.md` + `agent-log` | `obsidian-agent-vault-template` | **Rewrite + Extend** | Formalize with L1/L2 user-approval gates and multi-agent log adapters. |
| Semantic Search (`qmd`) | `obsidian-mind` | **Integrate (Adapter)** | Keep optional behind `RetrievalBackend` interface alongside built-in BM25. |
| Agent Harnesses (Claude, Codex, Gemini, OpenCode, Hermes, Goose, Antigravity) | `obsidian-mind`, `claudesidian`, `molavi-agentic-os` | **Integrate (Adapters)** | Unified `AGENTS.md` + `SKILL.md` + MCP server + thin per-harness exporters. |
| Hamzad `MemoryService` & `molavi-agentic-os` `MemoryInterface` | `molavi-agentic-os` | **Integrate (Adapter)** | Bridge without duplicating `Hamzad MemoryService` or mutating prod installs. |
| Privacy, PII/secret redaction, L0–L3 permissions | `TM-OPEN-SOURCE-STANDARD.md`, `obsidian-agent-vault-template` | **Rewrite (Core)** | First-class privacy filter & redaction engine in Python core. |
