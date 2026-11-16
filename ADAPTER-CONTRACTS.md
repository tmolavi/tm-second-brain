# Adapter Contracts (`ADAPTER-CONTRACTS.md`)

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 3 — Interfaces & Integration Contracts

---

## 1. Core Principle: Zero Runtime Coupling

`tm_second_brain/core/` and `tm_second_brain/memory/` **never** import agent SDKs, CLI wrappers, or LLM clients. Every external agent harness or ecosystem service connects through an explicit adapter implementing `HarnessAdapter` or `HamzadMemoryBridge`.

---

## 2. Base Harness Adapter Contract (`HarnessAdapter`)

```python
class HarnessAdapter(Protocol):
    @property
    def harness_name(self) -> str: ...

    def render_instructions(self, vault_root: Path) -> str: ...

    def export_skill(self, skill_name: str, skill_markdown: str, out_dir: Path) -> Path: ...

    def build_mcp_config(self, vault_root: Path) -> dict[str, Any]: ...
```

---

## 3. Target Harness Adapter Specifications

| Harness | Discovery / Instruction File | Skill / Command Surface | MCP / Tool Surface | Size / Platform Constraints |
|---|---|---|---|---|
| **Main Hermes (First-Class, Finland Server)** | `AGENTS.md` + `hermes_agent.json` (`environment: main-hermes`) | `SKILL.md` + `hermes_agent.json` via `MainHermesAdapter` | `MemoryInterface` (`main-hermes:<ns>`) + stdio MCP (`TM_BRAIN_ENV=main-hermes`) | Preserves production identity, tools, workflows; never mutates existing Hermes prod installs. |
| **Hermes Personal Desktop (First-Class, Mac Local)** | `AGENTS.md` + `hermes_agent.json` (`environment: hermes-personal-desktop`) | `SKILL.md` + `hermes_agent.json` via `HermesPersonalDesktopAdapter` | `MemoryInterface` (`desktop-hermes:<ns>`) + `export_controlled_exchange()` | Strictly isolated from Finland server (`Main Hermes` / `Hamzad Core`). |
| **Hamzad Core (First-Class)** | `AGENTS.md` + `ExternalMemoryService` protocol | `molavi-agentic-os` `second-brain-memory` & `tm-agent-orchestration` skill format | `HamzadBridge` (`sync_episodes_to_vault`, `recall_for_session`, `push_memory_to_hamzad_kv`, `record_orchestration_event`) | Separate from `MainHermesAdapter`; never duplicates `MemoryService` or alters prod DBs. |
| **Claude Code** | `CLAUDE.md` (1-line pointer to `AGENTS.md`) | `.claude/skills/<name>/SKILL.md` | `.mcp.json` stdio entry | Respect 10 KB hook output cap. |
| **OpenAI Codex** | `AGENTS.md` (native root discovery) | `.agents/skills/<name>/SKILL.md` | `.codex/` / stdio MCP | Keep `AGENTS.md` < 22 KB (Codex truncates ~32 KiB). |
| **Gemini CLI** | `.gemini/settings.json` (`context.fileName: AGENTS.md`) | `.gemini/commands/*.toml` wrappers | `.gemini/settings.json` MCP config | Windows/Linux/macOS safe paths. |
| **OpenCode** | `AGENTS.md` | `.opencode/skills/<name>/SKILL.md` | `opencode.json` MCP entry | Standard Agent Skills spec. |
| **Goose** | `.goosehints` / `AGENTS.md` | Standard `SKILL.md` | Goose stdio MCP extension (`tm-brain mcp`) | Zero proprietary Goose SDK dependency in core. |
| **Antigravity** | `AGENTS.md` (kept < 22 KB) | `.agents/skills/<name>/SKILL.md` | Stdio MCP config | Respect ~24 KB `AGENTS.md` limit. |
| **Obsidian 1.12+** | Native vault root | `.md`, `.base`, `.canvas` + optional `obsidian` CLI | Optional CLI bridge | Vault remains 100% usable without Obsidian running. |

---

## 4. MCP Tool Surface Contract (Agent-Agnostic)

When exposed over stdio MCP (`tm-brain mcp`), all harnesses call the same typed tools:
1. `memory_search(query, project?, limit?)` → `SearchResult[]` (privacy-filtered).
2. `memory_recall(project?, platforms?, limit?)` → `MemoryRecord[]` (project-isolated, privacy-filtered).
3. `memory_expand(memory_id, depth?)` → linked neighbors + backlinks.
4. `memory_remember(title, body, scope, projects?, platforms?, confidence?, verification?)` → `MemoryWriteResult`.
5. `memory_correct(target_id, new_title, new_body, reason, confidence?, verification?)` → `MemoryWriteResult`.
6. `memory_health()` → vault & index diagnostics.
