# AGENTS.md — TM Second Brain Operating Contract

> Shared agent-agnostic instructions for Claude Code, OpenAI Codex, Gemini CLI, OpenCode, Hermes, Goose, and Antigravity.

## 1. Prime Rules
1. **Markdown is canonical.** Durable knowledge, goals, project logs, and memories live in Markdown + YAML frontmatter. SQLite indexes are rebuildable caches.
2. **Respect privacy boundaries.** Never read `private: true` notes or `private_paths` unless explicitly requested by the user for that private context; never send them to external APIs or cross-repo MCP responses.
3. **Never silently overwrite corrections.** Use supersede semantics (`supersedes` / `superseded_by`) so correction history is preserved.
4. **Human approval for rule/skill mutations (L2).** Log repeated corrections to `FEEDBACK.md` as L1 proposals; do not alter `SKILL.md` or `AGENTS.md` without explicit user approval.
5. **Preserve user data.** Never modify existing Hamzad or Hermes production installations or overwrite user content folders during upgrades.
