"""Advanced Prompt Evolution Workbench pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .clarify import build_task_spec
from .config import AppConfig, ConfigError, read_text_file
from .inspo import run_inspo_evolution
from .mcp_tools import infer_tool_policy, load_mcp_config
from .metrics import build_metrics, pass_at_1
from .models import NoopSystemMetricsCollector, RewardWeights
from .providers import provider_from_config
from .report import (
    ensure_run_dirs,
    report_payload,
    write_candidates,
    write_final_prompt,
    write_json_report,
    write_markdown_report,
    write_run_log,
)
from .scope import update_prompt_with_guidelines
from .testcases import ensure_target_testcases, load_testcases, save_testcases


def _resolve_text(cli_path: str | None, config_path: str | None, text: str | None, label: str) -> str:
    path = cli_path or config_path
    if path:
        return read_text_file(path, label=label)
    if text and text.strip():
        return text.strip()
    raise ConfigError(f"{label} file is missing or empty")


def _resolve_tests(cli_path: str | None, config_path: str | None, data: list[dict[str, Any]] | None):
    path = cli_path or config_path
    if path:
        return load_testcases(path)
    if data:
        from .testcases import validate_testcases

        return validate_testcases(data)
    return []


def _write_yaml(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _write_promptfoo_config(out_dir: Path, tests: list, provider: str, model: str | None) -> Path:
    prompts = ["final_prompt.md"]
    cases = [
        {
            "vars": {"input": case.input},
            "assert": [
                {"type": "contains", "value": criterion}
                for criterion in case.evaluation_criteria[:2]
            ],
        }
        for case in tests
    ]
    return _write_yaml(
        out_dir / "promptfoo.yaml",
        {
            "description": "Prompt Evolution Workbench regression config",
            "providers": [f"{provider}:{model or 'default'}"],
            "prompts": prompts,
            "tests": cases,
        },
    )


def _write_failure_analysis(out_dir: Path, replay_records: list) -> Path:
    worst = replay_records[:5]
    lines = ["# Failure Analysis", ""]
    if not worst:
        lines.append("Ошибок и низких reward-траекторий не найдено.")
    for record in worst:
        failed = [item for item in record.evaluations if not item.get("passed")]
        lines.extend(
            [
                f"## {record.candidate_id}",
                "",
                f"Reward: `{record.reward:.3f}`",
                "",
                "Проваленные проверки:",
                "",
                "\n".join(f"- {item.get('test_case_id')}: {item.get('reason')}" for item in failed)
                or "- Нет явных провалов, запись попала в буфер как низкая по reward.",
                "",
            ]
        )
    path = out_dir / "failure_analysis.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run_workbench(
    *,
    task_path: str | None,
    config: AppConfig,
    task_text: str | None = None,
    config_task_path: str | None = None,
    prompt_path: str | None = None,
    prompt_text: str | None = None,
    config_prompt_path: str | None = None,
    tests_path: str | None = None,
    tests_data: list[dict[str, Any]] | None = None,
    config_tests_path: str | None = None,
    population_size: int | None = None,
    generations: int | None = None,
    elite_size: int = 2,
    replay_buffer_size: int = 100,
    clarify_questions: int = 8,
    mcp_config_path: str | None = None,
    status: callable | None = None,
) -> dict[str, Any]:
    logs: list[str] = []

    def emit(message: str) -> None:
        logs.append(message)
        if status:
            status(message)

    emit("[1/10] Loading workbench inputs...")
    task = _resolve_text(task_path, config_task_path, task_text, "Task")
    baseline_prompt = None
    if prompt_path or prompt_text or config_prompt_path:
        baseline_prompt = _resolve_text(prompt_path, config_prompt_path, prompt_text, "Prompt")
    user_tests = _resolve_tests(tests_path, config_tests_path, tests_data)

    emit("[2/10] Checking provider configuration...")
    provider = provider_from_config(config)
    provider.check_configured()

    emit("[3/10] Clarifying task into task_spec.yaml...")
    task_spec = build_task_spec(
        task,
        baseline_prompt,
        provider,
        max_questions=clarify_questions,
        model=config.model,
        reasoning=config.reasoning,
    )

    emit("[4/10] Building MCP/tool policy...")
    mcp_config = load_mcp_config(mcp_config_path)
    tool_policy = infer_tool_policy(task_spec, mcp_config=mcp_config)

    emit("[5/10] Generating production-grade eval tests...")
    testcases = ensure_target_testcases(
        task,
        user_tests,
        provider,
        target_tests=config.target_tests,
        user_tests_only=config.user_tests_only,
        model=config.model,
        reasoning=config.reasoning,
    )

    emit("[6/10] Running INSPO-like population evolution...")
    pop_size = population_size or max(config.candidates, 4)
    gens = generations or config.iterations
    evolution = run_inspo_evolution(
        task=task,
        baseline_prompt=baseline_prompt,
        testcases=testcases,
        provider=provider,
        population_size=pop_size,
        generations=gens,
        elite_size=elite_size,
        replay_buffer_size=replay_buffer_size,
        model=config.model,
        reasoning=config.reasoning,
        self_check=config.self_check,
    )

    emit("[7/10] Selecting final instruction and calculating reward metrics...")
    final_prompt = update_prompt_with_guidelines(evolution.best.candidate.content, evolution.guidelines[-1])
    baseline_pass = pass_at_1(evolution.all_results[0].evaluations) if evolution.all_results else 0.0
    metrics = build_metrics(
        evolution.best,
        evolution.all_results,
        testcases,
        k=min(config.pass_k, len(evolution.all_results) or 1),
        baseline_pass=baseline_pass,
    )

    emit("[8/10] Saving prompt population and replay buffer...")
    out_dir = ensure_run_dirs(config.output.dir)
    (out_dir / "prompt_population").mkdir(parents=True, exist_ok=True)
    write_candidates(out_dir / "prompt_population" / "all_results", evolution.all_results)
    evolution.replay_buffer.save(out_dir / "replay_buffer.json")

    emit("[9/10] Writing workbench artifacts...")
    save_testcases(testcases, out_dir / "tests.json")
    write_final_prompt(out_dir, final_prompt)
    _write_yaml(out_dir / "task_spec.yaml", task_spec.to_dict())
    _write_yaml(out_dir / "tool_policy.yaml", tool_policy.to_dict())
    _write_yaml(out_dir / "reward_config.yaml", {"weights": RewardWeights().to_dict()})
    _write_promptfoo_config(out_dir, testcases, config.provider, config.model)
    _write_failure_analysis(out_dir, evolution.replay_buffer.worst())
    (out_dir / "population.json").write_text(
        json.dumps([item.to_dict() for item in evolution.population], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    emit("[10/10] Saving final workbench report...")
    payload = report_payload(
        task=task,
        provider=config.provider,
        model=config.model,
        baseline_prompt=baseline_prompt,
        final_prompt=final_prompt,
        metrics=metrics,
        testcases=testcases,
        best_result=evolution.best,
        guidelines=evolution.guidelines,
        system_metrics=NoopSystemMetricsCollector().collect(),
    )
    payload["workbench"] = {
        "strategy": "inspo_hybrid",
        "population_size": pop_size,
        "generations": gens,
        "elite_size": elite_size,
        "task_spec": task_spec.to_dict(),
        "tool_policy": tool_policy.to_dict(),
        "replay_buffer_size": replay_buffer_size,
        "artifacts": [
            "task_spec.yaml",
            "tool_policy.yaml",
            "reward_config.yaml",
            "promptfoo.yaml",
            "replay_buffer.json",
            "population.json",
            "failure_analysis.md",
        ],
    }
    write_json_report(out_dir, payload)
    write_markdown_report(out_dir, payload)
    write_run_log(out_dir, logs)
    return payload
