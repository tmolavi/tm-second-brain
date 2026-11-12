"""Tests for Phase 6 Intelligence Layer and 4-environment isolation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tm_second_brain.adapters.hermes import (
    HermesPersonalDesktopFinlandAdapter,
    HermesPersonalDesktopMacAdapter,
    MainHermesAdapter,
)
from tm_second_brain.cli import main as cli_main
from tm_second_brain.core.models import MemoryScope, SearchQuery
from tm_second_brain.learning.activity_log import ActivityLogger
from tm_second_brain.learning.feedback import FeedbackManager
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore
from tm_second_brain.retrieval.hybrid import HybridRetrievalBackend
from tm_second_brain.retrieval.optional_backends import (
    OllamaRetrievalAdapter,
    QMDRetrievalAdapter,
)
from tm_second_brain.retrieval.sqlite_fts import SQLiteFTSBackend


def test_optional_backends_disabled_by_default(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    store.remember("Local note", "Works offline without QMD or Ollama.", scope=MemoryScope.GENERAL)

    qmd = QMDRetrievalAdapter(tmp_path)  # enabled=False by default
    ollama = OllamaRetrievalAdapter()  # enabled=False by default
    assert qmd.is_available() is False

    records = store._load_all_records()
    qmd.index(records)
    ollama.index(records)
    assert qmd.query(SearchQuery(text="offline")) == []
    assert ollama.query(SearchQuery(text="offline")) == []


def test_sqlite_fts_and_concurrent_readers(tmp_path: Path) -> None:
    fts = SQLiteFTSBackend(tmp_path / ".tm-brain" / "index.db")
    store = MarkdownMemoryStore(tmp_path, retrieval_backend=fts)
    for i in range(5):
        store.remember(f"Concurrency rule {i}", f"SQLite WAL reader test {i}.", scope=MemoryScope.PROJECT, projects=["core"])

    def _run_search(idx: int) -> int:
        hits = store.search(SearchQuery(text="WAL reader", project="core"))
        return len(hits)

    with ThreadPoolExecutor(max_workers=4) as pool:
        counts = list(pool.map(_run_search, range(8)))
    assert all(c == 5 for c in counts)


def test_hybrid_retrieval_graph_boost(tmp_path: Path) -> None:
    hybrid = HybridRetrievalBackend()
    store = MarkdownMemoryStore(tmp_path, retrieval_backend=hybrid)
    target = store.remember("Target Architecture", "Core SQLite pattern.", scope=MemoryScope.GENERAL).record
    store.remember("Ref 1", "See [[Target Architecture]] for SQLite.", scope=MemoryScope.GENERAL)
    store.remember("Ref 2", "Also uses [[Target Architecture]] SQLite.", scope=MemoryScope.GENERAL)

    hits = store.search(SearchQuery(text="SQLite"))
    assert hits[0].record.id == target.id
    assert hits[0].backend == "hybrid(bm25+graph)"


def test_feedback_l1_draft_and_l2_approval(tmp_path: Path) -> None:
    fb = FeedbackManager(tmp_path)
    fb.log_feedback("code-review", "missed edge case", correction="check empty list", proposed_rule="Always check empty inputs")
    fb.log_feedback("code-review", "missed edge case again", correction="check empty dict", proposed_rule="Always check empty inputs")

    drafts = fb.scan_patterns(min_occurrences=2)
    assert len(drafts) == 1
    assert drafts[0].status == "l1_draft"
    assert not (tmp_path / "Skills" / "code-review" / "SKILL.md").exists()

    # L2 explicit human approval promotes rule and creates backup
    res = fb.approve_proposal(drafts[0].proposal_id, approver="taqi")
    assert res["status"] == "l2_approved"
    skill_text = (tmp_path / "Skills" / "code-review" / "SKILL.md").read_text(encoding="utf-8")
    assert "Always check empty inputs" in skill_text


def test_activity_log_redacts_secrets(tmp_path: Path) -> None:
    logger = ActivityLogger(tmp_path)
    rec = logger.log_action(
        environment="hermes-personal-desktop-mac",
        agent_id="mac-agent",
        action="remember",
        summary="Stored note with sk-1234567890abcdef1234567890",
        project="demo",
    )
    assert "[REDACTED_API_KEY]" in rec["summary"]
    assert "sk-1234567890abcdef1234567890" not in rec["summary"]
    assert logger.jsonl_path.exists()


def test_four_environment_hermes_finland_vs_mac_isolation(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    main_h = MainHermesAdapter(store)
    finland_h = HermesPersonalDesktopFinlandAdapter(store)
    mac_h = HermesPersonalDesktopMacAdapter(store)

    main_h.store_episode("s1", "a1", {"title": "Main Hermes", "content": "Hamzad prod."})
    finland_h.store_episode("s1", "a2", {"title": "Finland Desktop", "content": "Remote personal."})
    mac_h.store_episode("s1", "a3", {"title": "Mac Desktop", "content": "Local Mac."})

    assert [e["entry"]["title"] for e in main_h.get_episodes("s1")] == ["Main Hermes"]
    assert [e["entry"]["title"] for e in finland_h.get_episodes("s1")] == ["Finland Desktop"]
    assert [e["entry"]["title"] for e in mac_h.get_episodes("s1")] == ["Mac Desktop"]


def test_cli_phase6_learn_and_activity(tmp_path: Path, capsys) -> None:
    assert cli_main(["--vault", str(tmp_path), "activity-log", "--env", "mac", "--agent", "cli", "--action", "test", "--summary", "ok"]) == 0
    assert cli_main(["--vault", str(tmp_path), "learn", "log", "--skill", "demo", "--outcome", "fail", "--rule", "Rule A"]) == 0
    assert cli_main(["--vault", str(tmp_path), "learn", "log", "--skill", "demo", "--outcome", "fail", "--rule", "Rule A"]) == 0
    capsys.readouterr()
    assert cli_main(["--vault", str(tmp_path), "learn", "scan", "--min-occurrences", "2"]) == 0
    drafts = json.loads(capsys.readouterr().out)
    assert len(drafts) == 1
