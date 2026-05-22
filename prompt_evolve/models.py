"""Shared data models for prompt evolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResponse:
    content: str
    usage: dict[str, int | float] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    name: str

    def check_configured(self) -> None:
        """Raise a clear error when provider credentials are missing."""

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        reasoning: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        """Generate a response from chat messages."""


@dataclass(frozen=True)
class TestCase:
    id: str
    name: str
    type: str
    priority: str
    input: str
    expected_behavior: str
    evaluation_criteria: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "priority": self.priority,
            "input": self.input,
            "expected_behavior": self.expected_behavior,
            "evaluation_criteria": list(self.evaluation_criteria),
        }


@dataclass(frozen=True)
class EvaluationResult:
    test_case_id: str
    passed: bool
    score: float
    reason: str
    failed_criteria: list[str] = field(default_factory=list)
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_case_id": self.test_case_id,
            "passed": self.passed,
            "score": self.score,
            "reason": self.reason,
            "failed_criteria": list(self.failed_criteria),
            "error_type": self.error_type,
        }


@dataclass(frozen=True)
class PromptCandidate:
    id: str
    content: str
    iteration: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "content": self.content, "iteration": self.iteration}


@dataclass
class PromptRunResult:
    candidate: PromptCandidate
    evaluations: list[EvaluationResult]
    responses: dict[str, str]
    usage: dict[str, int | float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict(),
            "evaluations": [item.to_dict() for item in self.evaluations],
            "responses": dict(self.responses),
            "usage": dict(self.usage),
        }


@dataclass(frozen=True)
class MetricsSnapshot:
    pass_at_1: float
    pass_at_k: float
    format_pass_rate: float
    critical_pass_rate: float
    average_score: float
    improvement_delta: float
    failed_tests_count: int
    token_usage: dict[str, int | float] = field(default_factory=dict)
    estimated_cost: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass@1": self.pass_at_1,
            "pass@k": self.pass_at_k,
            "format_pass_rate": self.format_pass_rate,
            "critical_pass_rate": self.critical_pass_rate,
            "average_score": self.average_score,
            "improvement_delta": self.improvement_delta,
            "failed_tests_count": self.failed_tests_count,
            "token_usage": dict(self.token_usage),
            "estimated_cost": self.estimated_cost,
        }


class SystemMetricsCollector(Protocol):
    def collect(self) -> dict[str, Any]:
        """Return model/system metrics collected by an external tool."""


class NoopSystemMetricsCollector:
    def collect(self) -> dict[str, Any]:
        return {}


@dataclass(frozen=True)
class TaskSpec:
    objective: str
    input_contract: str
    output_contract: str
    success_criteria: list[str]
    failure_modes: list[str]
    clarification_questions: list[str] = field(default_factory=list)
    tool_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "input_contract": self.input_contract,
            "output_contract": self.output_contract,
            "success_criteria": list(self.success_criteria),
            "failure_modes": list(self.failure_modes),
            "clarification_questions": list(self.clarification_questions),
            "tool_requirements": list(self.tool_requirements),
        }


@dataclass(frozen=True)
class ToolPolicy:
    allowed_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    approval_required: list[str] = field(default_factory=list)
    production_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_tools": list(self.allowed_tools),
            "blocked_tools": list(self.blocked_tools),
            "approval_required": list(self.approval_required),
            "production_notes": list(self.production_notes),
        }


@dataclass(frozen=True)
class RewardWeights:
    task_success: float = 0.35
    format_compliance: float = 0.20
    factuality: float = 0.25
    tool_usage_quality: float = 0.10
    cost_efficiency: float = 0.10

    def normalized(self) -> "RewardWeights":
        total = (
            self.task_success
            + self.format_compliance
            + self.factuality
            + self.tool_usage_quality
            + self.cost_efficiency
        )
        if total <= 0:
            return RewardWeights()
        return RewardWeights(
            task_success=self.task_success / total,
            format_compliance=self.format_compliance / total,
            factuality=self.factuality / total,
            tool_usage_quality=self.tool_usage_quality / total,
            cost_efficiency=self.cost_efficiency / total,
        )

    def to_dict(self) -> dict[str, float]:
        normalized = self.normalized()
        return {
            "task_success": normalized.task_success,
            "format_compliance": normalized.format_compliance,
            "factuality": normalized.factuality,
            "tool_usage_quality": normalized.tool_usage_quality,
            "cost_efficiency": normalized.cost_efficiency,
        }


TestCase.__test__ = False
EvaluationResult.__test__ = False
PromptCandidate.__test__ = False
PromptRunResult.__test__ = False
MetricsSnapshot.__test__ = False
TaskSpec.__test__ = False
ToolPolicy.__test__ = False
RewardWeights.__test__ = False
