"""Coding agent harness adapters (Codex, Claude Code, Gemini CLI, OpenCode, Goose, Antigravity)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..memory.markdown_store import atomic_write_text

_ANTIGRAVITY_MAX_BYTES = 22_000


@dataclass(frozen=True)
class HarnessSpec:
    """Declarative specification for a coding agent harness."""

    name: str
    instruction_file: str
    skills_dir: str
    mcp_config_path: str
    max_instruction_bytes: int | None = None
    command_toml_dir: str | None = None


HARNESS_SPECS: dict[str, HarnessSpec] = {
    "codex": HarnessSpec(
        name="codex",
        instruction_file="AGENTS.md",
        skills_dir=".agents/skills",
        mcp_config_path=".codex/mcp.json",
        max_instruction_bytes=22_000,
    ),
    "claude-code": HarnessSpec(
        name="claude-code",
        instruction_file="CLAUDE.md",
        skills_dir=".claude/skills",
        mcp_config_path=".mcp.json",
    ),
    "gemini-cli": HarnessSpec(
        name="gemini-cli",
        instruction_file=".gemini/settings.json",
        skills_dir=".agents/skills",
        mcp_config_path=".gemini/settings.json",
        command_toml_dir=".gemini/commands",
    ),
    "opencode": HarnessSpec(
        name="opencode",
        instruction_file="AGENTS.md",
        skills_dir=".opencode/skills",
        mcp_config_path="opencode.json",
    ),
    "goose": HarnessSpec(
        name="goose",
        instruction_file=".goosehints",
        skills_dir=".agents/skills",
        mcp_config_path=".goose/mcp.json",
    ),
    "antigravity": HarnessSpec(
        name="antigravity",
        instruction_file="AGENTS.md",
        skills_dir=".agents/skills",
        mcp_config_path=".antigravity/mcp.json",
        max_instruction_bytes=_ANTIGRAVITY_MAX_BYTES,
    ),
}


class GenericHarnessAdapter:
    """Data-driven HarnessAdapter supporting all 6 target coding agents."""

    def __init__(self, spec: HarnessSpec) -> None:
        self.spec = spec

    @property
    def harness_name(self) -> str:
        return self.spec.name

    def render_instructions(self, vault_root: Path) -> str:
        """Render harness-appropriate instruction file content."""
        if self.spec.name == "claude-code":
            return "@AGENTS.md\n"
        if self.spec.name == "gemini-cli":
            return json.dumps(
                {
                    "context": {"fileName": ["AGENTS.md"]},
                    "mcpServers": self.build_mcp_config(vault_root)["mcpServers"],
                },
                indent=2,
            ) + "\n"
        if self.spec.name == "goose":
            return (
                "# Goose Second Brain Hints\n"
                f"Vault: {vault_root}\n"
                "Read `AGENTS.md` at the vault root before modifying notes or memories.\n"
            )
        content = (
            f"# {self.spec.name} — TM Second Brain\n\n"
            f"Vault Root: `{vault_root}`\n"
            "Read `AGENTS.md` for memory, privacy, and approval rules.\n"
        )
        if self.spec.max_instruction_bytes:
            encoded = content.encode("utf-8")
            if len(encoded) > self.spec.max_instruction_bytes:
                content = encoded[: self.spec.max_instruction_bytes].decode("utf-8", errors="ignore")
        return content

    def export_skill(self, skill_name: str, skill_markdown: str, out_dir: Path) -> Path:
        """Export a standard SKILL.md (and TOML command wrapper for Gemini CLI)."""
        skill_dir = out_dir / self.spec.skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        atomic_write_text(skill_path, skill_markdown)

        if self.spec.command_toml_dir:
            toml_dir = out_dir / self.spec.command_toml_dir
            toml_dir.mkdir(parents=True, exist_ok=True)
            toml_path = toml_dir / f"{skill_name}.toml"
            atomic_write_text(
                toml_path,
                f'description = "Run {skill_name} skill"\nprompt = """\nFollow {self.spec.skills_dir}/{skill_name}/SKILL.md\n"""\n',
            )
        return skill_path

    def build_mcp_config(self, vault_root: Path) -> dict[str, Any]:
        """Build stdio MCP configuration for this harness."""
        server_entry = {
            "command": "python3",
            "args": ["-m", "tm_second_brain.cli", "--vault", str(vault_root), "mcp"],
        }
        if self.spec.name == "goose":
            return {
                "extensions": {
                    "tm-second-brain": {
                        "type": "stdio",
                        "cmd": server_entry["command"],
                        "args": server_entry["args"],
                    }
                }
            }
        return {"mcpServers": {"tm-second-brain": server_entry}}


def get_harness_adapter(name: str) -> GenericHarnessAdapter:
    """Return a HarnessAdapter by canonical harness name."""
    key = name.strip().lower()
    if key not in HARNESS_SPECS:
        supported = ", ".join(sorted(HARNESS_SPECS))
        raise KeyError(f"Unknown harness '{name}'. Supported: {supported}")
    return GenericHarnessAdapter(HARNESS_SPECS[key])


def list_harnesses() -> list[str]:
    """Return sorted list of supported coding agent harness names."""
    return sorted(HARNESS_SPECS)
