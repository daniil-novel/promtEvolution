from prompt_evolve.evaluator import (
    evaluate_response,
    heuristic_evaluate_response,
    run_candidate,
    self_check_evaluation,
)
from prompt_evolve.metrics import (
    aggregate_usage,
    average_score,
    build_metrics,
    critical_pass_rate,
    estimated_cost,
    failed_tests_count,
    format_pass_rate,
    improvement_delta,
    merge_usage,
    pass_at_1,
    pass_at_k,
)
from prompt_evolve.models import EvaluationResult, PromptCandidate, PromptRunResult, TestCase
from prompt_evolve.prompts import build_seed_prompt, generate_prompt_candidates, select_best_prompt
from prompt_evolve.providers import MockProvider
from prompt_evolve.providers import FatalProviderError
from prompt_evolve.scope import (
    analyze_failures,
    dedupe_guidelines,
    generate_guidelines,
    self_check_guidelines,
    update_prompt_with_guidelines,
)


def case(case_id="TC-001", priority="high"):
    return TestCase(
        id=case_id,
        name="Case",
        type="happy_path",
        priority=priority,
        input="Use Markdown",
        expected_behavior="Markdown output",
        evaluation_criteria=["Uses Markdown", "Preserves facts"],
    )


def result(candidate_id, passed, score=1.0, error_type=None):
    candidate = PromptCandidate(candidate_id, "Prompt")
    return PromptRunResult(
        candidate=candidate,
        evaluations=[EvaluationResult("TC-001", passed, score, "Reason", [], error_type)],
        responses={"TC-001": "Response"},
        usage={"prompt_tokens": 2, "completion_tokens": 3},
    )


def test_build_and_generate_prompt_candidates():
    assert "НИКОГДА" in build_seed_prompt("Task")
    assert "<self_check>" in build_seed_prompt("Task")
    candidates = generate_prompt_candidates("Task", None, MockProvider(), count=2, iteration=1)
    assert len(candidates) == 2
    assert candidates[0].id.startswith("iteration_1_candidate")
    assert "## Роль" in candidates[0].content


def test_select_best_prompt_prefers_pass_rate():
    best = select_best_prompt([result("bad", False, 0.2), result("good", True, 0.9)])
    assert best.candidate.id == "good"


def test_select_best_prompt_prefers_structured_candidate_over_equal_baseline():
    baseline = result("iteration_1_baseline", True, 0.9)
    structured = result("iteration_1_candidate_1", True, 0.9)
    structured.candidate = PromptCandidate(
        "iteration_1_candidate_1",
        "## Роль\n## Задача\n## Правила\n## Формат ответа\n<self_check>\ndecision reroute_to_coordinator continue_to_final",
    )
    best = select_best_prompt([baseline, structured])
    assert best.candidate.id == "iteration_1_candidate_1"


def test_evaluate_response_and_run_candidate():
    provider = MockProvider()
    evaluation = evaluate_response(case(), "Markdown with action items", provider)
    assert evaluation.passed is True
    run = run_candidate(PromptCandidate("p1", "Prompt"), [case()], provider)
    assert run.evaluations[0].test_case_id == "TC-001"


def test_run_candidate_supports_heuristic_eval_and_status():
    messages = []
    run = run_candidate(
        PromptCandidate("p1", "Prompt"),
        [case()],
        MockProvider(),
        llm_evaluate=False,
        status=messages.append,
    )
    assert run.evaluations[0].reason == "Heuristic evaluator result."
    assert any("running test" in item for item in messages)


def test_heuristic_evaluate_response():
    evaluation = heuristic_evaluate_response(case(), "Uses Markdown and preserves facts")
    assert evaluation.test_case_id == "TC-001"


def test_run_candidate_stops_on_fatal_provider_error():
    class FatalProvider(MockProvider):
        def generate(self, messages, *, model=None, reasoning=None, response_format=None):
            raise FatalProviderError("Key limit exceeded")

    import pytest

    with pytest.raises(FatalProviderError):
        run_candidate(PromptCandidate("p1", "Prompt"), [case(), case("TC-002")], FatalProvider())


