"""Prompt execution and evaluation."""

from __future__ import annotations

from .llm import generate_json, generate_text
from .metrics import merge_usage
from .models import EvaluationResult, LLMProvider, PromptCandidate, PromptRunResult, TestCase
from .providers import FatalProviderError


def evaluate_response(
    test_case: TestCase,
    response: str,
    provider: LLMProvider,
    *,
    model: str | None = None,
    reasoning: str | None = None,
) -> EvaluationResult:
    messages = [
        {
            "role": "system",
            "content": "Evaluate the model response against the test case. Return JSON.",
        },
        {
            "role": "user",
            "content": (
                "Evaluate this response.\n"
                f"Test case: {test_case.to_dict()}\n"
                f"Response: {response}\n"
                "Return passed, score, reason, failed_criteria, error_type."
            ),
        },
    ]
    try:
        data = generate_json(provider, messages, model=model, reasoning=reasoning)
    except Exception:
        failed = [
            criterion
            for criterion in test_case.evaluation_criteria
            if criterion.lower().split()[0] not in response.lower()
        ]
        passed = not failed
        score = 1.0 if passed else max(0.0, 1.0 - len(failed) / max(len(test_case.evaluation_criteria), 1))
        data = {
            "passed": passed,
            "score": score,
            "reason": "Heuristic evaluator result.",
            "failed_criteria": failed,
            "error_type": None if passed else "criteria_mismatch",
        }
    return EvaluationResult(
        test_case_id=test_case.id,
        passed=bool(data.get("passed", False)),
        score=float(data.get("score", 0.0)),
        reason=str(data.get("reason", "")),
        failed_criteria=list(data.get("failed_criteria") or []),
        error_type=data.get("error_type"),
    )


def run_candidate(
    candidate: PromptCandidate,
    testcases: list[TestCase],
    provider: LLMProvider,
    *,
    model: str | None = None,
    reasoning: str | None = None,
    self_check: bool = True,
) -> PromptRunResult:
    evaluations: list[EvaluationResult] = []
    responses: dict[str, str] = {}
    usage = {}
    for case in testcases:
        messages = [
            {"role": "system", "content": candidate.content},
            {"role": "user", "content": case.input},
        ]
        try:
            answer = provider.generate(messages, model=model, reasoning=reasoning)
            response_text = answer.content
            merge_usage(usage, answer.usage)
        except FatalProviderError:
            raise
        except Exception as exc:
            response_text = f"Provider error: {exc}"
        responses[case.id] = response_text
        result = evaluate_response(case, response_text, provider, model=model, reasoning=reasoning)
        if self_check:
            result = self_check_evaluation(result)
        evaluations.append(result)
    return PromptRunResult(candidate=candidate, evaluations=evaluations, responses=responses, usage=usage)


def self_check_evaluation(result: EvaluationResult) -> EvaluationResult:
    score = min(1.0, max(0.0, result.score))
    passed = result.passed and score >= 0.5
    if not passed and not result.error_type:
        return EvaluationResult(
            test_case_id=result.test_case_id,
            passed=False,
            score=score,
            reason=result.reason or "Self-check marked low-confidence result as failed.",
            failed_criteria=result.failed_criteria,
            error_type="self_check_failure",
        )
    return EvaluationResult(
        test_case_id=result.test_case_id,
        passed=passed,
        score=score,
        reason=result.reason,
        failed_criteria=result.failed_criteria,
        error_type=result.error_type,
    )
