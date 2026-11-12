# Third-Party Notices

`tm-second-brain` is an original open-source project licensed under the MIT License (`Copyright (c) 2026 Taqi Molavi (tmolavi)`).

This project studies, references, and/or interoperates with concepts and specifications from the following upstream open-source works. All upstream copyrights and licenses are acknowledged and preserved below. See [`LICENSE-AUDIT.md`](LICENSE-AUDIT.md) for the full compatibility audit.

---

## 1. Referenced & Studied Upstream Projects

### `kepano/obsidian-skills`
* **Repository:** <https://github.com/kepano/obsidian-skills>
* **License:** MIT License
* **Copyright:** `Copyright (c) 2026 Steph Ango (@kepano)`
* **Usage:** Agent Skills specification alignment and Obsidian `.md` / `.base` / `.canvas` format interoperability.

### `breferrari/obsidian-mind`
* **Repository:** <https://github.com/breferrari/obsidian-mind>
* **License:** MIT License
* **Copyright:** `Copyright (c) 2026 Brenno Ferrari`
* **Usage:** Architectural inspiration for epistemic memory contracts (`confidence`, `scope`, `origin`, supersede-on-correction), `vault-manifest.json` upgrade separation, and cross-repo MCP tool surfaces. Reimplemented originally in Python.

### `ballred/obsidian-claude-pkm`
* **Repository:** <https://github.com/ballred/obsidian-claude-pkm>
* **License:** MIT License
* **Copyright:** `Copyright (c) 2024 Obsidian Claude PKM Contributors`
* **Usage:** Inspiration for the 3-Year → Yearly → Monthly → Weekly → Daily goal cascade and Bring-Your-Own-Vault (`/adopt`) / safe `/upgrade` workflows.

### `heyitsnoah/claudesidian`
* **Repository:** <https://github.com/heyitsnoah/claudesidian>
* **License:** MIT License
* **Copyright:** `Copyright (c) 2025 Noah Brier / Alephic`
* **Usage:** Inspiration for PARA vault organization, Thinking vs. Writing modes, and `.agents/skills/` canonical skill layout. (Note: `claudesidian` bundles `anthropics/skills/skill-creator` under Apache-2.0, which is **not** included in `tm-second-brain`.)

### `louisfb01/obsidian-agent-vault-template`
* **Repository:** <https://github.com/louisfb01/obsidian-agent-vault-template>
* **License:** MIT License
* **Copyright:** `Copyright (c) 2026 Louis-François Bouchard`
* **Usage:** Inspiration for `AGENT-RULES.md`, `FEEDBACK.md` skill self-improvement loops, `working-dir/agent-log/`, `index.md` + `progress-log.md` project resumability, and session health scanning.
* **Upstream Attributions Noted in `obsidian-agent-vault-template`:**
  * `eugeniughelbur/obsidian-second-brain` (`AI-FIRST.md` note specification)
  * `warpdotdev/common-skills` (`skill-doctor` concepts, MIT License)

---

## 2. Optional Runtime Integrations (Not Bundled)

* **Python 3.10+ Standard Library** — PSF License
* **QMD (`@tobilu/qmd`)** — MIT License (optional local semantic search)
* **Ollama** — MIT License (optional local open-weight embeddings/models)
* **Obsidian 1.12+** — Optional desktop/CLI companion
