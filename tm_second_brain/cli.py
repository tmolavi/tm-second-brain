"""Command-line interface for TM Second Brain (`tm-brain`)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .adapters.harnesses import get_harness_adapter, list_harnesses
from .adapters.mcp_server import MCPServer
from .backup.archive import VaultBackupManager
from .backup.templates import VALID_TEMPLATES, install_starter_template
from .core.models import ConfidenceLevel, MemoryScope, SearchQuery
from .learning.activity_log import ActivityLogger
from .learning.feedback import FeedbackManager
from .memory.markdown_store import MarkdownMemoryStore, atomic_write_text


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tm-brain", description="TM Second Brain CLI")
    parser.add_argument("--vault", default=".", help="Path to the Markdown vault root")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Initialize vault memory directories")
    init_p.add_argument("--template", default=None, choices=list(VALID_TEMPLATES))
    sub.add_parser("health", help="Print vault and retrieval health")
    sub.add_parser("mcp", help="Run stdio JSON-RPC MCP server")

    adp = sub.add_parser("install-adapter", help="Install coding agent harness config into vault")
    adp.add_argument("harness", choices=list_harnesses())

    rem = sub.add_parser("remember", help="Store a new memory")
    rem.add_argument("--title", required=True)
    rem.add_argument("--body", required=True)
    rem.add_argument("--scope", default="project", choices=[s.value for s in MemoryScope])
    rem.add_argument("--project", action="append", default=[])
    rem.add_argument("--platform", action="append", default=[])
    rem.add_argument("--confidence", default="unverified", choices=[c.value for c in ConfidenceLevel])
    rem.add_argument("--verification", default=None)
    rem.add_argument("--agent", default="human")
    rem.add_argument("--private", action="store_true")
    rem.add_argument("--tag", action="append", default=[])

    rec = sub.add_parser("recall", help="Recall active memories")
    rec.add_argument("--project", default=None)
    rec.add_argument("--limit", type=int, default=20)

    sea = sub.add_parser("search", help="Search memories")
    sea.add_argument("query")
    sea.add_argument("--project", default=None)
    sea.add_argument("--limit", type=int, default=10)

    cor = sub.add_parser("correct", help="Supersede an existing memory")
    cor.add_argument("target_id")
    cor.add_argument("--title", required=True)
    cor.add_argument("--body", required=True)
    cor.add_argument("--reason", required=True)
    cor.add_argument("--agent", default="human")

    bak = sub.add_parser("backup", help="Create a SHA-256 verified .tar.gz backup")
    bak.add_argument("out")

    res = sub.add_parser("restore", help="Restore from a .tar.gz backup")
    res.add_argument("archive")
    res.add_argument("--overwrite", action="store_true")

    exp = sub.add_parser("export", help="Export memories to JSON bundle")
    exp.add_argument("out")
    exp.add_argument("--include-private", action="store_true")

    imp = sub.add_parser("import-bundle", help="Import memories from JSON bundle")
    imp.add_argument("bundle")
    imp.add_argument("--overwrite", action="store_true")

    lrn = sub.add_parser("learn", help="Feedback pattern detection and L2-approved learning")
    lrn_sub = lrn.add_subparsers(dest="learn_cmd", required=True)
    lrn_log = lrn_sub.add_parser("log")
    lrn_log.add_argument("--skill", required=True)
    lrn_log.add_argument("--outcome", required=True)
    lrn_log.add_argument("--correction", default="")
    lrn_log.add_argument("--rule", default="none")
    lrn_scan = lrn_sub.add_parser("scan")
    lrn_scan.add_argument("--min-occurrences", type=int, default=2)
    lrn_app = lrn_sub.add_parser("approve")
    lrn_app.add_argument("proposal_id")
    lrn_app.add_argument("--approver", default="human")

    act = sub.add_parser("activity-log", help="Append an entry to the agent activity log")
    act.add_argument("--env", required=True)
    act.add_argument("--agent", required=True)
    act.add_argument("--action", required=True)
    act.add_argument("--summary", required=True)
    act.add_argument("--project", default=None)

    orc = sub.add_parser("orchestrate", help="Inspect and control multi-agent orchestration sessions")
    orc_sub = orc.add_subparsers(dest="orc_cmd", required=True)
    orc_sub.add_parser("list", help="List persisted orchestration sessions")
    orc_stat = orc_sub.add_parser("status", help="Get details of a session")
    orc_stat.add_argument("session_id")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    store = MarkdownMemoryStore(Path(args.vault))
    backup_mgr = VaultBackupManager(store)

    if args.command == "init":
        store.ensure_layout()
        tpl_info = (
            install_starter_template(store.vault_root, args.template) if args.template else None
        )
        print(json.dumps({"status": "initialized", "vault": str(store.vault_root), "template": tpl_info}))
        return 0

    if args.command == "mcp":
        MCPServer(store).serve_stdio()
        return 0

    if args.command == "install-adapter":
        adapter = get_harness_adapter(args.harness)
        instr_path = store.vault_root / adapter.spec.instruction_file
        if not instr_path.exists():
            atomic_write_text(instr_path, adapter.render_instructions(store.vault_root))
        mcp_path = store.vault_root / adapter.spec.mcp_config_path
        if not mcp_path.exists():
            atomic_write_text(mcp_path, json.dumps(adapter.build_mcp_config(store.vault_root), indent=2) + "\n")
        print(json.dumps({"harness": adapter.harness_name, "instruction_file": str(instr_path), "mcp_config": str(mcp_path)}))
        return 0

    if args.command == "health":
        print(json.dumps(store.health(), indent=2))
        return 0

    if args.command == "remember":
        res = store.remember(
            args.title,
            args.body,
            scope=MemoryScope(args.scope),
            projects=args.project or None,
            platforms=args.platform or None,
            confidence=ConfidenceLevel(args.confidence),
            verification=args.verification,
            source_agent=args.agent,
            private=args.private,
            tags=args.tag or None,
        )
        print(
            json.dumps(
                {
                    "record": res.record.to_dict(),
                    "conflicts": [c.__dict__ for c in res.conflicts],
                    "warnings": res.warnings,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "recall":
        records = store.recall(project=args.project, limit=args.limit)
        print(json.dumps([r.to_dict() for r in records], indent=2, ensure_ascii=False))
        return 0

    if args.command == "search":
        hits = store.search(SearchQuery(text=args.query, project=args.project, limit=args.limit))
        print(
            json.dumps(
                [{"score": h.score, "backend": h.backend, "record": h.record.to_dict()} for h in hits],
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "correct":
        res = store.correct(
            args.target_id,
            args.title,
            args.body,
            reason=args.reason,
            source_agent=args.agent,
        )
        print(json.dumps(res.record.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.command == "backup":
        print(json.dumps(backup_mgr.create_backup(args.out), indent=2))
        return 0

    if args.command == "restore":
        print(json.dumps(backup_mgr.restore_backup(args.archive, overwrite=args.overwrite), indent=2))
        return 0

    if args.command == "export":
        print(
            json.dumps(
                backup_mgr.export_bundle(args.out, include_private=args.include_private),
                indent=2,
            )
        )
        return 0

    if args.command == "import-bundle":
        print(
            json.dumps(
                backup_mgr.import_bundle(args.bundle, overwrite=args.overwrite),
                indent=2,
            )
        )
        return 0

    if args.command == "learn":
        fb = FeedbackManager(store.vault_root)
        if args.learn_cmd == "log":
            p = fb.log_feedback(args.skill, args.outcome, correction=args.correction, proposed_rule=args.rule)
            print(json.dumps({"feedback_file": str(p)}))
            return 0
        if args.learn_cmd == "scan":
            drafts = fb.scan_patterns(min_occurrences=args.min_occurrences)
            print(json.dumps([d.__dict__ for d in drafts], indent=2))
            return 0
        if args.learn_cmd == "approve":
            print(json.dumps(fb.approve_proposal(args.proposal_id, approver=args.approver), indent=2))
            return 0

    if args.command == "activity-log":
        rec = ActivityLogger(store.vault_root).log_action(
            environment=args.env,
            agent_id=args.agent,
            action=args.action,
            summary=args.summary,
            project=args.project,
        )
        print(json.dumps(rec, indent=2))
        return 0

    if args.command == "orchestrate":
        from .orchestration.session_journal import SessionJournal

        journal = SessionJournal(store.vault_root)
        if args.orc_cmd == "list":
            sessions = journal.list_sessions()
            print(json.dumps(sessions, indent=2, ensure_ascii=False))
            return 0
        if args.orc_cmd == "status":
            session_data = journal.load_session(args.session_id)
            if not session_data:
                print(json.dumps({"error": f"Session '{args.session_id}' not found."}, indent=2))
                return 1
            print(json.dumps(session_data, indent=2, ensure_ascii=False))
            return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
