"""Report writers for prompt evolution runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import MetricsSnapshot, PromptRunResult, TestCase


def ensure_run_dirs(out_dir: str | Path) -> Path:
    base = Path(out_dir)
    for child in ("candidates", "evaluations", "logs"):
        (base / child).mkdir(parents=True, exist_ok=True)
    return base


def write_run_log(out_dir: str | Path, lines: list[str]) -> Path:
    base = ensure_run_dirs(out_dir)
    path = base / "logs" / "run.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_candidates(out_dir: str | Path, results: list[PromptRunResult]) -> list[Path]:
    base = ensure_run_dirs(out_dir)
    paths: list[Path] = []
    for result in results:
        path = base / "candidates" / f"{result.candidate.id}.md"
        path.write_text(result.candidate.content, encoding="utf-8")
        paths.append(path)
    return paths


def write_evaluations(out_dir: str | Path, iteration: int, results: list[PromptRunResult]) -> Path:
    base = ensure_run_dirs(out_dir)
    path = base / "evaluations" / f"iteration_{iteration}.json"
    path.write_text(
        json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def write_final_prompt(out_dir: str | Path, prompt: str) -> Path:
    base = ensure_run_dirs(out_dir)
    path = base / "final_prompt.md"
    path.write_text(prompt, encoding="utf-8")
    return path


def report_payload(
    *,
    task: str,
    provider: str,
    model: str | None,
    baseline_prompt: str | None,
    final_prompt: str,
    metrics: MetricsSnapshot,
    testcases: list[TestCase],
    best_result: PromptRunResult,
    guidelines: list[dict[str, list[str]]],
    system_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "task": task,
        "provider": provider,
        "model": model,
        "baseline_prompt": baseline_prompt,
        "final_prompt": final_prompt,
        "metrics": metrics.to_dict(),
        "test_cases": [case.to_dict() for case in testcases],
        "best_result": best_result.to_dict(),
        "guidelines": guidelines,
        "system_metrics": system_metrics or {},
    }


def write_json_report(out_dir: str | Path, payload: dict[str, Any]) -> Path:
    base = ensure_run_dirs(out_dir)
    path = base / "report.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_markdown_report(out_dir: str | Path, payload: dict[str, Any]) -> Path:
    base = ensure_run_dirs(out_dir)
    metrics = payload["metrics"]
    failed = [
        item
        for item in payload["best_result"]["evaluations"]
        if not item["passed"]
    ]
    guideline_lines: list[str] = []
    for item in payload.get("guidelines", []):
        for label, values in item.items():
            for guideline in values:
                guideline_lines.append(f"- {label}: {guideline}")
    workbench = payload.get("workbench") or {}
    workbench_lines = []
    if workbench:
        workbench_lines = [
            "## 11. Workbench Artifacts",
            "",
            f"Strategy: `{workbench.get('strategy')}`",
            f"Population size: `{workbench.get('population_size')}`",
            f"Generations: `{workbench.get('generations')}`",
            "",
            "\n".join(f"- `{item}`" for item in workbench.get("artifacts", [])),
            "",
        ]
    content = "\n".join(
        [
            "# Prompt Evolution Report",
            "",
            "## 1. Summary",
            "",
            f"Provider: `{payload['provider']}`",
            f"Model: `{payload.get('model') or 'default'}`",
            "",
            "## 2. Input Task",
            "",
            payload["task"],
            "",
            "## 3. Provider and Model",
            "",
            f"{payload['provider']} / {payload.get('model') or 'default'}",
            "",
            "## 4. Baseline Prompt",
            "",
            payload.get("baseline_prompt") or "No baseline prompt was provided.",
            "",
            "## 5. Final Prompt",
            "",
            payload["final_prompt"],
            "",
            "## 6. Metrics",
            "",
            "| Metric | Final |",
            "|---|---:|",
            f"| pass@1 | {metrics['pass@1']:.2f} |",
            f"| pass@k | {metrics['pass@k']:.2f} |",
            f"| average_score | {metrics['average_score']:.2f} |",
            f"| failed_tests_count | {metrics['failed_tests_count']} |",
            "",
            "## 7. Test Cases Summary",
            "",
            f"Total test cases: {len(payload['test_cases'])}",
            "",
            "## 8. Failed Tests",
            "",
            "\n".join(f"- {item['test_case_id']}: {item['reason']}" for item in failed) or "No failed tests.",
            "",
            "## 9. Generated SCOPE Guidelines",
            "",
            "\n".join(guideline_lines) or "No guidelines generated.",
            "",
            "## 10. Iteration History",
            "",
            f"Best candidate: `{payload['best_result']['candidate']['id']}`",
            "",
            *workbench_lines,
            "## 12. Recommendations" if workbench else "## 11. Recommendations",
            "",
            "Review failed cases and run another iteration if quality is below target.",
        ]
    )
    path = base / "report.md"
    path.write_text(content, encoding="utf-8")
    return path
