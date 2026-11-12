"""Integration, mock-adapter, environment isolation, and security tests for Phase 5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tm_second_brain.adapters.hamzad import HamzadBridge
from tm_second_brain.adapters.harnesses import get_harness_adapter, list_harnesses
from tm_second_brain.adapters.hermes import (
    HermesPersonalDesktopAdapter,
    MainHermesAdapter,
)
from tm_second_brain.adapters.mcp_server import MCPServer
from tm_second_brain.adapters.obsidian import ObsidianAdapter
from tm_second_brain.cli import main as cli_main
from tm_second_brain.core.models import MemoryScope
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore


class FakeHamzadMemoryService:
    """In-memory mock of Hamzad MemoryService / molavi-agentic-os MemoryInterface."""

    def __init__(self) -> None:
        self.episodes: dict[str, list[dict[str, Any]]] = {}
        self.kv: dict[tuple[str, str], Any] = {}

    def store_episode(self, session_id: str, agent_id: str, entry: dict[str, Any]) -> None:
        self.episodes.setdefault(session_id, []).append(
            {"agent_id": agent_id, "entry": entry, "created_at": 1700000000.0}
        )

    def get_episodes(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return list(self.episodes.get(session_id, []))[-limit:]

    def set_key(self, namespace: str, key: str, value: Any) -> None:
        self.kv[(namespace, key)] = value

    def get_key(self, namespace: str, key: str) -> Any | None:
        return self.kv.get((namespace, key))


# --- P5-01: Obsidian Adapter ---


def test_obsidian_adapter_safe_rw_and_backup(tmp_path: Path) -> None:
    obs = ObsidianAdapter(tmp_path)
    first = obs.write_markdown("notes/Guide.md", "Initial [[Home]] link.", {"tags": ["guide"]})
    assert first["backup"] is None

    second = obs.write_markdown("notes/Guide.md", "Updated [[Home]] and [[API]].", {"tags": ["guide"], "custom": "keep"})
    assert second["backup"] is not None
    assert Path(second["backup"]).exists()

    read_back = obs.read_markdown("notes/Guide.md")
    assert read_back["frontmatter"]["custom"] == "keep"
    assert read_back["wikilinks"] == ["Home", "API"]


def test_obsidian_adapter_bases_canvas_and_traversal_block(tmp_path: Path) -> None:
    obs = ObsidianAdapter(tmp_path)
    (tmp_path / "View.base").write_text("views:\n  - type: table\n", encoding="utf-8")
    obs.write_canvas("Map.canvas", {"nodes": [{"id": "n1", "type": "text", "text": "Hi"}], "edges": []})

    special = obs.list_special_files()
    assert special["bases"] == ["View.base"]
    assert special["canvases"] == ["Map.canvas"]
    assert "views:" in obs.read_base("View.base")
    assert len(obs.read_canvas("Map.canvas")["nodes"]) == 1

    with pytest.raises(ValueError):
        obs.read_markdown("../escape.md")
    with pytest.raises(ValueError):
        obs.write_markdown("/tmp/abs.md", "blocked")


# --- P5-02 & Amendment: Main Hermes vs Hermes Personal Desktop Isolation ---


def test_hermes_environment_isolation(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    main_hermes = MainHermesAdapter(store)
    desktop_hermes = HermesPersonalDesktopAdapter(store)

    main_hermes.store_episode("sess-1", "prod-agent", {"title": "Prod deploy rule", "content": "Finland server only."})
    main_hermes.set_key("ops", "region", "finland")

    desktop_hermes.store_episode("sess-1", "mac-agent", {"title": "Mac note", "content": "Local personal workflow."})
    desktop_hermes.set_key("ops", "region", "mac-local")

    main_eps = main_hermes.get_episodes("sess-1")
    desk_eps = desktop_hermes.get_episodes("sess-1")
    assert len(main_eps) == 1
    assert main_eps[0]["environment"] == "main-hermes"
    assert main_eps[0]["host"] == "finland-server"
    assert len(desk_eps) == 1
    assert desk_eps[0]["environment"] == "hermes-personal-desktop-mac"
    assert desk_eps[0]["host"] == "mac-local"

    assert main_hermes.get_key("ops", "region") == "finland"
    assert desktop_hermes.get_key("ops", "region") == "mac-local"

    skill_path = desktop_hermes.export_skill("daily-sync", "# Daily Sync", tmp_path / "hermes-skills")
    manifest = json.loads((skill_path.parent / "hermes_agent.json").read_text(encoding="utf-8"))
    assert manifest["environment"] == "hermes-personal-desktop-mac"
    assert manifest["execution_host"] == "mac-local"


def test_hermes_desktop_controlled_exchange_privacy(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    desktop = HermesPersonalDesktopAdapter(store)
    desktop.store_episode(
        "proj-x",
        "mac-agent",
        {"title": "Shareable tip", "content": "Key is sk-1234567890abcdef1234567890."},
    )
    # Directly store a private memory tagged for desktop
    store.remember(
        "Private desktop secret",
        "Must never be exported.",
        scope=MemoryScope.PROJECT,
        projects=["desktop-mac:proj-x"],
        private=True,
        tags=["env:hermes-personal-desktop-mac"],
    )

    exported = desktop.export_controlled_exchange("proj-x")
    assert len(exported) == 1
    assert "[REDACTED_API_KEY]" in exported[0]["body"]
    assert "sk-1234567890abcdef1234567890" not in exported[0]["body"]


# --- P5-04: Hamzad Bridge (Separate from Main Hermes) ---


def test_hamzad_bridge_sync_dedup_conflict_and_privacy(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    hamzad_svc = FakeHamzadMemoryService()
    bridge = HamzadBridge(store, hamzad_svc)

    # Seed existing vault memory to trigger conflict on sync
    store.remember(
        "Gateway timeout policy",
        "Old timeout 5s.",
        scope=MemoryScope.PROJECT,
        projects=["hamzad-core"],
    )
    # Seed private vault memory that must never leak to Hamzad recall
    store.remember(
        "Personal note",
        "Secret personal info.",
        scope=MemoryScope.PROJECT,
        projects=["hamzad-core"],
        private=True,
    )

    hamzad_svc.store_episode(
        "hz-1",
        "router",
        {"title": "Gateway timeout policy", "content": "New timeout 15s, token sk-1234567890abcdef1234567890."},
    )

    first_sync = bridge.sync_episodes_to_vault("hz-1", project="hamzad-core", supersede_conflicts=True)
    assert first_sync["synced"] == 1
    assert first_sync["conflicts"] == 1

    # Re-syncing the same session is idempotent
    second_sync = bridge.sync_episodes_to_vault("hz-1", project="hamzad-core")
    assert second_sync["synced"] == 0
    assert second_sync["skipped"] == 1

    recalled = bridge.recall_for_session("hamzad-core")
    titles = {r["title"] for r in recalled}
    assert "Personal note" not in titles
    assert any("[REDACTED_API_KEY]" in r["content"] for r in recalled)

    # Push non-private memory to Hamzad KV
    assert bridge.push_memory_to_hamzad_kv("core", recalled[0]["id"]) is True
    assert hamzad_svc.get_key("core", recalled[0]["id"]) is not None


# --- P5-03: Coding Agent Harness Adapters & MCP ---


@pytest.mark.parametrize("harness", list_harnesses())
def test_coding_agent_adapters(tmp_path: Path, harness: str) -> None:
    adapter = get_harness_adapter(harness)
    instr = adapter.render_instructions(tmp_path)
    assert instr
    mcp_cfg = adapter.build_mcp_config(tmp_path)
    assert "mcpServers" in mcp_cfg or "extensions" in mcp_cfg

    skill_file = adapter.export_skill("memory-check", "# Memory Check\nRun health.", tmp_path)
    assert skill_file.exists()
    if harness == "gemini-cli":
        assert (tmp_path / ".gemini" / "commands" / "memory-check.toml").exists()

    assert cli_main(["--vault", str(tmp_path), "install-adapter", harness]) == 0


def test_mcp_server_privacy_and_tools(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    store.remember("Secret private", "Do not expose.", scope=MemoryScope.GENERAL, private=True)
    mcp = MCPServer(store)

    init_resp = mcp.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_resp["result"]["serverInfo"]["name"] == "tm-second-brain"

    tools_resp = mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert len(tools_resp["result"]["tools"]) == 6

    rem_resp = mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_remember",
                "arguments": {
                    "title": "MCP tip",
                    "body": "Use stdio MCP, key sk-1234567890abcdef1234567890",
                    "scope": "general",
                },
            },
        }
    )
    payload = json.loads(rem_resp["result"]["content"][0]["text"])
    assert "[REDACTED_API_KEY]" in payload["record"]["body"]

    rec_resp = mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "memory_recall", "arguments": {}},
        }
    )
    rec_payload = json.loads(rec_resp["result"]["content"][0]["text"])
    assert all(r["title"] != "Secret private" for r in rec_payload["records"])
