"""Hermes adapters: Main Hermes (production/Hamzad-integrated) and Hermes Personal Desktop (Mac local)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.models import ConfidenceLevel, MemoryRecord, MemoryScope, SearchQuery
from ..memory.markdown_store import MarkdownMemoryStore, atomic_write_text


@dataclass(frozen=True)
class HermesEnvironmentConfig:
    """Independent runtime configuration for a Hermes environment."""

    environment_id: str  # e.g. "main-hermes" | "hermes-personal-desktop"
    execution_host: str  # e.g. "finland-server" | "mac-local"
    namespace_prefix: str
    allow_cross_env_read: bool = False


class BaseHermesAdapter:
    """Shared MemoryInterface + HarnessAdapter implementation isolated by HermesEnvironmentConfig."""

    def __init__(self, store: MarkdownMemoryStore, config: HermesEnvironmentConfig) -> None:
        self.store = store
        self.config = config

    @property
    def harness_name(self) -> str:
        return self.config.environment_id

    def _env_tag(self) -> str:
        return f"env:{self.config.environment_id}"

    def _host_tag(self) -> str:
        return f"host:{self.config.execution_host}"

    def _scoped_project(self, session_id: str) -> str:
        return f"{self.config.namespace_prefix}:{session_id}"

    # --- MemoryInterface ---

    def store_episode(self, session_id: str, agent_id: str, entry: dict[str, Any]) -> None:
        """Persist an episode strictly isolated to this Hermes environment."""
        title = str(entry.get("title") or f"{self.config.environment_id} episode {session_id}")
        body = str(entry.get("content") or json.dumps(entry, ensure_ascii=False))
        project = self._scoped_project(str(entry.get("project") or session_id))
        self.store.remember(
            title,
            body,
            scope=MemoryScope.PROJECT,
            projects=[project],
            confidence=ConfidenceLevel.INFERRED,
            source_agent=f"{self.config.environment_id}:{agent_id}",
            origin=f"{self.config.execution_host}:{session_id}",
            tags=[self._env_tag(), self._host_tag(), f"session:{session_id}"],
        )

    def get_episodes(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve non-private episodes strictly within this Hermes environment."""
        project = self._scoped_project(session_id)
        records = self.store.recall(project=project, include_private=False, limit=limit)
        env_records = [r for r in records if self._env_tag() in r.tags]
        return [
            {
                "environment": self.config.environment_id,
                "host": self.config.execution_host,
                "agent_id": r.provenance.source_agent,
                "entry": {
                    "id": r.id,
                    "title": r.title,
                    "content": self.store.privacy.redact(r.body),
                    "tags": r.tags,
                },
                "created_at": r.provenance.created_at,
            }
            for r in env_records
        ]

    def set_key(self, namespace: str, key: str, value: Any) -> None:
        """Store a namespaced key-value fact isolated to this Hermes environment."""
        scoped_ns = self._scoped_project(namespace)
        title = f"kv:{scoped_ns}:{key}"
        body = json.dumps(
            {
                "environment": self.config.environment_id,
                "namespace": namespace,
                "key": key,
                "value": value,
            },
            ensure_ascii=False,
        )
        existing = self.store.search(
            SearchQuery(text=title, project=scoped_ns, include_private=False, limit=5)
        )
        exact = next(
            (h.record for h in existing if h.record.title == title and self._env_tag() in h.record.tags),
            None,
        )
        if exact is not None:
            self.store.correct(
                exact.id,
                title,
                body,
                reason=f"Updated key {namespace}:{key}",
                confidence=ConfidenceLevel.VERIFIED,
                verification=f"{self.config.environment_id} KV update",
                source_agent=self.config.environment_id,
            )
        else:
            self.store.remember(
                title,
                body,
                scope=MemoryScope.PROJECT,
                projects=[scoped_ns],
                confidence=ConfidenceLevel.VERIFIED,
                verification=f"{self.config.environment_id} KV set",
                source_agent=self.config.environment_id,
                origin=self.config.execution_host,
                tags=[self._env_tag(), self._host_tag(), "hermes-kv", namespace],
            )

    def get_key(self, namespace: str, key: str) -> Any | None:
        """Retrieve a namespaced key-value fact from this Hermes environment only."""
        scoped_ns = self._scoped_project(namespace)
        title = f"kv:{scoped_ns}:{key}"
        for rec in self.store.recall(project=scoped_ns, include_private=False, limit=100):
            if rec.title == title and self._env_tag() in rec.tags:
                try:
                    return json.loads(rec.body).get("value")
                except json.JSONDecodeError:
                    return rec.body
        return None

    # --- HarnessAdapter ---

    def render_instructions(self, vault_root: Path) -> str:
        """Render environment-specific Hermes instructions."""
        return (
            f"# {self.config.environment_id} — TM Second Brain\n\n"
            f"- Execution Host: `{self.config.execution_host}`\n"
            f"- Vault Root: `{vault_root}`\n"
            "- Operating Contract: Read `AGENTS.md` at vault root.\n"
            f"- MCP Server: `python3 -m tm_second_brain.cli --vault {vault_root} mcp`\n"
        )

    def export_skill(self, skill_name: str, skill_markdown: str, out_dir: Path) -> Path:
        """Export a skill in Hermes-compatible SKILL.md + hermes_agent.json format."""
        skill_dir = out_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        atomic_write_text(skill_path, skill_markdown)
        manifest_path = skill_dir / "hermes_agent.json"
        atomic_write_text(
            manifest_path,
            json.dumps(
                {
                    "hermes_agent_version": "1.0",
                    "environment": self.config.environment_id,
                    "execution_host": self.config.execution_host,
                    "id": skill_name,
                    "skill_file": "SKILL.md",
                    "mcp_server": "tm-second-brain",
                },
                indent=2,
            )
            + "\n",
        )
        return skill_path

    def build_mcp_config(self, vault_root: Path) -> dict[str, Any]:
        """Build an independent MCP server configuration for this Hermes environment."""
        return {
            "mcpServers": {
                "tm-second-brain": {
                    "command": "python3",
                    "args": ["-m", "tm_second_brain.cli", "--vault", str(vault_root), "mcp"],
                    "env": {
                        "TM_BRAIN_ENV": self.config.environment_id,
                        "TM_BRAIN_HOST": self.config.execution_host,
                    },
                }
            }
        }


