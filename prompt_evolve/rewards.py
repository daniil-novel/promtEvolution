"""Reward functions for trajectory-based prompt optimization."""

from __future__ import annotations

from .metrics import average_score, format_pass_rate, pass_at_1
from .models import PromptRunResult, RewardWeights


def cost_efficiency_score(result: PromptRunResult, *, token_budget: int = 100_000) -> float:
    total = result.usage.get("total_tokens")
    if total is None:
        total = result.usage.get("prompt_tokens", 0) + result.usage.get("completion_tokens", 0)
    if not total:
        return 1.0
    return max(0.0, 1.0 - float(total) / token_budget)


def tool_usage_quality_score(result: PromptRunResult) -> float:
    if not result.responses:
        return 0.0
    provider_errors = sum(1 for value in result.responses.values() if value.startswith("Provider error:"))
    return max(0.0, 1.0 - provider_errors / len(result.responses))


def reward_score(result: PromptRunResult, *, weights: RewardWeights | None = None) -> float:
    current = (weights or RewardWeights()).normalized()
    return (
        pass_at_1(result.evaluations) * current.task_success
        + format_pass_rate(result.evaluations) * current.format_compliance
        + average_score(result.evaluations) * current.factuality
        + tool_usage_quality_score(result) * current.tool_usage_quality
        + cost_efficiency_score(result) * current.cost_efficiency
    )