def test_self_check_evaluation_marks_low_score_failed():
    checked = self_check_evaluation(EvaluationResult("TC-1", True, 0.2, "", []))
    assert checked.passed is False
    assert checked.error_type == "self_check_failure"


def test_metrics_functions():
    evaluations = [
        EvaluationResult("TC-001", True, 1.0, ""),
        EvaluationResult("TC-002", False, 0.2, "", [], "format_violation"),
    ]
    assert pass_at_1(evaluations) == 0.5
    assert format_pass_rate(evaluations) == 0.5
    assert average_score(evaluations) == 0.6
    assert failed_tests_count(evaluations) == 1
    assert improvement_delta(0.4, 0.7) == 0.29999999999999993
    assert critical_pass_rate(evaluations, [case("TC-001", "high"), case("TC-002", "low")]) == 1.0


def test_pass_at_k_and_build_metrics():
    first = result("a", False, 0.1)
    second = result("b", True, 0.9)
    assert pass_at_k([first, second], k=2) == 1.0
    metrics = build_metrics(second, [first, second], [case()], k=2, baseline_pass=0.0)
    assert metrics.pass_at_1 == 1.0
    assert metrics.token_usage["prompt_tokens"] == 4


def test_usage_and_cost():
    usage = aggregate_usage([result("a", True), result("b", True)])
    assert usage["completion_tokens"] == 6
    assert estimated_cost({"total_tokens": 1000}, per_1k_tokens=0.5) == 0.5


def test_usage_merge_flattens_nested_provider_details():
    usage = merge_usage(
        {},
        {
            "prompt_tokens": 2,
            "completion_tokens": 3,
            "completion_tokens_details": {"reasoning_tokens": 4},
            "ignored": {"nested": "text"},
        },
    )
    merge_usage(usage, {"prompt_tokens": 5, "completion_tokens_details": {"reasoning_tokens": 6}})
    assert usage["prompt_tokens"] == 7
    assert usage["completion_tokens"] == 3
    assert usage["completion_tokens_details.reasoning_tokens"] == 10
    assert "ignored.nested" not in usage


def test_run_candidate_accepts_nested_usage_details():
    class NestedUsageProvider(MockProvider):
        def generate(self, messages, *, model=None, reasoning=None, response_format=None):
            response = super().generate(messages, model=model, reasoning=reasoning, response_format=response_format)
            response.usage["completion_tokens_details"] = {"reasoning_tokens": 2}
            return response

    run = run_candidate(PromptCandidate("p1", "Prompt"), [case()], NestedUsageProvider())
    assert run.usage["completion_tokens_details.reasoning_tokens"] == 2


def test_scope_guidelines_and_update_prompt():
    failed = result("bad", False, 0.1)
    assert analyze_failures(failed)
    guidelines = generate_guidelines(failed, MockProvider())
    assert guidelines["corrective"]
    checked = self_check_guidelines({"corrective": ["too short", "Validate output format carefully."], "enhancement": []})
    assert checked["corrective"] == ["Validate output format carefully."]
    assert dedupe_guidelines(["A useful rule", "A useful rule"]) == ["A useful rule"]
    updated = update_prompt_with_guidelines("Prompt", {"corrective": ["Fix format"], "enhancement": []})
    assert "SCOPE Guidelines" in updated


def test_update_prompt_with_guidelines_replaces_previous_scope_block():
    updated = update_prompt_with_guidelines(
        "Prompt\n\nSCOPE Guidelines:\n- Old duplicated rule\n",
        {"corrective": ["New rule"], "enhancement": ["New rule"]},
    )
    assert "Old duplicated rule" not in updated
    assert updated.count("SCOPE Guidelines:") == 1
    assert updated.count("New rule") == 1
