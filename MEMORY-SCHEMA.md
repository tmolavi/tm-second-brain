# Memory Schema (`MEMORY-SCHEMA.md`)

> **Project:** `tm-second-brain` (`tmolavi/tm-second-brain`)  
> **Phase:** Phase 3 — Interfaces & Integration Contracts

---

## 1. Memory Identity

* **Format:** `mem_<YYYYMMDD>_<12-hex-sha256>` (deterministic or UUID4-backed unique ID).
* **Filename Slug:** Windows-safe slug (max 60 chars, strips `..`, `/`, `\`, control chars, trailing dots, and rewrites Windows reserved stems `CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`).
* **Canonical Storage Path:**
  * Project-scoped: `<vault>/memories/projects/<project_slug>/<id>__<slug>.md`
  * Platform-scoped: `<vault>/memories/platform/<id>__<slug>.md`
  * General-scoped: `<vault>/memories/general/<id>__<slug>.md`

---

## 2. Canonical Markdown + YAML Frontmatter Schema

```yaml
---
id: mem_20261112_8f3a1c9b2e10
title: "Use atomic temp-file rename for vault writes"
status: active                # draft | active | superseded | archived
version: 1                    # monotonically incremented on correction chain
scope: project                # general | platform | project
projects:
  - tm-second-brain
platforms:
  - python
confidence: verified          # verified | inferred | unverified
verification: "Verified across Linux/Windows path tests"
source_agent: hermes          # claude-code | codex | gemini | opencode | hermes | goose | antigravity | human
origin: "tm-second-brain"     # derived server/CLI-side
created_at: "2026-11-12T06:30:00Z"
updated_at: "2026-11-12T06:30:00Z"
supersedes: null              # previous memory ID in correction chain
superseded_by: null           # newer memory ID if superseded
private: false                # true => excluded from cross-repo MCP & external APIs
tags:
  - storage
  - reliability
links:
  - "[[ARCHITECTURE]]"
---

Body of the memory in Obsidian Flavored Markdown.
```

---

## 3. Provenance, Versioning & Conflict Resolution

1. **Provenance:** Every record captures `source_agent`, `origin`, `verification`, `created_at`, and `updated_at`.
2. **Versioning & Correction History:**
   * Correcting `mem_A` creates `mem_B` with `version = mem_A.version + 1` and `supersedes = mem_A.id`.
   * `mem_A` is updated in place **only** for lifecycle metadata: `status = superseded`, `superseded_by = mem_B.id`, `updated_at = now`.
   * An immutable append-only JSONL record is written to `<vault>/.tm-brain/corrections.jsonl` (`timestamp`, `old_id`, `new_id`, `reason`, `source_agent`).
3. **Conflict Detection:**
   * On `remember()`, active memories in the same `(scope, projects)` slice are compared by normalized title/token Jaccard similarity ($\ge 0.55$ threshold).
   * Potential conflicts are returned in `MemoryWriteResult.conflicts` rather than silently overwriting.

---

## 4. Project-Scoped Memory Isolation

| Query `project` | `scope: project` | `scope: platform` | `scope: general` |
|---|---|---|---|
| `"alpha"` | Returned **only if** `"alpha" in record.projects` | Returned if `platforms` intersects (or unspecified) | Returned |
| `None` (global/vault) | Returned | Returned | Returned |

* A memory with `scope: project` and `projects: ["alpha"]` **never leaks** into a `recall(project="beta")` or `search(SearchQuery(..., project="beta"))` call.

---

## 5. Privacy & Sensitive-Data Exclusion

1. **Private Flag & Paths:** Any record with `private: true` or residing under configured `private_paths` (default: `Areas/Personal/`, `private/`) is excluded from `recall()`/`search()` unless `include_private=True` is explicitly requested by the local owner.
2. **Secret Redaction:** Before writing logs or exporting non-private bundles, `PrivacyPolicy.redact(text)` scrubs `sk-*`, `ghp_*`, `AIza*`, `xoxb-*`, `-----BEGIN ... PRIVATE KEY-----`, and bearer tokens.

---

## 6. Five-Language Documentation Structure

Per `TM-OPEN-SOURCE-STANDARD.md` §3, documentation is maintained across five synchronized languages:
* `README.md` — English (canonical primary)
* `docs/fa/README.md` — فارسی (Persian)
* `docs/tr/README.md` — Türkçe (Istanbul Turkish)
* `docs/az/README.md` — Azərbaycan dili (Azerbaijani Turkish)
* `docs/ar/README.md` — العربية (Arabic)

Every localized `README.md` mirrors the same sections (Overview, Features, Installation, CLI Quickstart, Architecture Summary, Model Requirements, License) while keeping CLI commands, identifiers, and paths in English.
