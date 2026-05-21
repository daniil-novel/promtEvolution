from pathlib import Path

import pytest

from prompt_evolve.config import (
    AppConfig,
    ConfigError,
    load_config,
    load_dotenv,
    merge_cli_overrides,
    read_text_file,
    validate_runtime_config,
    write_default_config,
)


def test_load_dotenv_sets_missing_values(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=secret\n", encoding="utf-8")
    load_dotenv(env)
    assert "OPENROUTER_API_KEY" in __import__("os").environ


def test_load_config_from_yaml(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("provider: mock\ntarget_tests: 2\noutput:\n  dir: out\n", encoding="utf-8")
    config = load_config(path)
    assert config.provider == "mock"
    assert config.target_tests == 2
    assert config.output.dir == "out"


def test_merge_cli_overrides_has_priority():
    config = merge_cli_overrides(AppConfig(provider="openrouter"), {"provider": "mock", "out": "runs/x"})
    assert config.provider == "mock"
    assert config.output.dir == "runs/x"


@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"provider": "bad"}, "Unsupported provider"),
        ({"target_tests": 0}, "target-tests must be between 1 and 500"),
        ({"iterations": 0}, "iterations must be between 1 and 50"),
        ({"candidates": 0}, "candidates must be between 1 and 20"),
        ({"candidates": 1, "pass_k": 2}, "pass-k cannot be greater than candidates"),
    ],
)
def test_validate_runtime_config_errors(kwargs, message):
    with pytest.raises(ConfigError, match=message):
        validate_runtime_config(AppConfig(**kwargs))


def test_read_text_file_rejects_empty(tmp_path):
    empty = tmp_path / "task.md"
    empty.write_text("  ", encoding="utf-8")
    with pytest.raises(ConfigError, match="Task file is missing or empty"):
        read_text_file(empty, label="Task")


def test_write_default_config(tmp_path):
    path = write_default_config(tmp_path / "prompt-evolve.yaml")
    assert Path(path).read_text(encoding="utf-8").startswith("provider:")
