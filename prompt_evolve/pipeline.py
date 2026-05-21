"""High-level orchestration for CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import AppConfig, read_text_file
from .evaluator import run_candidate
from .metrics import build_metrics, pass_at_1
from .models import NoopSystemMetricsCollector, PromptRunResult
from .prompts import generate_prompt_candidates, select_best_prompt
from .providers import provider_from_config
from .report import (
    ensure_run_dirs,
    report_payload,
    write_candidates,
    write_evaluations,
    write_final_prompt,
    write_json_report,
    write_markdown_report,
    write_run_log,
)
from .scope import generate_guidelines, self_check_guidelines, update_prompt_with_guidelines
from .testcases import ensure_target_testcases, load_testcases, save_testcases, self_check_testcases


def generate_tests_command(task_path: str, output_path: str, config: AppConfig) -> list[dict[str, Any]]:
    task = read_text_file(task_path, label="Task")
    provider = provider_from_config(config)
    provider.check_configured()
    testcases = ensure_target_testcases(
        task,
        [],
        provider,
        target_tests=config.target_tests,
        model=config.model,
        reasoning=config.reasoning,
    )
    save_testcases(testcases, output_path)
    return [case.to_dict() for case in testcases]


def evaluate_command(task_path: str, prompt_path: str, tests_path: str, config: AppConfig) -> dict[str, Any]:
    task = read_text_file(task_path, label="Task")
    prompt = read_text_file(prompt_path, label="Prompt")
    testcases = load_testcases(tests_path)
    provider = provider_from_config(config)
    provider.check_configured()
    candidate = generate_prompt_candidates(
        task,
        prompt,
        provider,
        count=1,
        iteration=1,
        model=config.model,
        reasoning=config.reasoning,
    )[0]
    result = run_candidate(
        candidate,
        testcases,
        provider,
        model=config.model,
        reasoning=config.reasoning,
        self_check=config.self_check,
    )
    metrics = build_metrics(result, [result], testcases, k=1, baseline_pass=pass_at_1(result.evaluations))
    out_dir = ensure_run_dirs(config.output.dir)
    payload = report_payload(
        task=task,
        provider=config.provider,
        model=config.model,
        baseline_prompt=prompt,
        final_prompt=candidate.content,
        metrics=metrics,
        testcases=testcases,
        best_result=result,
        guidelines=[],
    )
    save_testcases(testcases, out_dir / "tests.json")
    write_final_prompt(out_dir, candidate.content)
    write_json_report(out_dir, payload)
    write_markdown_report(out_dir, payload)
    write_run_log(out_dir, ["evaluate completed"])
    return payload


def run_evolution(
    *,
    task_path: str,
    config: AppConfig,
    prompt_path: str | None = None,
    tests_path: str | None = None,
    status: callable | None = None,
) -> dict[str, Any]:
    logs: list[str] = []

    def emit(message: str) -> None:
        logs.append(message)
        if status:
            status(message)

    emit("[1/9] Loading input files...")
    task = read_text_file(task_path, label="Task")
    baseline_prompt = read_text_file(prompt_path, label="Prompt") if prompt_path else None
    user_tests = load_testcases(tests_path) if tests_path else []

    emit("[2/9] Checking provider configuration...")
    provider = provider_from_config(config)
    provider.check_configured()

    emit("[3/9] Generating test cases...")
    testcases = ensure_target_testcases(
        task,
        user_tests,
        provider,
        target_tests=config.target_tests,
        user_tests_only=config.user_tests_only,
        model=config.model,
        reasoning=config.reasoning,
    )

    emit("[4/9] Running self-check for test cases...")
    warnings = self_check_testcases(testcases) if config.self_check else []
    logs.extend(warnings)

    current_prompt = baseline_prompt
    all_results: list[PromptRunResult] = []
    all_guidelines: list[dict[str, list[str]]] = []
    baseline_pass: float | None = None
    best_result: PromptRunResult | None = None

    for iteration in range(1, config.iterations + 1):
        emit("[5/9] Generating prompt candidates...")
        candidates = generate_prompt_candidates(
            task,
            current_prompt,
            provider,
            count=config.candidates,
            iteration=iteration,
            model=config.model,
            reasoning=config.reasoning,
        )
        emit("[6/9] Evaluating candidates...")
        iteration_results = [
            run_candidate(
                candidate,
                testcases,
                provider,
                model=config.model,
                reasoning=config.reasoning,
                self_check=config.self_check,
            )
            for candidate in candidates
        ]
        if baseline_pass is None and iteration_results:
            baseline_pass = pass_at_1(iteration_results[0].evaluations)
        all_results.extend(iteration_results)
        best_result = select_best_prompt(iteration_results)

        emit("[7/9] Calculating metrics...")
        emit("[8/9] Applying SCOPE improvements...")
        guidelines = generate_guidelines(
            best_result,
            provider,
            model=config.model,
            reasoning=config.reasoning,
        )
        if config.self_check:
            guidelines = self_check_guidelines(guidelines)
        all_guidelines.append(guidelines)
        current_prompt = update_prompt_with_guidelines(best_result.candidate.content, guidelines)

        out_dir = ensure_run_dirs(config.output.dir)
        write_candidates(out_dir, iteration_results)
        write_evaluations(out_dir, iteration, iteration_results)

    if best_result is None:
        raise RuntimeError("No prompt candidates were evaluated")
    final_prompt = current_prompt or best_result.candidate.content
    metrics = build_metrics(best_result, all_results, testcases, k=config.pass_k, baseline_pass=baseline_pass)
    system_metrics = NoopSystemMetricsCollector().collect()

    emit("[9/9] Saving final report...")
    out_dir = ensure_run_dirs(config.output.dir)
    save_testcases(testcases, Path(out_dir) / "tests.json")
    write_final_prompt(out_dir, final_prompt)
    payload = report_payload(
        task=task,
        provider=config.provider,
        model=config.model,
        baseline_prompt=baseline_prompt,
        final_prompt=final_prompt,
        metrics=metrics,
        testcases=testcases,
        best_result=best_result,
        guidelines=all_guidelines,
        system_metrics=system_metrics,
    )
    write_json_report(out_dir, payload)
    write_markdown_report(out_dir, payload)
    write_run_log(out_dir, logs)
    return payload
