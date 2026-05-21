"""SCOPE guideline generation and prompt updates."""

from __future__ import annotations

from .llm import generate_json
from .models import EvaluationResult, LLMProvider, PromptRunResult


def analyze_failures(result: PromptRunResult) -> list[EvaluationResult]:
    return [item for item in result.evaluations if not item.passed]


def generate_guidelines(
    result: PromptRunResult,
    provider: LLMProvider,
    *,
    model: str | None = None,
    reasoning: str | None = None,
) -> dict[str, list[str]]:
    failures = analyze_failures(result)
    messages = [
        {
            "role": "system",
            "content": "Generate short SCOPE corrective and enhancement guidelines as JSON.",
        },
        {
            "role": "user",
            "content": (
                f"Prompt: {result.candidate.content}\n"
                f"Failed evaluations: {[item.to_dict() for item in failures]}\n"
                "Return JSON with corrective and enhancement arrays."
            ),
        },
    ]
    try:
        data = generate_json(provider, messages, model=model, reasoning=reasoning)
    except Exception:
        data = {
            "corrective": ["Validate the final answer against every evaluation criterion."],
            "enhancement": ["State output format and anti-hallucination rules explicitly."],
        }
    corrective = [str(item) for item in data.get("corrective", []) if str(item).strip()]
    enhancement = [str(item) for item in data.get("enhancement", []) if str(item).strip()]
    return {
        "corrective": dedupe_guidelines(corrective),
        "enhancement": dedupe_guidelines(enhancement),
    }


def dedupe_guidelines(guidelines: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for guideline in guidelines:
        normalized = guideline.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(guideline.strip())
    return result


def self_check_guidelines(guidelines: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        key: [
            guideline
            for guideline in dedupe_guidelines(values)
            if len(guideline.split()) >= 3 and len(guideline) <= 240
        ]
        for key, values in guidelines.items()
    }


def update_prompt_with_guidelines(prompt: str, guidelines: dict[str, list[str]]) -> str:
    base_prompt = prompt.split("SCOPE Guidelines:", 1)[0].rstrip()
    lines = [base_prompt, "", "SCOPE Guidelines:"]
    existing: set[str] = set()
    for label in ("corrective", "enhancement"):
        for guideline in guidelines.get(label, []):
            normalized = guideline.strip().lower()
            if normalized and normalized not in existing:
                existing.add(normalized)
                lines.append(f"- {guideline}")
    return "\n".join(lines).strip() + "\n"
