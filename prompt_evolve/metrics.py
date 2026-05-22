"""Metric calculations for prompt evolution."""

from __future__ import annotations

from typing import Any

from .models import EvaluationResult, MetricsSnapshot, PromptRunResult, TestCase


def pass_at_1(evaluations: list[EvaluationResult]) -> float:
    if not evaluations:
        return 0.0
    return sum(1 for item in evaluations if item.passed) / len(evaluations)


def pass_at_k(results: list[PromptRunResult], *, k: int) -> float:
    selected = results[:k]
    if not selected:
        return 0.0
    test_ids = {item.test_case_id for result in selected for item in result.evaluations}
    if not test_ids:
        return 0.0
    passed = 0
    for test_id in test_ids:
        if any(
            evaluation.test_case_id == test_id and evaluation.passed
            for result in selected
            for evaluation in result.evaluations
        ):
            passed += 1
    return passed / len(test_ids)


def format_pass_rate(evaluations: list[EvaluationResult]) -> float:
    if not evaluations:
        return 0.0
    passed = sum(1 for item in evaluations if item.error_type != "format_violation")
    return passed / len(evaluations)


def critical_pass_rate(evaluations: list[EvaluationResult], testcases: list[TestCase]) -> float:
    priorities = {case.id: case.priority for case in testcases}
    critical = [item for item in evaluations if priorities.get(item.test_case_id) in {"critical", "high"}]
    if not critical:
        return pass_at_1(evaluations)
    return sum(1 for item in critical if item.passed) / len(critical)


def average_score(evaluations: list[EvaluationResult]) -> float:
    if not evaluations:
        return 0.0
    return sum(item.score for item in evaluations) / len(evaluations)


def improvement_delta(baseline: float | None, final: float) -> float:
    return final - (baseline or 0.0)


def failed_tests_count(evaluations: list[EvaluationResult]) -> int:
    return sum(1 for item in evaluations if not item.passed)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def merge_usage(usage: dict[str, Any], update: dict[str, Any], *, prefix: str = "") -> dict[str, Any]:
    for key, value in update.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if _is_number(value):
            current = usage.get(name, 0)
            usage[name] = (current if _is_number(current) else 0) + value
        elif isinstance(value, dict):
            merge_usage(usage, value, prefix=name)
    return usage


def aggregate_usage(results: list[PromptRunResult]) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    for result in results:
        merge_usage(usage, result.usage)
    return usage


def estimated_cost(usage: dict[str, Any], *, per_1k_tokens: float = 0.0) -> float | None:
    total = usage.get("total_tokens")
    if total is None:
        prompt = usage.get("prompt_tokens", 0)
        completion = usage.get("completion_tokens", 0)
        total = prompt + completion
    if not _is_number(total) or not total or per_1k_tokens <= 0:
        return None
    return float(total) / 1000 * per_1k_tokens


def build_metrics(
    best: PromptRunResult,
    all_results: list[PromptRunResult],
    testcases: list[TestCase],
    *,
    k: int,
    baseline_pass: float | None = None,
) -> MetricsSnapshot:
    final_pass = pass_at_1(best.evaluations)
    usage = aggregate_usage(all_results)
    return MetricsSnapshot(
        pass_at_1=final_pass,
        pass_at_k=pass_at_k(all_results, k=k),
        format_pass_rate=format_pass_rate(best.evaluations),
        critical_pass_rate=critical_pass_rate(best.evaluations, testcases),
        average_score=average_score(best.evaluations),
        improvement_delta=improvement_delta(baseline_pass, final_pass),
        failed_tests_count=failed_tests_count(best.evaluations),
        token_usage=usage,
        estimated_cost=estimated_cost(usage),
    )
