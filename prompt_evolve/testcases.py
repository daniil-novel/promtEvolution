"""Test case loading, validation, generation, and self-check."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ConfigError
from .llm import generate_json
from .models import LLMProvider, TestCase

REQUIRED_FIELDS = {
    "id",
    "name",
    "type",
    "priority",
    "input",
    "expected_behavior",
    "evaluation_criteria",
}

TYPE_DISTRIBUTION = [
    "happy_path",
    "happy_path",
    "complex",
    "edge_case",
    "negative",
    "format_compliance",
    "adversarial",
    "regression",
]


def testcase_from_dict(data: dict[str, Any]) -> TestCase:
    missing = REQUIRED_FIELDS - set(data)
    if missing:
        raise ConfigError(f"Invalid tests file format: missing {', '.join(sorted(missing))}")
    criteria = data["evaluation_criteria"]
    if not isinstance(criteria, list) or not all(isinstance(item, str) and item for item in criteria):
        raise ConfigError("Invalid tests file format: evaluation_criteria must be a list of strings")
    return TestCase(
        id=str(data["id"]),
        name=str(data["name"]),
        type=str(data["type"]),
        priority=str(data["priority"]),
        input=str(data["input"]),
        expected_behavior=str(data["expected_behavior"]),
        evaluation_criteria=list(criteria),
    )


def validate_testcases(items: list[dict[str, Any]] | list[TestCase]) -> list[TestCase]:
    if not isinstance(items, list):
        raise ConfigError("Invalid tests file format")
    result = [item if isinstance(item, TestCase) else testcase_from_dict(item) for item in items]
    if not result:
        raise ConfigError("Invalid tests file format: at least one test case is required")
    return dedupe_testcases(result)


def load_testcases(path: str | Path) -> list[TestCase]:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise ConfigError("Invalid tests file format")
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError("Invalid tests file format") from exc
    return validate_testcases(data)


def save_testcases(testcases: list[TestCase], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([case.to_dict() for case in testcases], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output


def dedupe_testcases(testcases: list[TestCase]) -> list[TestCase]:
    seen: set[tuple[str, str]] = set()
    unique: list[TestCase] = []
    for case in testcases:
        key = (case.input.strip().lower(), case.expected_behavior.strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append(case)
    return unique


def _fallback_case(index: int, task: str) -> TestCase:
    case_type = TYPE_DISTRIBUTION[(index - 1) % len(TYPE_DISTRIBUTION)]
    priority = "high" if case_type in {"happy_path", "format_compliance"} else "medium"
    return TestCase(
        id=f"TC-{index:03d}",
        name=f"Generated {case_type.replace('_', ' ')} {index}",
        type=case_type,
        priority=priority,
        input=f"Input example {index} for: {task[:80]}",
        expected_behavior="The prompt should satisfy the task requirements without adding unsupported facts.",
        evaluation_criteria=[
            "Preserves user intent",
            "Follows the requested format",
            "Does not hallucinate",
        ],
    )


def generate_testcases(
    task: str,
    provider: LLMProvider,
    *,
    count: int,
    model: str | None = None,
    reasoning: str | None = None,
) -> list[TestCase]:
    if count <= 0:
        return []
    messages = [
        {
            "role": "system",
            "content": "Generate prompt evaluation test cases as JSON array.",
        },
        {
            "role": "user",
            "content": f"Task:\n{task}\nGenerate {count} test cases with required fields.",
        },
    ]
    try:
        data = generate_json(provider, messages, model=model, reasoning=reasoning)
        generated = validate_testcases(data if isinstance(data, list) else [data])
    except Exception:
        generated = []
    while len(generated) < count:
        generated.append(_fallback_case(len(generated) + 1, task))
    return generated[:count]


def ensure_target_testcases(
    task: str,
    existing: list[TestCase] | None,
    provider: LLMProvider,
    *,
    target_tests: int,
    user_tests_only: bool = False,
    model: str | None = None,
    reasoning: str | None = None,
) -> list[TestCase]:
    testcases = dedupe_testcases(existing or [])
    if user_tests_only:
        return testcases
    missing = target_tests - len(testcases)
    if missing > 0:
        generated = generate_testcases(
            task,
            provider,
            count=missing,
            model=model,
            reasoning=reasoning,
        )
        offset = len(testcases)
        renumbered = [
            TestCase(
                id=f"TC-{offset + index:03d}",
                name=case.name,
                type=case.type,
                priority=case.priority,
                input=case.input,
                expected_behavior=case.expected_behavior,
                evaluation_criteria=case.evaluation_criteria,
            )
            for index, case in enumerate(generated, start=1)
        ]
        testcases.extend(renumbered)
    return dedupe_testcases(testcases)[:target_tests]


def self_check_testcases(testcases: list[TestCase]) -> list[str]:
    warnings: list[str] = []
    ids = [case.id for case in testcases]
    if len(ids) != len(set(ids)):
        warnings.append("Duplicate test IDs detected.")
    for case in testcases:
        if len(case.evaluation_criteria) < 2:
            warnings.append(f"{case.id} has too few evaluation criteria.")
        if len(case.input.strip()) < 3:
            warnings.append(f"{case.id} has an overly short input.")
    return warnings


testcase_from_dict.__test__ = False