class MainHermesAdapter(BaseHermesAdapter):
    """Dedicated adapter for Main Hermes (production server integrated with Hamzad)."""

    def __init__(self, store: MarkdownMemoryStore) -> None:
        super().__init__(
            store,
            HermesEnvironmentConfig(
                environment_id="main-hermes",
                execution_host="finland-server",
                namespace_prefix="main-hermes",
                allow_cross_env_read=False,
            ),
        )


class HermesPersonalDesktopFinlandAdapter(BaseHermesAdapter):
    """Dedicated adapter for Hermes Personal Desktop on the Finland server."""

    def __init__(self, store: MarkdownMemoryStore) -> None:
        super().__init__(
            store,
            HermesEnvironmentConfig(
                environment_id="hermes-personal-desktop-finland",
                execution_host="finland-server",
                namespace_prefix="desktop-finland",
                allow_cross_env_read=False,
            ),
        )

    def export_controlled_exchange(self, project: str, limit: int = 20) -> list[dict[str, Any]]:
        """Explicitly export redacted, non-private memories for controlled cross-env exchange."""
        scoped = self._scoped_project(project)
        records: list[MemoryRecord] = self.store.recall(
            project=scoped, include_private=False, limit=limit
        )
        return [
            {
                "source_environment": self.config.environment_id,
                "source_host": self.config.execution_host,
                "id": r.id,
                "title": r.title,
                "body": self.store.privacy.redact(r.body),
                "confidence": r.confidence.value,
                "tags": [t for t in r.tags if not t.startswith(("env:", "host:"))],
            }
            for r in records
            if self._env_tag() in r.tags
        ]


class HermesPersonalDesktopMacAdapter(BaseHermesAdapter):
    """Dedicated adapter for Hermes Personal Desktop on Mac local execution."""

    def __init__(self, store: MarkdownMemoryStore) -> None:
        super().__init__(
            store,
            HermesEnvironmentConfig(
                environment_id="hermes-personal-desktop-mac",
                execution_host="mac-local",
                namespace_prefix="desktop-mac",
                allow_cross_env_read=False,
            ),
        )

    def export_controlled_exchange(self, project: str, limit: int = 20) -> list[dict[str, Any]]:
        """Explicitly export redacted, non-private memories for controlled cross-env exchange."""
        scoped = self._scoped_project(project)
        records: list[MemoryRecord] = self.store.recall(
            project=scoped, include_private=False, limit=limit
        )
        return [
            {
                "source_environment": self.config.environment_id,
                "source_host": self.config.execution_host,
                "id": r.id,
                "title": r.title,
                "body": self.store.privacy.redact(r.body),
                "confidence": r.confidence.value,
                "tags": [t for t in r.tags if not t.startswith(("env:", "host:"))],
            }
            for r in records
            if self._env_tag() in r.tags
        ]


# Backward-compatible aliases
HermesPersonalDesktopAdapter = HermesPersonalDesktopMacAdapter
HermesMemoryAdapter = MainHermesAdapter
