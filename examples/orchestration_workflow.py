"""Example: Multi-agent coordination with parallel tasks, approval gate, and recovery."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure tm-second-brain is on path when running standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tm_second_brain.orchestration import (
    AgentOrchestrator,
    AgentRole,
    OrchestrationTaskStatus,
    RiskLevel,
    TaskUnit,
)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        vault = Path(tmp_dir)
        orchestrator = AgentOrchestrator(vault, max_workers=2)

        # 1. Register agents
        orchestrator.register_role(AgentRole("crawler", "Web Scraper", "Fetches pages", ["scrape"]))
        orchestrator.register_role(AgentRole("summarizer", "Summarizer", "Distills text", ["summarize"]))
        orchestrator.register_role(AgentRole("publisher", "Publisher", "Deploys output", ["publish"]))

        # 2. Define tasks with parallel branches and approval
        t1 = TaskUnit(task_id="t1", name="Scrape Site A", action="scrape", agent_id="crawler")
        t2 = TaskUnit(task_id="t2", name="Scrape Site B", action="scrape", agent_id="crawler")
        t3 = TaskUnit(
            task_id="t3",
            name="Summarize Data",
            action="summarize",
            agent_id="summarizer",
            depends_on=["t1", "t2"],
            expected_artifacts=["summary_artifact"],
        )
        t4 = TaskUnit(
            task_id="t4",
            name="Deploy Report",
            action="publish",
            agent_id="publisher",
            depends_on=["t3"],
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
        )

        def mock_runner(task: TaskUnit, envelope):
            if task.action == "scrape":
                return {"output": {"status": "ok", "site": task.name}, "evidence": [f"{task.task_id}_raw"]}
            if task.action == "summarize":
                return {"output": {"status": "ok", "verdict": "valid"}, "evidence": ["summary_artifact"]}
            return {"output": {"status": "published"}}

        # Run session
        session_id = "demo_session_01"
        tasks, records = orchestrator.run_session(session_id, [t1, t2, t3, t4], mock_runner)

        # t4 should be BLOCKED_ON_APPROVAL
        assert tasks["t4"].status == OrchestrationTaskStatus.BLOCKED_ON_APPROVAL
        print(f"Session {session_id}: t4 is safely paused waiting for human approval.")

        # Operator approves t4
        ticket = orchestrator.get_pending_approvals()[0]
        orchestrator.approve_task(ticket.ticket_id, approver="senior-engineer")
        print(f"Ticket {ticket.ticket_id} approved!")

        # Resume session without re-executing t1, t2, t3
        tasks, records = orchestrator.resume_session(session_id, mock_runner)
        assert tasks["t4"].status == OrchestrationTaskStatus.COMPLETED
        print("Session completed successfully after approval!")

        # Aggregate results
        agg = orchestrator.aggregate_results(session_id, tasks)
        print(f"Aggregation summary: {agg.consolidated_summary}")


if __name__ == "__main__":
    main()
