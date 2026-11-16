"""TM Agent Orchestrator: Multi-agent coordination, delegation, parallel DAG execution,

session recovery, approval gates, and result aggregation (AutoSwarm-inspired).
"""

from __future__ import annotations

import concurrent.futures
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from ..core.contracts import PrivacyPolicy
from ..learning.activity_log import ActivityLogger
from ..privacy.policy import DefaultPrivacyPolicy
from .models import (
    AgentRole,
    AggregationResult,
    ApprovalRequest,
    ExecutionRecord,
    OrchestrationTaskStatus,
    RiskLevel,
    TaskEnvelope,
    TaskUnit,
)
from .session_journal import SessionJournal


# Type alias for task executor: receives a TaskUnit and TaskEnvelope, returns a dict or TaskUnit
TaskRunner = Callable[[TaskUnit, TaskEnvelope], dict[str, Any]]


class AgentOrchestrator:
    """Portable multi-agent orchestration coordinator."""

    def __init__(
        self,
        vault_root: Path,
        *,
        max_workers: int = 4,
        privacy: PrivacyPolicy | None = None,
        roles: list[AgentRole] | None = None,
    ) -> None:
        self.vault_root = Path(vault_root)
        self.max_workers = max_workers
        self.privacy = privacy or DefaultPrivacyPolicy()
        self.journal = SessionJournal(self.vault_root)
        self.activity_logger = ActivityLogger(self.vault_root)
        self._roles: dict[str, AgentRole] = {r.role_id: r for r in (roles or [])}
        self._approval_requests: dict[str, ApprovalRequest] = {}

    def register_role(self, role: AgentRole) -> None:
        """Register an agent role in the orchestration catalogue."""
        self._roles[role.role_id] = role

    def get_role(self, role_id: str) -> AgentRole | None:
        return self._roles.get(role_id)

    def select_agent_for_action(self, action: str, preferred_agent: str | None = None) -> str:
        """Select an available agent capable of executing the requested action."""
        if preferred_agent and preferred_agent in self._roles:
            role = self._roles[preferred_agent]
            if role.available:
                return role.role_id
            if role.fallback_role_id and role.fallback_role_id in self._roles:
                return role.fallback_role_id

        # Search catalogue by capability or action
        for role in self._roles.values():
            if role.available and (action in role.capabilities or action == role.role_id):
                return role.role_id

        # Fallback to preferred or default
        return preferred_agent or "generic-agent"

    def create_envelope(
        self,
        session_id: str,
        task: TaskUnit,
        source_agent: str = "orchestrator",
        context_summary: str = "",
    ) -> TaskEnvelope:
        """Create a secret-redacted message envelope for inter-agent delegation."""
        redacted_inputs = self._redact_structure(task.inputs)
        redacted_summary = self.privacy.redact(context_summary or f"Task '{task.name}' delegated to '{task.agent_id}'")
        return TaskEnvelope(
            task_id=task.task_id,
            session_id=session_id,
            source_agent=source_agent,
            target_agent=task.agent_id,
            payload=redacted_inputs,
            parent_task_id=task.parent_id,
            context_summary=redacted_summary,
        )

    def _redact_structure(self, obj: Any) -> Any:
        """Recursively redact secrets and PII from payloads."""
        if isinstance(obj, str):
            return self.privacy.redact(obj)
        if isinstance(obj, dict):
            return {k: self._redact_structure(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._redact_structure(x) for x in obj]
        return obj

    def run_session(
        self,
        session_id: str,
        tasks: list[TaskUnit],
        runner: TaskRunner,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, TaskUnit], list[ExecutionRecord]]:
        """Execute a DAG of tasks with parallel dispatch, dependency resolution,

        approval checkpoints, and durable session state persistence.
        """
        self.journal.ensure_storage()
        task_map: dict[str, TaskUnit] = {t.task_id: t for t in tasks}
        completed_map: dict[str, TaskUnit] = {}
        records: list[ExecutionRecord] = []

        # Save initial state
        self.journal.save_session(session_id, list(task_map.values()), metadata=metadata, records=records)

        return self._coordinate_dag(session_id, task_map, completed_map, records, runner, metadata)

    def resume_session(
        self,
        session_id: str,
        runner: TaskRunner,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, TaskUnit], list[ExecutionRecord]]:
        """Resume an interrupted session, safely skipping already-completed tasks."""
        completed_map, pending_tasks = self.journal.get_resumable_state(session_id)
        task_map: dict[str, TaskUnit] = {**completed_map, **{t.task_id: t for t in pending_tasks}}

        existing_data = self.journal.load_session(session_id) or {}
        raw_records = existing_data.get("records", [])
        records: list[ExecutionRecord] = [ExecutionRecord.from_dict(r) for r in raw_records]

        merged_metadata = {**(existing_data.get("metadata") or {}), **(metadata or {})}

        return self._coordinate_dag(session_id, task_map, completed_map, records, runner, merged_metadata)

    def _coordinate_dag(
        self,
        session_id: str,
        task_map: dict[str, TaskUnit],
        completed_map: dict[str, TaskUnit],
        records: list[ExecutionRecord],
        runner: TaskRunner,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[dict[str, TaskUnit], list[ExecutionRecord]]:
        """Internal DAG resolution loop."""
        remaining: dict[str, TaskUnit] = {
            tid: t for tid, t in task_map.items() if tid not in completed_map
        }

        while remaining:
            # 1. Identify runnable tasks whose dependencies are satisfied and successful
            runnable: list[TaskUnit] = []
            for t in list(remaining.values()):
                # If blocked on approval, check if it was approved
                if t.status == OrchestrationTaskStatus.BLOCKED_ON_APPROVAL:
                    if t.approval_ticket_id:
                        req = self._approval_requests.get(t.approval_ticket_id)
                        if req and req.status == "approved":
                            t.status = OrchestrationTaskStatus.PENDING

                deps_met = all(
                    dep in completed_map
                    and completed_map[dep].status == OrchestrationTaskStatus.COMPLETED
                    for dep in t.depends_on
                )
                if deps_met and t.status in (OrchestrationTaskStatus.PENDING, OrchestrationTaskStatus.QUEUED):
                    # Check if approval was already granted
                    is_approved = False
                    if t.approval_ticket_id:
                        req = self._approval_requests.get(t.approval_ticket_id)
                        if req and req.status == "approved":
                            is_approved = True

                    if not is_approved and (t.requires_approval or t.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)):
                        t.status = OrchestrationTaskStatus.BLOCKED_ON_APPROVAL
                        if not t.approval_ticket_id:
                            ticket = self._create_approval_request(t)
                            t.approval_ticket_id = ticket.ticket_id
                        continue
                    runnable.append(t)

            if not runnable:
                # If there are tasks blocked on approval, checkpoint session state and halt gracefully
                has_blocked = any(t.status == OrchestrationTaskStatus.BLOCKED_ON_APPROVAL for t in remaining.values())
                if has_blocked:
                    self.journal.save_session(
                        session_id,
                        list(task_map.values()),
                        metadata=metadata,
                        records=records,
                    )
                    break

                # Otherwise, deadlock or unsatisfied dependencies
                for t in remaining.values():
                    if t.status not in (OrchestrationTaskStatus.BLOCKED_ON_APPROVAL, OrchestrationTaskStatus.COMPLETED):
                        t.status = OrchestrationTaskStatus.FAILED
                        t.error = f"Unsatisfied dependencies: {t.depends_on}"
                break

            # 2. Execute runnable tasks in parallel
            batch_records = self._execute_parallel_batch(session_id, runnable, runner)
            records.extend(batch_records)

            for t in runnable:
                if t.status == OrchestrationTaskStatus.COMPLETED:
                    completed_map[t.task_id] = t
                    del remaining[t.task_id]
                elif t.status == OrchestrationTaskStatus.FAILED:
                    # Keep failed task in task_map and remove from remaining to prevent infinite loop
                    del remaining[t.task_id]

            # 3. Checkpoint session state to journal
            self.journal.save_session(
                session_id,
                list(task_map.values()),
                metadata=metadata,
                records=records,
            )

        return task_map, records

    def _execute_parallel_batch(
        self,
        session_id: str,
        tasks: list[TaskUnit],
        runner: TaskRunner,
    ) -> list[ExecutionRecord]:
        """Execute independent tasks in parallel with safety, timeout, and fallback handling."""
        records: list[ExecutionRecord] = []
        if not tasks:
            return records

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks), self.max_workers)) as executor:
            future_to_task = {}
            for t in tasks:
                t.status = OrchestrationTaskStatus.RUNNING
                t.started_at = time.time()
                envelope = self.create_envelope(session_id, t)
                fut = executor.submit(self._execute_single_task_with_fallback, t, envelope, runner)
                future_to_task[fut] = (t, envelope)

            for fut in concurrent.futures.as_completed(future_to_task):
                task, envelope = future_to_task[fut]
                task.completed_at = time.time()
                duration = task.completed_at - (task.started_at or task.completed_at)

                try:
                    res_dict = fut.result()
                    task.output = self._redact_structure(res_dict.get("output", res_dict))
                    task.evidence = res_dict.get("evidence", [])
                    task.status = OrchestrationTaskStatus.COMPLETED
                    task.error = None
                except Exception as ex:
                    task.status = OrchestrationTaskStatus.FAILED
                    task.error = str(ex)

                rec = ExecutionRecord(
                    record_id=f"rec_{uuid.uuid4().hex[:8]}",
                    session_id=session_id,
                    task_id=task.task_id,
                    agent_id=task.agent_id,
                    action=task.action,
                    runtime=self._get_agent_runtime(task.agent_id),
                    status=task.status,
                    started_at=task.started_at or 0.0,
                    finished_at=task.completed_at,
                    duration_seconds=duration,
                    evidence_refs=task.evidence,
                    error=task.error,
                )
                records.append(rec)

                # Log activity
                self.activity_logger.log_action(
                    environment="orchestrator",
                    agent_id=task.agent_id,
                    action=task.action,
                    summary=f"Task '{task.name}' ended with status {task.status.value}",
                    project=session_id,
                )

        return records

    def _execute_single_task_with_fallback(
        self,
        task: TaskUnit,
        envelope: TaskEnvelope,
        runner: TaskRunner,
    ) -> dict[str, Any]:
        """Execute a task using runner; if agent is unavailable, route to fallback."""
        target_agent = task.agent_id
        role = self._roles.get(target_agent)

        # Check if primary agent is available
        if role and not role.available:
            fallback = task.fallback_agent_id or role.fallback_role_id
            if fallback:
                task.agent_id = fallback
                envelope.target_agent = fallback
                envelope.context_summary += f" (Fallback from {target_agent})"

        try:
            return runner(task, envelope)
        except Exception as exc:
            # If error suggests agent unavailability and fallback exists, try fallback
            fallback = task.fallback_agent_id or (role.fallback_role_id if role else None)
            if fallback and fallback != task.agent_id:
                task.agent_id = fallback
                envelope.target_agent = fallback
                envelope.context_summary += f" (Retried on fallback {fallback} after error: {exc})"
                return runner(task, envelope)
            raise

    def _get_agent_runtime(self, agent_id: str) -> str:
        role = self._roles.get(agent_id)
        return role.runtime if role else "generic"

    def _create_approval_request(self, task: TaskUnit) -> ApprovalRequest:
        """Create and register an approval ticket."""
        ticket_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
        req = ApprovalRequest(
            ticket_id=ticket_id,
            task_id=task.task_id,
            action=task.action,
            reason=f"Action '{task.action}' requires approval (risk: {task.risk_level.value})",
            target_resource=task.name,
            risk_level=task.risk_level,
        )
        self._approval_requests[ticket_id] = req
        return req

    def approve_task(
        self,
        ticket_id: str,
        approver: str = "human-operator",
        reason: str = "Approved by operator",
    ) -> bool:
        """Approve a pending approval ticket."""
        req = self._approval_requests.get(ticket_id)
        if not req or req.status != "pending":
            return False
        req.status = "approved"
        req.approver = approver
        req.decision_reason = reason
        return True

    def reject_task(
        self,
        ticket_id: str,
        approver: str = "human-operator",
        reason: str = "Rejected by operator",
    ) -> bool:
        """Reject a pending approval ticket."""
        req = self._approval_requests.get(ticket_id)
        if not req or req.status != "pending":
            return False
        req.status = "rejected"
        req.approver = approver
        req.decision_reason = reason
        return True

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        return [r for r in self._approval_requests.values() if r.status == "pending"]

    def aggregate_results(
        self,
        session_id: str,
        tasks: dict[str, TaskUnit] | list[TaskUnit],
    ) -> AggregationResult:
        """Collect and cross-verify outputs from multiple agents, detecting missing evidence

        and contradictory conclusions.
        """
        task_list = list(tasks.values()) if isinstance(tasks, dict) else list(tasks)
        total = len(task_list)
        completed = sum(1 for t in task_list if t.status == OrchestrationTaskStatus.COMPLETED)
        failed = sum(1 for t in task_list if t.status == OrchestrationTaskStatus.FAILED)

        agent_outputs: dict[str, dict[str, Any]] = {}
        missing_evidence: list[str] = []
        conflicts: list[dict[str, Any]] = []

        # 1. Gather outputs & verify evidence
        for t in task_list:
            if t.status == OrchestrationTaskStatus.COMPLETED:
                agent_outputs[t.task_id] = {
                    "agent_id": t.agent_id,
                    "action": t.action,
                    "output": t.output,
                    "evidence": t.evidence,
                }
                # Check expected artifacts
                for art in t.expected_artifacts:
                    if art not in t.output and art not in t.evidence:
                        missing_evidence.append(f"Task '{t.task_id}' missing expected artifact '{art}'")

        # 2. Detect conflicts across common keys in completed outputs
        keys_seen: dict[str, list[tuple[str, Any]]] = {}
        for tid, data in agent_outputs.items():
            out = data.get("output", {})
            if isinstance(out, dict):
                for k, v in out.items():
                    if k in ("verdict", "decision", "status", "version", "passed", "result"):
                        keys_seen.setdefault(k, []).append((tid, v))

        for k, occurrences in keys_seen.items():
            unique_values = {str(v).strip().lower() for _, v in occurrences}
            if len(unique_values) > 1:
                conflicts.append({
                    "conflicting_key": k,
                    "tasks_involved": [
                        {"task_id": tid, "value": val} for tid, val in occurrences
                    ],
                    "details": f"Discrepancy detected for key '{k}': values vary across agents",
                })

        summary_parts = [
            f"Orchestration Session: {session_id}",
            f"Tasks: {completed}/{total} completed, {failed} failed.",
        ]
        if missing_evidence:
            summary_parts.append(f"Evidence Warnings: {len(missing_evidence)} missing artifacts.")
        if conflicts:
            summary_parts.append(f"Conflicts Detected: {len(conflicts)} discrepancies found.")

        is_successful = failed == 0 and len(conflicts) == 0

        return AggregationResult(
            session_id=session_id,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            agent_outputs=agent_outputs,
            conflicts_detected=conflicts,
            missing_evidence=missing_evidence,
            consolidated_summary=" | ".join(summary_parts),
            is_successful=is_successful,
        )
