# License & Attribution Audit

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Target License:** MIT License  
> **Phase:** Phase 1 — Repository & License Audit  
> **Date:** 2026-11-12

---

## 1. Audit Summary

All five reference repositories were inspected for root `LICENSE` files, nested `LICENSE*` files, `NOTICE.md` files, and inline attribution headers in source code.

| Repository | Root License | Copyright Holder(s) | Nested / Bundled Licenses | MIT Compatibility | Action for `tm-second-brain` |
|---|---|---|---|---|---|
| `kepano/obsidian-skills` | **MIT** | `Copyright (c) 2026 Steph Ango (@kepano)` | `plugins/obsidian/LICENSE` (MIT, same) | **Compatible** | Attribute in `THIRD_PARTY_NOTICES.md` & `SOURCES.md`; reference Obsidian specs. |
| `breferrari/obsidian-mind` | **MIT** | `Copyright (c) 2026 Brenno Ferrari` | None found | **Compatible** | Attribute in `THIRD_PARTY_NOTICES.md` & `SOURCES.md`; reimplement epistemic & MCP concepts originally in Python. |
| `ballred/obsidian-claude-pkm` | **MIT** | `Copyright (c) 2024 Obsidian Claude PKM Contributors` | None found | **Compatible** | Attribute in `THIRD_PARTY_NOTICES.md` & `SOURCES.md`; adapt goal-cascade & BYOV concepts. |
| `heyitsnoah/claudesidian` | **MIT** | `Copyright (c) 2025 Noah Brier / Alephic` | 1. `.claude/skills/LICENSE-kepano` (MIT, Steph Ango)<br>2. `.agents/skills/skill-creator/LICENSE.txt` (**Apache-2.0**) + `NOTICE.md` (`anthropics/skills`) | **MIT core compatible; Apache-2.0 sub-component requires isolation** | **Do NOT copy** `skill-creator` (Apache-2.0) into `tm-second-brain`. Attribute `claudesidian` (MIT) in `SOURCES.md` & `THIRD_PARTY_NOTICES.md`. |
| `louisfb01/obsidian-agent-vault-template` | **MIT** | `Copyright (c) 2026 Louis-François Bouchard` | Inline attribution in `AGENT-RULES.md` to `eugeniughelbur/obsidian-second-brain` (`AI-FIRST.md`) and in `skill_health.py` to `warpdotdev/common-skills` (MIT) | **Compatible** | Attribute in `THIRD_PARTY_NOTICES.md` & `SOURCES.md` (including upstream `AI-FIRST.md` and `warpdotdev/common-skills` references). |

---

## 2. Detailed Findings & Compliance Rules

### 2.1 Why `tm-second-brain` Can Safely Use the MIT License
1. **Clean-Room Original Core:** All Python modules, schemas, CLI commands, retrieval engines, privacy filters, and adapters in `tm-second-brain` will be authored originally under the **MIT License** (`Copyright (c) 2026 Taqi Molavi (tmolavi)`).
2. **Avoidance of Apache-2.0 / Non-MIT Contamination:** During the audit of `heyitsnoah/claudesidian`, we discovered a nested Apache-2.0 component (`.agents/skills/skill-creator/LICENSE.txt` and `NOTICE.md` from `anthropics/skills`). While Apache-2.0 is permissive, mixing verbatim Apache-2.0 files into an MIT repository requires carrying Apache-2.0 license text, `NOTICE` propagation, and modified-file notices. `tm-second-brain` **excludes** `skill-creator` completely to keep the entire repository cleanly MIT-licensed.
3. **Preservation of Attribution:** In accordance with `TM-OPEN-SOURCE-STANDARD.md` §6 and MIT license terms:
   - `THIRD_PARTY_NOTICES.md` records all referenced/adapted projects, copyright holders, and licenses.
   - `SOURCES.md` documents architectural inspiration and conceptual lineage.

### 2.2 Optional External Dependencies & Model Providers
`tm-second-brain` core runs on **Python 3.10+ standard library only** (zero mandatory third-party packages). Optional integrations remain decoupled behind adapters:

| Optional Dependency / Tool | License | Integration Mechanism | Bundled? |
|---|---|---|---|
| Python 3.10+ Standard Library (`sqlite3`, `json`, `pathlib`, `re`, `hashlib`, `argparse`, `http`) | PSF License | Core runtime | System runtime |
| Obsidian 1.12+ / Obsidian CLI | Proprietary (free personal use) | Optional CLI / file-format interop (`.md`, `.base`, `.canvas`) | No |
| `@tobilu/qmd` | MIT | Optional subprocess / MCP retrieval backend | No |
| Ollama (local open-weight models/embeddings) | MIT | Optional local HTTP adapter (`localhost:11434`) | No |
| Google Gemini Free Tier / Groq Free Tier | Proprietary API (Free Tier) | Optional user-configured provider adapter | No |
| `pytest` / `ruff` (dev/test only) | MIT | Dev dependencies (`pyproject.toml` `[project.optional-dependencies]`) | No |

---

## 3. Compliance Gate for Implementation

Before any release or PR merge:
1. Every new file authored for `tm-second-brain` is original MIT work.
2. No verbatim files from Apache-2.0, GPL, or proprietary repositories may be copied into the repository.
3. Any optional third-party dependency added to `pyproject.toml` must be MIT/BSD/Apache-2.0/ISC compatible and documented in `THIRD_PARTY_NOTICES.md` and `MODEL-REQUIREMENTS.md`.
