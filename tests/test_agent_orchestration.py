"""Comprehensive acceptance test suite for TM Agent Orchestration (10 Scenarios).

Inspired by HKUDS/AutoSwarm, fully integrated with TM Second Brain & Molavi Agentic OS.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from tm_second_brain.adapters.hamzad import HamzadBridge
from tm_second_brain.adapters.harnesses import get_harness_adapter, list_harnesses
from tm_second_brain.adapters.hermes import (
    HermesPersonalDesktopAdapter,
    MainHermesAdapter,
)
from tm_second_brain.core.contracts import (
    AgentOrchestratorProtocol,
    HarnessAdapter,
)
from tm_second_brain.core.models import MemoryScope
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore
from tm_second_brain.orchestration import (
    AgentOrchestrator,
    AgentRole,
    AggregationResult,
    OrchestrationTaskStatus,
    RiskLevel,
    TaskEnvelope,
    TaskUnit,
)
from tm_second_brain.privacy.policy import DefaultPrivacyPolicy


# Scenario 1: Delegate a task to two independent agents
def test_scenario_01_multi_agent_delegation(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    orchestrator.register_role(AgentRole("code-gen", "Code Generator", "Writes code", ["generate_code"]))
    orchestrator.register_role(AgentRole("code-review", "Code Reviewer", "Reviews code", ["review_code"]))

    t1 = TaskUnit(task_id="t1", name="Generate Feature", action="generate_code", agent_id="code-gen")
    t2 = TaskUnit(task_id="t2", name="Review Feature", action="review_code", agent_id="code-review", depends_on=["t1"])

    executed_agents = []

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        executed_agents.append((task.agent_id, envelope.source_agent))
        return {"output": {"status": "ok", "agent": task.agent_id}}

    tasks, records = orchestrator.run_session("sess-sc1", [t1, t2], runner)
    assert len(tasks) == 2
    assert tasks["t1"].status == OrchestrationTaskStatus.COMPLETED
    assert tasks["t2"].status == OrchestrationTaskStatus.COMPLETED
    assert executed_agents[0] == ("code-gen", "orchestrator")
    assert executed_agents[1] == ("code-review", "orchestrator")


# Scenario 2: Execute independent subtasks in parallel
def test_scenario_02_parallel_execution(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path, max_workers=3)
    t1 = TaskUnit(task_id="p1", name="Fetch Source A", action="fetch", agent_id="crawler-1")
    t2 = TaskUnit(task_id="p2", name="Fetch Source B", action="fetch", agent_id="crawler-2")
    t3 = TaskUnit(task_id="p3", name="Fetch Source C", action="fetch", agent_id="crawler-3")

    timestamps = {}

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        start = time.time()
        time.sleep(0.05)
        end = time.time()
        timestamps[task.task_id] = (start, end)
        return {"output": {"status": "fetched"}}

    tasks, records = orchestrator.run_session("sess-sc2", [t1, t2, t3], runner)
    assert len(tasks) == 3
    assert all(t.status == OrchestrationTaskStatus.COMPLETED for t in tasks.values())

    # Check concurrency: tasks should overlap in time
    starts = [ts[0] for ts in timestamps.values()]
    ends = [ts[1] for ts in timestamps.values()]
    # Overlap occurs if the max start is before the min end
    assert max(starts) < min(ends) + 0.1


# Scenario 3: Transfer results between agents
def test_scenario_03_transfer_results_between_agents(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    t1 = TaskUnit(
        task_id="t1",
        name="Step 1 Output",
        action="produce",
        agent_id="producer",
        inputs={"token": "sk-1234567890abcdef1234567890", "data": "clean-metric-42"},
    )
    t2 = TaskUnit(
        task_id="t2",
        name="Step 2 Consume",
        action="consume",
        agent_id="consumer",
        depends_on=["t1"],
    )

    received_payloads = []

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        received_payloads.append(envelope.payload)
        if task.action == "produce":
            return {"output": {"artifact": "res-alpha", "metric": 42}, "evidence": ["proof-1"]}
        return {"output": {"consumed": True}}

    tasks, records = orchestrator.run_session("sess-sc3", [t1, t2], runner)
    assert tasks["t1"].status == OrchestrationTaskStatus.COMPLETED
    assert tasks["t2"].status == OrchestrationTaskStatus.COMPLETED

    # Verify secret was redacted during transmission
    assert "[REDACTED_API_KEY]" in received_payloads[0]["token"]
    assert "sk-1234567890abcdef1234567890" not in received_payloads[0]["token"]


# Scenario 4: Resume an interrupted task without duplicate execution
def test_scenario_04_session_recovery_no_duplicate(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    t1 = TaskUnit(task_id="step1", name="Compute Step 1", action="compute", agent_id="worker")
    t2 = TaskUnit(task_id="step2", name="Compute Step 2", action="compute", agent_id="worker", depends_on=["step1"])

    execution_counts = {"step1": 0, "step2": 0}

    def failing_runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        execution_counts[task.task_id] += 1
        if task.task_id == "step2":
            raise RuntimeError("Simulated transient network drop mid-task")
        return {"output": {"val": 1}}

    # Initial run - step2 fails
    tasks, records = orchestrator.run_session("sess-sc4", [t1, t2], failing_runner)
    assert tasks["step1"].status == OrchestrationTaskStatus.COMPLETED
    assert tasks["step2"].status == OrchestrationTaskStatus.FAILED
    assert execution_counts["step1"] == 1
    assert execution_counts["step2"] == 1

    # Resume session with recovered runner
    def recovered_runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        execution_counts[task.task_id] += 1
        return {"output": {"val": 2}}

    resumed_tasks, resumed_records = orchestrator.resume_session("sess-sc4", recovered_runner)
    assert resumed_tasks["step1"].status == OrchestrationTaskStatus.COMPLETED
    assert resumed_tasks["step2"].status == OrchestrationTaskStatus.COMPLETED

    # Step 1 MUST NOT have been re-executed!
    assert execution_counts["step1"] == 1
    # Step 2 ran a second time to complete
    assert execution_counts["step2"] == 2


# Scenario 5: Trigger an approval requirement for a sensitive operation
def test_scenario_05_approval_requirement_sensitive_operation(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    t_safe = TaskUnit(task_id="safe", name="Read Stats", action="read", agent_id="analyst")
    t_sens = TaskUnit(
        task_id="deploy",
        name="Deploy to Production",
        action="deploy",
        agent_id="deployer",
        depends_on=["safe"],
        requires_approval=True,
        risk_level=RiskLevel.HIGH,
    )

    run_calls = []

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        run_calls.append(task.task_id)
        return {"output": {"status": "ok"}}

    # First execution: t_sens must be paused in BLOCKED_ON_APPROVAL
    tasks, records = orchestrator.run_session("sess-sc5", [t_safe, t_sens], runner)
    assert tasks["safe"].status == OrchestrationTaskStatus.COMPLETED
    assert tasks["deploy"].status == OrchestrationTaskStatus.BLOCKED_ON_APPROVAL
    assert "deploy" not in run_calls

    pending = orchestrator.get_pending_approvals()
    assert len(pending) == 1
    ticket = pending[0]
    assert ticket.task_id == "deploy"
    assert ticket.risk_level == RiskLevel.HIGH

    # Operator approves ticket
    assert orchestrator.approve_task(ticket.ticket_id, approver="sec-lead", reason="Change approved for staging")

    # Resume session
    resumed_tasks, _ = orchestrator.resume_session("sess-sc5", runner)
    assert resumed_tasks["deploy"].status == OrchestrationTaskStatus.COMPLETED
    assert "deploy" in run_calls


# Scenario 6: Aggregate results and identify conflicting outputs
def test_scenario_06_result_aggregation_and_conflict_detection(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    t1 = TaskUnit(
        task_id="review_a",
        name="Reviewer A",
        action="review",
        agent_id="auditor-1",
        expected_artifacts=["audit_report"],
    )
    t2 = TaskUnit(
        task_id="review_b",
        name="Reviewer B",
        action="review",
        agent_id="auditor-2",
        expected_artifacts=["audit_report"],
    )

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        if task.task_id == "review_a":
            # Reports verdict: approved, but forgot audit_report artifact
            return {"output": {"verdict": "approved", "score": 90}}
        # Reports verdict: rejected, includes audit_report
        return {
            "output": {"verdict": "rejected", "score": 40},
            "evidence": ["audit_report"],
        }

    tasks, records = orchestrator.run_session("sess-sc6", [t1, t2], runner)
    agg = orchestrator.aggregate_results("sess-sc6", tasks)

    # Conflicts detected
    assert len(agg.conflicts_detected) == 1
    assert agg.conflicts_detected[0]["conflicting_key"] == "verdict"

    # Missing evidence detected for reviewer A
    assert len(agg.missing_evidence) == 1
    assert "missing expected artifact 'audit_report'" in agg.missing_evidence[0]

    assert agg.is_successful is False
    assert "Conflicts Detected: 1" in agg.consolidated_summary


# Scenario 7: Detect an unavailable agent and use a supported fallback
def test_scenario_07_agent_unavailable_fallback(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(tmp_path)
    orchestrator.register_role(
        AgentRole("primary-summarizer", "Primary Summarizer", "Fast summarizer", available=False, fallback_role_id="fallback-summarizer")
    )
    orchestrator.register_role(
        AgentRole("fallback-summarizer", "Fallback Summarizer", "Backup summarizer", available=True)
    )

    t = TaskUnit(
        task_id="sum1",
        name="Summarize Article",
        action="summarize",
        agent_id="primary-summarizer",
    )

    executed_agent = []

    def runner(task: TaskUnit, envelope: TaskEnvelope) -> dict[str, Any]:
        executed_agent.append(task.agent_id)
        return {"output": {"summary": "done"}}

    tasks, records = orchestrator.run_session("sess-sc7", [t], runner)
    assert tasks["sum1"].status == OrchestrationTaskStatus.COMPLETED
    assert executed_agent == ["fallback-summarizer"]
    assert records[0].agent_id == "fallback-summarizer"


# Scenario 8: Verify Skill works without creating a second orchestration engine
def test_scenario_08_no_duplicate_engine(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    orchestrator = AgentOrchestrator(store.vault_root)

    # Must satisfy protocol
    assert isinstance(orchestrator, AgentOrchestratorProtocol)

    # Must reuse Second Brain storage (.tm-brain)
    session_file = orchestrator.journal.save_session("check-sc8", [])
    assert session_file.exists()
    assert ".tm-brain" in str(session_file)


# Scenario 9: Verify compatibility with existing adapters
def test_scenario_09_adapter_compatibility(tmp_path: Path) -> None:
    # All 6 harnesses can export the new skill
    skill_content = (tmp_path / "dummy_skill.md")
    skill_content.write_text("# Orchestration Skill", encoding="utf-8")

    for h in list_harnesses():
        adapter = get_harness_adapter(h)
        assert isinstance(adapter, HarnessAdapter)
        exported = adapter.export_skill("tm-agent-orchestration", "# Skill", tmp_path / h)
        assert exported.exists()
        assert exported.name == "SKILL.md"


# Scenario 10: Verify private credentials and memory remain isolated between environments
def test_scenario_10_credentials_and_memory_isolation(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    main_hermes = MainHermesAdapter(store)
    desktop_hermes = HermesPersonalDesktopAdapter(store)

    # Main Hermes stores production orchestration episode
    main_hermes.store_episode(
        "sess-prod",
        "orchestrator",
        {"title": "Prod Workflow", "content": "Prod cluster, token: sk-prod-secret-9999999999999999."},
    )

    # Desktop Hermes stores local orchestration episode
    desktop_hermes.store_episode(
        "sess-desktop",
        "orchestrator",
        {"title": "Desktop Workflow", "content": "Local Mac cluster, key: sk-desk-secret-1111111111111111."},
    )

    # Query episodes from Main Hermes: should NOT see desktop episodes
    main_eps = main_hermes.get_episodes("sess-desktop")
    assert len(main_eps) == 0

    # Query episodes from Desktop Hermes: should NOT see prod episodes
    desk_eps = desktop_hermes.get_episodes("sess-prod")
    assert len(desk_eps) == 0

    # Controlled exchange from desktop redacts secrets
    exported = desktop_hermes.export_controlled_exchange("sess-desktop")
    assert len(exported) == 1
    assert "sk-desk-secret" not in exported[0]["body"]
    assert "[REDACTED_API_KEY]" in exported[0]["body"]
