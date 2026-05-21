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
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    task, _, _ = write_inputs(tmp_path)
    result = runner.invoke(app, ["run", "--task", str(task), "--target-tests", "1", "--iterations", "1"])
    assert result.exit_code == 1
    assert "OPENROUTER_API_KEY" in result.output
