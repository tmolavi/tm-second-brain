---
name: tm-agent-orchestration
description: Multi-agent coordination, structured task delegation, parallel DAG execution, session recovery, approval checkpoints, and result aggregation across Antigravity, Hermes, Hamzad, and coding harnesses.
---

# TM Agent Orchestration (`tm-agent-orchestration`)

> **A reusable, portable Skill under the TM Second Brain & Molavi Agentic OS ecosystem.**  
> Inspired by **HKUDS/AutoSwarm** principles, built on zero-external-dependency standard Python.

---

## 1. Core Purpose & Architectural Role

`tm-agent-orchestration` provides a uniform, runtime-aware protocol to coordinate heterogeneous agents without duplicating existing runtime infrastructure (such as Hermes Main, Hamzad AI Gateway, or native subagents).

It addresses the fundamental challenges of multi-agent collaboration:
1. **Context Fragmentation & Leakage:** Prevents monolithic prompt accumulation by passing atomic, secret-redacted task envelopes.
2. **Brittle Dependencies:** Formally models multi-agent workflows as Directed Acyclic Graphs (DAGs), dispatching independent tasks in parallel and gating dependent steps.
3. **Session Interruption:** Checkpoints task progress in a durable session journal so interrupted runs resume safely without re-executing completed side-effects.
4. **Safety & Privileged Operations:** Enforces tokenized human approval gates on sensitive, destructive, credential, or deployment actions before downstream execution proceeds.
5. **Hallucination & Divergence:** Aggregates multi-agent outputs, enforces Foreman evidence verification, detects cross-agent discrepancies, and synthesizes consolidated findings.

---

## 2. Key Capabilities

### A. Multi-Agent Delegation
- Matches requested actions against a catalogue of `AgentRole` capabilities.
- Formally binds task contracts:
  - **Goal & Action:** What must be accomplished.
  - **Assigned Agent/Role:** Best-fit runtime or specialist.
  - **Inputs & Constraints:** Structured parameters, pre-redacted for privacy.
  - **Expected Artifacts & Acceptance Criteria:** Tangible verification outputs.
- Automatically re-routes to `fallback_agent_id` or `fallback_role_id` if the primary agent is marked unavailable.

### B. Parallel Execution
- Analyzes DAG dependency structures to isolate independent tasks.
- Concurrently dispatches independent tasks across a bounded worker pool (`max_workers`).
- Guarantees sequential gating for dependent tasks.

### C. Structured Agent Communication
- Transfers information between agents using `TaskEnvelope`:
  - `task_id`, `parent_task_id`, `session_id`, `source_agent`, `target_agent`.
  - `payload` with automatic secret and PII redaction (`[REDACTED_API_KEY]`, `[REDACTED_TOKEN]`).
  - `context_summary` maintaining lineage without ballooning context windows.

### D. Session Recovery
- Checkpoints execution state to `.tm-brain/orchestration_sessions/<session_id>.json`.
- On interruption or runtime crash, calling `resume_session(session_id)`:
  - Preserves outputs and records of already `COMPLETED` tasks.
  - Identifies `PENDING`, `RUNNING`, or `FAILED` tasks.
  - Resumes execution safely without accidental duplicate execution of completed work.

### E. Approval Handoff
- Tasks with `requires_approval=True` or `risk_level` in `["HIGH", "CRITICAL"]` automatically transition to `BLOCKED_ON_APPROVAL`.
- Generates an `ApprovalRequest` with unique ticket ID.
- Blocks downstream dependent execution until an authorized human or operator approves via `approve_task(ticket_id)`.
- Rejections cleanly halt dependent execution branches.

### F. Result Aggregation & Conflict Detection
- Aggregates outputs from multiple agents into `AggregationResult`.
- **Foreman Evidence Check:** Verifies that all declared `expected_artifacts` are present in outputs or evidence references.
- **Discrepancy Detection:** Analyzes critical fields (`verdict`, `decision`, `status`, `version`, `passed`) across agents to detect contradictory conclusions.
- Produces a unified summary and status verdict.

### G. Execution Evidence
- Generates immutable `ExecutionRecord`s:
  - Agent ID, task ID, action, runtime, timestamps, elapsed latency, evidence artifacts, error details.
  - Avoids storing credentials or raw private data.
  - Appends to the session journal and Second Brain activity log.

