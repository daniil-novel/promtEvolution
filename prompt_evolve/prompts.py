"""Prompt candidate generation and selection."""

from __future__ import annotations

from .llm import generate_text
from .models import LLMProvider, PromptCandidate, PromptRunResult


def build_seed_prompt(task: str) -> str:
    return (
        "You are a reliable AI assistant.\n"
        f"Goal: {task.strip()}\n"
        "Rules:\n"
        "- Preserve user intent and facts.\n"
        "- Follow the requested output format.\n"
        "- Handle happy path, edge cases, and malformed inputs.\n"
        "- Do not hallucinate or add unsupported details.\n"
        "- Before answering, self-check the result against the task requirements.\n"
    )


def generate_prompt_candidates(
    task: str,
    baseline_prompt: str | None,
    provider: LLMProvider,
    *,
    count: int,
    iteration: int,
    model: str | None = None,
    reasoning: str | None = None,
) -> list[PromptCandidate]:
    candidates: list[PromptCandidate] = []
    if baseline_prompt:
        candidates.append(PromptCandidate(id=f"iteration_{iteration}_baseline", content=baseline_prompt, iteration=iteration))
    while len(candidates) < count:
        candidate_number = len(candidates) + 1
        messages = [
            {
                "role": "system",
                "content": "Create a production-ready system prompt with role, goal, rules, constraints, output format, and self-check.",
            },
            {
                "role": "user",
                "content": (
                    f"Task:\n{task}\n"
                    f"Baseline prompt:\n{baseline_prompt or 'Create from scratch.'}\n"
                    f"Create candidate {candidate_number}."
                ),
            },
        ]
        try:
            content = generate_text(provider, messages, model=model, reasoning=reasoning)
        except Exception:
            content = build_seed_prompt(task)
        candidates.append(
            PromptCandidate(
                id=f"iteration_{iteration}_candidate_{candidate_number}",
                content=content,
                iteration=iteration,
            )
        )
    return candidates[:count]


def select_best_prompt(results: list[PromptRunResult]) -> PromptRunResult:
    if not results:
        raise ValueError("No prompt results to select from")

    def key(result: PromptRunResult) -> tuple[float, float, int, int]:
        total = max(len(result.evaluations), 1)
        pass_rate = sum(1 for item in result.evaluations if item.passed) / total
        critical = [
            item
            for item in result.evaluations
            if item.test_case_id and item.error_type != "non_critical_marker"
        ]
        critical_rate = sum(1 for item in critical if item.passed) / max(len(critical), 1)
        avg_score = sum(item.score for item in result.evaluations) / total
        format_violations = sum(1 for item in result.evaluations if item.error_type == "format_violation")
        return (pass_rate, critical_rate, avg_score, -format_violations, -len(result.candidate.content))

    return max(results, key=key)
