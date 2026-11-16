# TM Second Brain — Complete User & Integration Guide (`en`)

> [README](../../README.md) · [فارسی](../fa/GUIDE.md) · [Türkçe](../tr/GUIDE.md) · [Azərbaycan dili](../az/GUIDE.md) · [العربية](../ar/GUIDE.md)

---

## 1. Installation Instructions

```bash
git clone https://github.com/tmolavi/tm-second-brain.git
cd tm-second-brain
python3 -m pip install -e .
```

Zero mandatory external dependencies. Works on **Linux, macOS, and Windows** with Python 3.10+.

## 2. Configuration

Initialize a vault with one of the three starter templates (`personal-knowledge`, `business-project`, `developer-agent`):

```bash
tm-brain --vault ./my-vault init --template developer-agent
```

Optional semantic adapters (`QMDRetrievalAdapter`, `OllamaRetrievalAdapter`) are **disabled by default** and never install runtimes or model weights.

## 3. Architecture

1. **Layer 1 (Canonical Storage):** Markdown + YAML frontmatter + wikilinks under `memories/`, `working-dir/agent-log/`, and rebuildable SQLite FTS5 cache `.tm-brain/index.db` (WAL mode).
2. **Layer 2 (Pure Python Core):** Memory lifecycle (`draft` → `active` → `superseded` → `archived`), provenance, conflict detection, project/environment isolation, BM25 + graph hybrid retrieval, L1→L2 learning gate, and SHA-256 backup/restore.
3. **Layer 3 (Adapters & Orchestration):** Obsidian, stdio MCP (`tm-brain mcp`), coding agents (`codex`, `claude-code`, `gemini-cli`, `opencode`, `goose`, `antigravity`), portable orchestration (`tm-agent-orchestration`), and four isolated TM targets (`hamzad-core`, `main-hermes`, `hermes-personal-desktop-finland`, `hermes-personal-desktop-mac`).

## 4. Usage Examples

```bash
tm-brain --vault ./my-vault remember --title "WAL Mode" --body "Enable SQLite WAL." --project core --confidence verified --verification "pytest"
tm-brain --vault ./my-vault search "WAL" --project core
tm-brain --vault ./my-vault correct mem_20261112_abc123 --title "WAL Mode" --body "Enable WAL + synchronous=NORMAL." --reason "Throughput tuning"
tm-brain --vault ./my-vault orchestrate list
tm-brain --vault ./my-vault orchestrate status sess_001
tm-brain --vault ./my-vault learn log --skill code-review --outcome missed --rule "Check empty inputs"
tm-brain --vault ./my-vault learn scan --min-occurrences 2
tm-brain --vault ./my-vault backup ./backup.tar.gz
```

## 5. Agent Integrations

```bash
tm-brain --vault ./my-vault install-adapter codex
tm-brain --vault ./my-vault install-adapter claude-code
tm-brain --vault ./my-vault install-adapter gemini-cli
tm-brain --vault ./my-vault mcp
```

## 6. Security & Privacy

* Notes with `private: true` or under `private_paths` (`Areas/Personal/`, `02_Areas/Personal/`, `memories/private/`) are excluded from MCP, cross-environment sync, and default exports.
* Known API keys and tokens (`sk-*`, `ghp_*`, `AIza*`, `xoxb-*`, private keys) are automatically redacted.
* `restore_backup(..., overwrite=True)` creates a `pre-restore-*.tar.gz` safety snapshot before overwriting.

## 7. Troubleshooting

* **No search results:** Check `--project` isolation; memories with `scope: project` only match their declared `projects`.
* **Windows filename errors:** `sanitize_slug` automatically rewrites reserved stems (`CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`).

## 8. Contribution Guidelines

See [`CONTRIBUTING.md`](../../CONTRIBUTING.md). All contributions must remain MIT-compatible, zero-runtime-dependency in core, cross-platform, and covered by `pytest`.
