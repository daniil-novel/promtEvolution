import json

from typer.testing import CliRunner

from prompt_evolve.cli import app
from tests.unit.test_prompts_evaluator_scope_metrics import case

runner = CliRunner()


def write_inputs(tmp_path):
    task = tmp_path / "task.md"
    prompt = tmp_path / "prompt.md"
    tests = tmp_path / "tests.json"
    task.write_text("Task requirements", encoding="utf-8")
    prompt.write_text("Prompt", encoding="utf-8")
    tests.write_text(json.dumps([case().to_dict()]), encoding="utf-8")
    return task, prompt, tests


def test_init_config(tmp_path):
    result = runner.invoke(app, ["init-config", "--out", str(tmp_path / "config.yaml")])
    assert result.exit_code == 0
    assert "Config written" in result.output


def test_run_task_only(tmp_path):
    task, _, _ = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "run",
            "--task",
            str(task),
            "--provider",
            "mock",
            "--target-tests",
            "2",
            "--iterations",
            "1",
            "--candidates",
            "2",
            "--pass-k",
            "2",
            "--out",
            str(tmp_path / "run1"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Prompt evolution completed" in result.output
    assert (tmp_path / "run1" / "report.json").exists()


def test_run_from_python_config(tmp_path):
    config = tmp_path / "project.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'task': {'text': 'Task requirements'},\n"
        "  'prompt': {'text': 'Prompt'},\n"
        "  'tests': {'cases': [{\n"
        "    'id': 'TC-001', 'name': 'Case', 'type': 'happy_path', 'priority': 'high',\n"
        "    'input': 'Use Markdown', 'expected_behavior': 'Markdown output',\n"
        "    'evaluation_criteria': ['Uses Markdown', 'Preserves facts']\n"
        "  }]},\n"
        f"  'settings': {{'provider': 'mock', 'target_tests': 1, 'iterations': 1, 'candidates': 1, 'pass_k': 1, 'output': {{'dir': r'{tmp_path / 'py-run'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["run", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "py-run" / "final_prompt.md").exists()


def test_run_from_python_config_uses_default_task_when_only_prompt_is_supplied(tmp_path):
    config = tmp_path / "prompt_only_project.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'prompt': {'text': 'Отвечай только JSON.'},\n"
        f"  'settings': {{'provider': 'mock', 'target_tests': 1, 'iterations': 1, 'candidates': 1, 'pass_k': 1, 'output': {{'dir': r'{tmp_path / 'prompt-only-run'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["run", "--config", str(config)])
    assert result.exit_code == 0, result.output
    report = json.loads((tmp_path / "prompt-only-run" / "report.json").read_text(encoding="utf-8"))
    assert "production-ready" in report["task"]


def test_run_with_prompt_and_tests(tmp_path):
    task, prompt, tests = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "run",
            "--task",
            str(task),
            "--prompt",
            str(prompt),
            "--tests",
            str(tests),
            "--provider",
            "mock",
            "--target-tests",
            "1",
            "--iterations",
            "1",
            "--candidates",
            "1",
            "--pass-k",
            "1",
            "--out",
            str(tmp_path / "run2"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "run2" / "final_prompt.md").exists()


def test_generate_tests_command(tmp_path):
    task, _, _ = write_inputs(tmp_path)
    out = tmp_path / "generated.json"
    result = runner.invoke(
        app,
        [
            "generate-tests",
            "--task",
            str(task),
            "--target-tests",
            "4",
            "--provider",
            "mock",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert len(json.loads(out.read_text(encoding="utf-8"))) == 4


def test_generate_tests_from_python_config(tmp_path):
    config = tmp_path / "project.py"
    out = tmp_path / "generated.json"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'task': {'text': 'Task requirements'},\n"
        "  'settings': {'provider': 'mock', 'target_tests': 3, 'output': {'dir': 'runs/x'}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["generate-tests", "--config", str(config), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert len(json.loads(out.read_text(encoding="utf-8"))) == 3


def test_evaluate_command(tmp_path):
    task, prompt, tests = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "evaluate",
            "--task",
            str(task),
            "--prompt",
            str(prompt),
            "--tests",
            str(tests),
            "--provider",
            "mock",
            "--out",
            str(tmp_path / "eval"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Evaluation completed" in result.output


def test_workbench_command(tmp_path):
    task, prompt, tests = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "workbench",
            "--task",
            str(task),
            "--prompt",
            str(prompt),
            "--tests",
            str(tests),
            "--provider",
            "mock",
            "--target-tests",
            "1",
            "--population-size",
            "2",
            "--generations",
            "1",
            "--pass-k",
            "1",
            "--out",
            str(tmp_path / "workbench"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Prompt workbench completed" in result.output
    assert (tmp_path / "workbench" / "task_spec.yaml").exists()
    assert (tmp_path / "workbench" / "tool_policy.yaml").exists()
    assert (tmp_path / "workbench" / "replay_buffer.json").exists()
    assert (tmp_path / "workbench" / "promptfoo.yaml").exists()
    assert "Estimated LLM calls" in (tmp_path / "workbench" / "logs" / "run.log").read_text(encoding="utf-8")


def test_workbench_from_python_config_without_prompt_or_tests(tmp_path):
    config = tmp_path / "workbench_project.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'task': {'text': 'Отвечай только JSON'},\n"
        f"  'settings': {{'provider': 'mock', 'target_tests': 1, 'candidates': 2, 'pass_k': 1, 'output': {{'dir': r'{tmp_path / 'wb-config'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "workbench",
            "--config",
            str(config),
            "--population-size",
            "2",
            "--generations",
            "1",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "wb-config" / "final_prompt.md").exists()


def test_workbench_llm_eval_flag(tmp_path):
    task, prompt, tests = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "workbench",
            "--task",
            str(task),
            "--prompt",
            str(prompt),
            "--tests",
            str(tests),
            "--provider",
            "mock",
            "--target-tests",
            "1",
            "--population-size",
            "2",
            "--generations",
            "1",
            "--pass-k",
            "1",
            "--llm-eval",
            "--out",
            str(tmp_path / "workbench-llm"),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads((tmp_path / "workbench-llm" / "report.json").read_text(encoding="utf-8"))
    assert payload["workbench"]["fast_eval"] is False


def test_workbench_from_python_config_uses_default_task_when_prompt_only(tmp_path):
    config = tmp_path / "workbench_prompt_only.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'prompt': {'text': 'Отвечай только JSON.'},\n"
        f"  'settings': {{'provider': 'mock', 'target_tests': 1, 'candidates': 2, 'pass_k': 1, 'output': {{'dir': r'{tmp_path / 'wb-prompt-only'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        ["workbench", "--config", str(config), "--population-size", "2", "--generations", "1"],
    )
    assert result.exit_code == 0, result.output
    spec_text = (tmp_path / "wb-prompt-only" / "task_spec.yaml").read_text(encoding="utf-8")
    assert "production-ready" in spec_text


def test_workbench_validation_error():
    result = runner.invoke(app, ["workbench", "--provider", "mock", "--population-size", "1"])
    assert result.exit_code == 1
    assert "population-size must be at least 2" in result.output


def test_evaluate_from_python_config(tmp_path):
    config = tmp_path / "project.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'task': {'text': 'Task requirements'},\n"
        "  'prompt': {'text': 'Prompt'},\n"
        "  'tests': {'cases': [{\n"
        "    'id': 'TC-001', 'name': 'Case', 'type': 'happy_path', 'priority': 'high',\n"
        "    'input': 'Use Markdown', 'expected_behavior': 'Markdown output',\n"
        "    'evaluation_criteria': ['Uses Markdown', 'Preserves facts']\n"
        "  }]},\n"
        f"  'settings': {{'provider': 'mock', 'output': {{'dir': r'{tmp_path / 'py-eval'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["evaluate", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "py-eval" / "report.md").exists()


def test_evaluate_from_python_config_uses_default_task_when_only_prompt_is_supplied(tmp_path):
    config = tmp_path / "prompt_only_eval.py"
    config.write_text(
        "PROMPT_EVOLVE = {\n"
        "  'prompt': {'text': 'Отвечай только JSON.'},\n"
        "  'tests': {'cases': [{\n"
        "    'id': 'TC-001', 'name': 'Case', 'type': 'happy_path', 'priority': 'high',\n"
        "    'input': 'Use JSON', 'expected_behavior': 'JSON output',\n"
        "    'evaluation_criteria': ['Uses JSON', 'Preserves facts']\n"
        "  }]},\n"
        f"  'settings': {{'provider': 'mock', 'output': {{'dir': r'{tmp_path / 'prompt-only-eval'}'}}}}\n"
        "}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["evaluate", "--config", str(config)])
    assert result.exit_code == 0, result.output
    report = json.loads((tmp_path / "prompt-only-eval" / "report.json").read_text(encoding="utf-8"))
    assert "production-ready" in report["task"]


def test_cli_validation_error(tmp_path):
    task, _, _ = write_inputs(tmp_path)
    result = runner.invoke(
        app,
        [
            "run",
            "--task",
            str(task),
            "--provider",
            "mock",
            "--candidates",
            "1",
            "--pass-k",
            "2",
        ],
    )
    assert result.exit_code == 1
    assert "pass-k cannot be greater than candidates" in result.output


def test_missing_openrouter_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    task, _, _ = write_inputs(tmp_path)
    result = runner.invoke(app, ["run", "--task", str(task), "--target-tests", "1", "--iterations", "1"])
    assert result.exit_code == 1
    assert "OPENROUTER_API_KEY" in result.output
