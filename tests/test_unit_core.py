"""Unit tests for core memory, slugification, conflict/corrections, graph, and CLI."""

from __future__ import annotations

import json
from pathlib import Path

from tm_second_brain.cli import main as cli_main
from tm_second_brain.core.models import ConfidenceLevel, LifecycleStatus, MemoryScope
from tm_second_brain.memory.markdown_store import (
    MarkdownMemoryStore,
    parse_memory_markdown,
    sanitize_slug,
    serialize_memory_markdown,
)


def test_windows_safe_slug() -> None:
    assert sanitize_slug("CON") == "mem-con"
    assert sanitize_slug("LPT1") == "mem-lpt1"
    assert sanitize_slug("../../etc/passwd") == "etc-passwd"
    assert sanitize_slug("Hello: World? *Test*") == "hello-world-test"


def test_conflict_detection_and_correction_history(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    first = store.remember(
        "Cache strategy for API",
        "Use in-memory TTL cache.",
        scope=MemoryScope.PROJECT,
        projects=["api"],
    ).record

    # High-overlap title triggers conflict warning
    second_write = store.remember(
        "Cache strategy for API endpoints",
        "Use Redis.",
        scope=MemoryScope.PROJECT,
        projects=["api"],
    )
    assert len(second_write.conflicts) == 1
    assert second_write.conflicts[0].existing_id == first.id

    # Explicit correction supersedes cleanly and logs history
    corrected = store.correct(
        first.id,
        "Cache strategy for API",
        "Use SQLite + WAL local cache.",
        reason="Removed external Redis dependency",
        confidence=ConfidenceLevel.VERIFIED,
        verification="Load test passed",
        source_agent="hermes",
    ).record

    old_after = store.get(first.id)
    assert old_after is not None
    assert old_after.status == LifecycleStatus.SUPERSEDED
    assert old_after.superseded_by == corrected.id
    assert corrected.supersedes == first.id
    assert corrected.version == 2
    assert store.corrections_log.exists()


def test_wikilink_graph_expand(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    a = store.remember("Node A", "Links to [[Node B]].", scope=MemoryScope.GENERAL).record
    b = store.remember("Node B", "Standalone target.", scope=MemoryScope.GENERAL).record

    expanded = store.expand(a.id, depth=1)
    assert expanded["root"].id == a.id
    assert [n.id for n in expanded["neighbors"]] == [b.id]


def test_markdown_roundtrip(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    rec = store.remember(
        "Unicode & Persian Test",
        "پشتیبانی کامل از زبان فارسی و [[Architecture]].",
        scope=MemoryScope.GENERAL,
        tags=["persian", "i18n"],
    ).record
    raw = serialize_memory_markdown(rec)
    parsed = parse_memory_markdown(raw, relative_path=rec.relative_path)
    assert parsed.id == rec.id
    assert parsed.title == rec.title
    assert parsed.tags == ["persian", "i18n"]
    assert parsed.links == ["Architecture"]


def test_cli_end_to_end(tmp_path: Path, capsys) -> None:
    assert cli_main(["--vault", str(tmp_path), "init"]) == 0
    assert (
        cli_main(
            [
                "--vault",
                str(tmp_path),
                "remember",
                "--title",
                "CLI memory",
                "--body",
                "Stored via CLI.",
                "--project",
                "demo",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert cli_main(["--vault", str(tmp_path), "search", "CLI", "--project", "demo"]) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["record"]["title"] == "CLI memory"
