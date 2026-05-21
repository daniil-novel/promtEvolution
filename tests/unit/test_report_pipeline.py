import json

from prompt_evolve.config import AppConfig
from prompt_evolve.pipeline import evaluate_command, generate_tests_command, run_evolution
from prompt_evolve.report import (
    ensure_run_dirs,
    report_payload,
    write_candidates,
    write_evaluations,
    write_final_prompt,
    write_json_report,
    write_markdown_report,
    write_run_log,
)
from tests.unit.test_prompts_evaluator_scope_metrics import case, result
from prompt_evolve.metrics import build_metrics


def test_report_writers(tmp_path):
    out = ensure_run_dirs(tmp_path / "run")
    run_result = result("best", True)
    metrics = build_metrics(run_result, [run_result], [case()], k=1)
    payload = report_payload(
        task="Task",
        provider="mock",
        model=None,
        baseline_prompt=None,
        final_prompt="Prompt",
        metrics=metrics,
        testcases=[case()],
        best_result=run_result,
        guidelines=[{"corrective": ["Fix"], "enhancement": []}],
    )
    assert write_candidates(out, [run_result])[0].exists()
    assert write_evaluations(out, 1, [run_result]).exists()
    assert write_final_prompt(out, "Prompt").exists()
    assert write_json_report(out, payload).exists()
    assert write_markdown_report(out, payload).exists()
    assert write_run_log(out, ["done"]).exists()


def test_pipeline_commands(tmp_path):
    task = tmp_path / "task.md"
    prompt = tmp_path / "prompt.md"
    tests = tmp_path / "tests.json"
    task.write_text("Task", encoding="utf-8")
    prompt.write_text("Prompt", encoding="utf-8")
    tests.write_text(json.dumps([case().to_dict()]), encoding="utf-8")
    config = AppConfig(provider="mock", target_tests=2, iterations=1, candidates=2, pass_k=2)
    config = type(config)(**{**config.__dict__, "output": type(config.output)(dir=str(tmp_path / "run"))})

    generated = generate_tests_command(str(task), str(tmp_path / "generated.json"), config)
    assert len(generated) == 2
    evaluated = evaluate_command(str(task), str(prompt), str(tests), config)
    assert evaluated["metrics"]["pass@1"] >= 0
    statuses = []
    payload = run_evolution(
        task_path=str(task),
        prompt_path=str(prompt),
        tests_path=str(tests),
        config=config,
        status=statuses.append,
    )
    assert payload["final_prompt"]
    assert any("[9/9]" in item for item in statuses)
