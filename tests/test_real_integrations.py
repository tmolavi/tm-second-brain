"""Controlled real-runtime integration tests (non-destructive, tmp_path-scoped)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tm_second_brain.adapters.hamzad import HamzadBridge
from tm_second_brain.adapters.hermes import (
    HermesPersonalDesktopFinlandAdapter,
    HermesPersonalDesktopMacAdapter,
    MainHermesAdapter,
)
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore

MOLAVI_OS_ROOT = Path("/Users/taghimolavi/Downloads/git/molavi-agentic-os")


def test_hamzad_core_sqlite_memory_store_bridge_roundtrip(tmp_path: Path) -> None:
    """Verify HamzadBridge against real molavi_agentic_os SQLiteMemoryStore in tmp_path."""
    if not MOLAVI_OS_ROOT.exists():
        pytest.skip("molavi-agentic-os repository not present at expected workspace path")

    if str(MOLAVI_OS_ROOT) not in sys.path:
        sys.path.insert(0, str(MOLAVI_OS_ROOT))

    from molavi_agentic_os.memory.sqlite_store import SQLiteMemoryStore

    db_path = tmp_path / "hamzad_core_test.db"
    vault_root = tmp_path / "hamzad_vault"

    service = SQLiteMemoryStore(db_path=str(db_path))
    store = MarkdownMemoryStore(vault_root)
    bridge = HamzadBridge(store, service)

    # 1. Store episodes in real SQLiteMemoryStore
    service.store_episode(
        "sess-alpha",
        "hamzad-core",
        {
            "title": "PostgreSQL WAL tuning",
            "content": "Enable WAL mode and checkpoint_timeout=15min for hamzad-core.",
        },
    )
    service.store_episode(
        "sess-beta",
        "hamzad-core",
        {
            "title": "Unrelated project note",
            "content": "Brandex crawler rate limit is 30 req/min.",
        },
    )

    # 2. Sync only sess-alpha into project-alpha
    sync_stats = bridge.sync_episodes_to_vault("sess-alpha", project="project-alpha", limit=10)
    assert sync_stats["synced"] == 1
    assert sync_stats["skipped"] == 0

    # Idempotent re-sync must skip duplicate
    sync_again = bridge.sync_episodes_to_vault("sess-alpha", project="project-alpha", limit=10)
    assert sync_again["synced"] == 0
    assert sync_again["skipped"] == 1

    # 3. Project-scoped recall must return project-alpha memory and exclude project-beta
    recalled_alpha = bridge.recall_for_session(project="project-alpha", limit=10)
    assert len(recalled_alpha) == 1
    assert "PostgreSQL WAL tuning" in recalled_alpha[0]["title"]

    recalled_beta = bridge.recall_for_session(project="project-beta", limit=10)
    assert recalled_beta == []

    # 4. Push a vault memory back into Hamzad KV store
    mem_id = recalled_alpha[0]["id"]
    pushed = bridge.push_memory_to_hamzad_kv("tm-second-brain", mem_id)
    assert pushed is True
    kv_record = service.get_key("tm-second-brain", mem_id)
    assert kv_record is not None
    assert kv_record["title"] == "PostgreSQL WAL tuning"
    assert "WAL mode" in kv_record["body"]
    assert kv_record["version"] == 1


def test_real_mcp_stdio_subprocess_roundtrip(tmp_path: Path) -> None:
    """Spawn real `python3 -m tm_second_brain.cli mcp` subprocess and run JSON-RPC over stdio."""
    vault_root = tmp_path / "mcp_vault"
    repo_root = Path(__file__).resolve().parents[1]

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "memory_remember",
                "arguments": {
                    "title": "MCP stdio verification",
                    "body": "Verified real JSON-RPC stdio roundtrip.",
                    "scope": "project",
                    "projects": ["hermes-prod"],
                    "confidence": "verified",
                    "source_agent": "main-hermes",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "memory_search",
                "arguments": {"query": "stdio roundtrip", "project": "hermes-prod", "limit": 5},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "memory_recall",
                "arguments": {"project": "hermes-prod", "limit": 5},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "memory_health", "arguments": {}},
        },
    ]
    stdin_payload = "\n".join(json.dumps(req) for req in requests) + "\n"

    proc = subprocess.run(
        [sys.executable, "-m", "tm_second_brain.cli", "--vault", str(vault_root), "mcp"],
        input=stdin_payload,
        text=True,
        capture_output=True,
        cwd=str(repo_root),
        timeout=15,
        check=False,
    )
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 6
    responses = [json.loads(line) for line in lines]

    assert responses[0]["result"]["serverInfo"]["name"] == "tm-second-brain"
    tool_names = [t["name"] for t in responses[1]["result"]["tools"]]
    assert "memory_search" in tool_names
    assert "memory_remember" in tool_names

    remember_payload = json.loads(responses[2]["result"]["content"][0]["text"])
    assert remember_payload["record"]["title"] == "MCP stdio verification"

    search_payload = json.loads(responses[3]["result"]["content"][0]["text"])
    assert len(search_payload["results"]) == 1
    assert search_payload["results"][0]["record"]["title"] == "MCP stdio verification"

    recall_payload = json.loads(responses[4]["result"]["content"][0]["text"])
    assert len(recall_payload["records"]) == 1

    health_payload = json.loads(responses[5]["result"]["content"][0]["text"])
    assert health_payload["offline_ready"] is True
    assert health_payload["total_memories"] == 1


def test_four_target_environments_isolated_adapters(tmp_path: Path) -> None:
    """Verify Main Hermes, Finland Desktop, and Mac Desktop maintain strict isolation."""
    main_store = MarkdownMemoryStore(tmp_path / "main_hermes_vault")
    fi_store = MarkdownMemoryStore(tmp_path / "finland_desktop_vault")
    mac_store = MarkdownMemoryStore(tmp_path / "mac_desktop_vault")

    main_adapter = MainHermesAdapter(main_store)
    fi_adapter = HermesPersonalDesktopFinlandAdapter(fi_store)
    mac_adapter = HermesPersonalDesktopMacAdapter(mac_store)

    main_adapter.store_episode(
        "hamzad-prod",
        "main-hermes",
        {
            "title": "Main Hermes prod rule",
            "content": "Never share production operational secrets with personal desktops.",
        },
    )
    fi_adapter.store_episode(
        "personal-finland",
        "hermes-desktop-fi",
        {
            "title": "Finland desktop note",
            "content": "Personal Helsinki server workspace note.",
        },
    )
    mac_adapter.store_episode(
        "personal-mac",
        "hermes-desktop-mac",
        {
            "title": "Mac desktop note",
            "content": "Personal macOS Apple Silicon local note.",
        },
    )

    assert len(main_adapter.get_episodes("personal-finland")) == 0
    assert len(fi_adapter.get_episodes("hamzad-prod")) == 0
    assert len(mac_adapter.get_episodes("personal-finland")) == 0
    assert len(mac_adapter.get_episodes("personal-mac")) == 1
