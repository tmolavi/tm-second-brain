"""Data models for TM Agent Orchestration (AutoSwarm-inspired, zero-dependency)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class OrchestrationTaskStatus(str, Enum):
    """Execution lifecycle status for an orchestrated task unit."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED_ON_APPROVAL = "blocked_on_approval"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    """Risk tier for sensitive operation gating."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentRole:
    """Agent role definition within the team capability catalogue."""

    role_id: str
    name: str
    description: str
    capabilities: list[str] = field(default_factory=list)
    runtime: str = "generic"  # antigravity, hermes, hamzad, codex, claude-code, generic
    available: bool = True
    fallback_role_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentRole:
        return cls(**data)


@dataclass
class TaskUnit:
    """Atomic unit of delegation binding goals, agent, constraints, and acceptance criteria."""

    name: str
    action: str
    agent_id: str  # specific agent or role_id
    inputs: dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: f"tsk_{uuid.uuid4().hex[:8]}")
    parent_id: str | None = None
    status: OrchestrationTaskStatus = OrchestrationTaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    requires_approval: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    approval_ticket_id: str | None = None
    expected_artifacts: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    fallback_agent_id: str | None = None
    max_retries: int = 2
    retry_count: int = 0
    timeout_seconds: float = 60.0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    output: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["risk_level"] = self.risk_level.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskUnit:
        d = dict(data)
        d["status"] = OrchestrationTaskStatus(d.get("status", OrchestrationTaskStatus.PENDING.value))
        d["risk_level"] = RiskLevel(d.get("risk_level", RiskLevel.LOW.value))
        return cls(**d)


@dataclass
class TaskEnvelope:
    """Structured, secret-redacted inter-agent message envelope."""

    task_id: str
    session_id: str
    source_agent: str
    target_agent: str
    payload: dict[str, Any]
    parent_task_id: str | None = None
    context_summary: str = ""
    timestamp: float = field(default_factory=time.time)
    envelope_id: str = field(default_factory=lambda: f"env_{uuid.uuid4().hex[:8]}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskEnvelope:
        return cls(**data)


@dataclass
class ApprovalRequest:
    """Approval request ticket for sensitive operations."""

    ticket_id: str
    task_id: str
    action: str
    reason: str
    target_resource: str
    risk_level: RiskLevel
    status: str = "pending"  # pending, approved, rejected, expired
    approver: str | None = None
    decision_reason: str | None = None
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600.0)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["risk_level"] = self.risk_level.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApprovalRequest:
        d = dict(data)
        d["risk_level"] = RiskLevel(d.get("risk_level", RiskLevel.HIGH.value))
        return cls(**d)


@dataclass
class ExecutionRecord:
    """Structured audit evidence of a task execution."""

    record_id: str
    session_id: str
    task_id: str
    agent_id: str
    action: str
    runtime: str
    status: OrchestrationTaskStatus
    started_at: float
    finished_at: float
    duration_seconds: float
    evidence_refs: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionRecord:
        d = dict(data)
        d["status"] = OrchestrationTaskStatus(d.get("status", OrchestrationTaskStatus.COMPLETED.value))
        return cls(**d)


@dataclass
class AggregationResult:
    """Aggregated output from multiple executed tasks with conflict detection."""

    session_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    agent_outputs: dict[str, dict[str, Any]]
    conflicts_detected: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    consolidated_summary: str = ""
    is_successful: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