---

## 3. Python API Usage

```python
from pathlib import Path
from tm_second_brain.orchestration import (
    AgentOrchestrator,
    AgentRole,
    TaskUnit,
    RiskLevel,
    OrchestrationTaskStatus,
)

# 1. Initialize orchestrator linked to Second Brain vault
orchestrator = AgentOrchestrator(Path("./my-vault"), max_workers=4)

# 2. Register agent roles
orchestrator.register_role(AgentRole(
    role_id="researcher",
    name="Research Agent",
    description="Gathers facts and sources",
    capabilities=["search", "extract", "summarize"],
    runtime="antigravity"
))
orchestrator.register_role(AgentRole(
    role_id="verifier",
    name="Foreman Verifier",
    description="Validates physical artifacts and evidence",
    capabilities=["verify", "audit"],
    runtime="hermes"
))

# 3. Define DAG tasks
t1 = TaskUnit(
    task_id="task_research",
    name="Gather Evidence",
    action="search",
    agent_id="researcher",
    inputs={"topic": "AutoSwarm architecture"},
    expected_artifacts=["evidence_report"]
)

t2 = TaskUnit(
    task_id="task_verify",
    name="Verify Findings",
    action="verify",
    agent_id="verifier",
    inputs={"scope": "report_validation"},
    depends_on=["task_research"],
    expected_artifacts=["verification_verdict"]
)

# 4. Define task runner
def mock_runner(task: TaskUnit, envelope):
    if task.action == "search":
        return {
            "output": {"summary": "Extracted key patterns", "status": "pass"},
            "evidence": ["evidence_report"]
        }
    return {
        "output": {"verdict": "verified", "status": "pass"},
        "evidence": ["verification_verdict"]
    }

# 5. Execute session
session_id = "sess_001"
tasks, records = orchestrator.run_session(session_id, [t1, t2], mock_runner)

# 6. Aggregate results
agg = orchestrator.aggregate_results(session_id, tasks)
print(agg.consolidated_summary)
# -> "Orchestration Session: sess_001 | Tasks: 2/2 completed, 0 failed."
```

---

## 4. CLI Usage

The `tm-brain` CLI provides commands to inspect and manage orchestration sessions:

```bash
# List all persisted sessions in vault
tm-brain --vault ./my-vault orchestrate list

# Inspect session details and task statuses
tm-brain --vault ./my-vault orchestrate status sess_001
```

---

## 5. Runtime Compatibility & Environment Isolation

| Target Runtime | Integration Mechanism | Isolation Boundary |
|---|---|---|
| **Antigravity** | Installed as Native Agent Skill (`~/.gemini/config/skills/tm-agent-orchestration/`) | Uses local subagent invocation tools; no remote command escalation. |
| **Hermes Main (Finland)** | Installed as Hermes Agent Skill (`~/.hermes/skills/tm-agent-orchestration/`) with `hermes_agent.json` | Scoped to `main-hermes` namespace; does not mutate Hamzad production database. |
| **Hamzad Core** | Non-duplicating bridge via `HamzadBridge.record_orchestration_event()` | Preserves existing AI Gateway and Memory Service; zero duplicate storage. |
| **Hermes Personal Desktop (Mac)** | Installed in `hermes-mac-distribution/skills/tm-agent-orchestration/` with `hermes_agent.json` | Scoped to `hermes-personal-desktop-mac`; strict local file jail and human approval requirement. |
| **Coding Harnesses (Codex, Claude Code, Goose)** | Exported via `GenericHarnessAdapter.export_skill("tm-agent-orchestration", ...)` | Generates standard `SKILL.md` and harness instructions. |

---

## 6. Security Guarantees

1. **Zero Credential Transmission:** Secrets, bearer tokens, and API keys are automatically stripped from inter-agent task envelopes and session checkpoints.
2. **Mandatory Human-in-the-Loop for Privileged Actions:** Tasks tagged with `RiskLevel.HIGH` or `RiskLevel.CRITICAL` cannot be executed without explicit operator approval.
3. **Audit Trail:** Every delegated step produces an immutable execution record with duration, evidence, and provenance.
