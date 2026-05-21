"""Typer CLI entrypoints."""

from pathlib import Path
from typing import Optional

import typer

from .config import ConfigError, load_config, merge_cli_overrides, validate_runtime_config, write_default_config
from .pipeline import evaluate_command, generate_tests_command, run_evolution

app = typer.Typer(help="Prompt Evolution CLI")


def _prepare_config(
    *,
    config_path: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    target_tests: Optional[int],
    iterations: Optional[int],
    candidates: Optional[int],
    pass_k: Optional[int],
    user_tests_only: Optional[bool],
    reasoning: Optional[str],
    self_check: Optional[bool],
    out: Optional[str],
):
    config = load_config(config_path)
    config = merge_cli_overrides(
        config,
        {
            "provider": provider,
            "model": model,
            "target_tests": target_tests,
            "iterations": iterations,
            "candidates": candidates,
            "pass_k": pass_k,
            "user_tests_only": user_tests_only,
            "reasoning": reasoning,
            "self_check": self_check,
            "out": out,
        },
    )
    validate_runtime_config(config)
    return config


def _handle_error(exc: Exception) -> None:
    typer.echo(str(exc), err=True)
    raise typer.Exit(1) from exc


@app.command()
def init_config(
    out: str = typer.Option("prompt-evolve.yaml", "--out", help="Config file path."),
) -> None:
    """Create an example YAML configuration."""
    path = write_default_config(out)
    typer.echo(f"Config written to {path}")


@app.command()
def generate_tests(
    task: str = typer.Option(..., "--task", help="Task Markdown file."),
    out: str = typer.Option(..., "--out", help="Output tests.json path."),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    target_tests: Optional[int] = typer.Option(None, "--target-tests"),
    reasoning: Optional[str] = typer.Option(None, "--reasoning"),
    self_check: bool = typer.Option(True, "--self-check"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Generate test cases for a task."""
    try:
        cfg = _prepare_config(
            config_path=config,
            provider=provider,
            model=model,
            target_tests=target_tests,
            iterations=None,
            candidates=None,
            pass_k=None,
            user_tests_only=None,
            reasoning=reasoning,
            self_check=self_check,
            out=None,
        )
        tests = generate_tests_command(task, out, cfg)
    except Exception as exc:
        _handle_error(exc)
    typer.echo(f"Generated {len(tests)} test cases: {out}")


@app.command()
def evaluate(
    task: str = typer.Option(..., "--task", help="Task Markdown file."),
    prompt: str = typer.Option(..., "--prompt", help="Prompt Markdown file."),
    tests: str = typer.Option(..., "--tests", help="Tests JSON file."),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    pass_k: Optional[int] = typer.Option(None, "--pass-k"),
    reasoning: Optional[str] = typer.Option(None, "--reasoning"),
    self_check: bool = typer.Option(True, "--self-check"),
    out: Optional[str] = typer.Option(None, "--out"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Evaluate one prompt against existing tests."""
    try:
        cfg = _prepare_config(
            config_path=config,
            provider=provider,
            model=model,
            target_tests=None,
            iterations=None,
            candidates=1,
            pass_k=pass_k or 1,
            user_tests_only=True,
            reasoning=reasoning,
            self_check=self_check,
            out=out,
        )
        payload = evaluate_command(task, prompt, tests, cfg)
    except Exception as exc:
        _handle_error(exc)
    metrics = payload["metrics"]
    typer.echo("Evaluation completed.")
    typer.echo(f"Final pass@1: {metrics['pass@1']:.2f}")
    typer.echo(f"Report: {Path(cfg.output.dir) / 'report.md'}")


@app.command()
def run(
    task: str = typer.Option(..., "--task", help="Task Markdown file."),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Baseline prompt Markdown file."),
    tests: Optional[str] = typer.Option(None, "--tests", help="Tests JSON file."),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    target_tests: Optional[int] = typer.Option(None, "--target-tests"),
    iterations: Optional[int] = typer.Option(None, "--iterations"),
    candidates: Optional[int] = typer.Option(None, "--candidates"),
    pass_k: Optional[int] = typer.Option(None, "--pass-k"),
    user_tests_only: bool = typer.Option(False, "--user-tests-only"),
    reasoning: Optional[str] = typer.Option(None, "--reasoning"),
    self_check: bool = typer.Option(True, "--self-check"),
    out: Optional[str] = typer.Option(None, "--out"),
    config: Optional[str] = typer.Option(None, "--config"),
) -> None:
    """Run the full SCOPE prompt evolution pipeline."""
    try:
        cfg = _prepare_config(
            config_path=config,
            provider=provider,
            model=model,
            target_tests=target_tests,
            iterations=iterations,
            candidates=candidates,
            pass_k=pass_k,
            user_tests_only=user_tests_only,
            reasoning=reasoning,
            self_check=self_check,
            out=out,
        )
        payload = run_evolution(
            task_path=task,
            prompt_path=prompt,
            tests_path=tests,
            config=cfg,
            status=typer.echo,
        )
    except Exception as exc:
        if isinstance(exc, ConfigError):
            _handle_error(exc)
        _handle_error(exc)
    metrics = payload["metrics"]
    typer.echo("")
    typer.echo("Prompt evolution completed.")
    typer.echo(f"Final pass@1: {metrics['pass@1']:.2f}")
    typer.echo(f"Final pass@{cfg.pass_k}: {metrics['pass@k']:.2f}")
    typer.echo(f"Best prompt: {Path(cfg.output.dir) / 'final_prompt.md'}")
    typer.echo(f"Report: {Path(cfg.output.dir) / 'report.md'}")
    typer.echo(f"Test cases: {Path(cfg.output.dir) / 'tests.json'}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
