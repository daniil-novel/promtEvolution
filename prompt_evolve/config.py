"""Configuration loading and validation."""

from __future__ import annotations

import os
import importlib.util
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised for invalid CLI or config input."""


@dataclass(frozen=True)
class OutputConfig:
    dir: str = "runs/latest"
    save_markdown_report: bool = True
    save_json_report: bool = True
    save_final_prompt: bool = True


@dataclass(frozen=True)
class ProviderConfig:
    api_key_env: str = "OPENROUTER_API_KEY"
    credentials_env: str = "GIGACHAT_CREDENTIALS"
    base_url: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class AppConfig:
    provider: str = "openrouter"
    model: str | None = None
    target_tests: int = 40
    iterations: int = 3
    candidates: int = 4
    pass_k: int = 4
    reasoning: str = "max"
    self_check: bool = True
    user_tests_only: bool = False
    output: OutputConfig = field(default_factory=OutputConfig)
    openrouter: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(
            api_key_env="OPENROUTER_API_KEY",
            base_url="https://openrouter.ai/api/v1",
            enabled=True,
        )
    )
    gigachat: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(
            credentials_env="GIGACHAT_CREDENTIALS",
            base_url=None,
            enabled=False,
        )
    )


@dataclass(frozen=True)
class ScenarioInputs:
    task_text: str | None = None
    task_file: str | None = None
    prompt_text: str | None = None
    prompt_file: str | None = None
    tests_data: list[dict[str, Any]] | None = None
    tests_file: str | None = None


@dataclass(frozen=True)
class ScenarioConfig:
    app: AppConfig
    inputs: ScenarioInputs = field(default_factory=ScenarioInputs)


def default_config_dict() -> dict[str, Any]:
    return {
        "provider": "openrouter",
        "model": "openai/gpt-4.1",
        "target_tests": 40,
        "iterations": 3,
        "candidates": 4,
        "pass_k": 4,
        "reasoning": "max",
        "self_check": True,
        "user_tests_only": False,
        "output": {
            "dir": "runs/latest",
            "save_markdown_report": True,
            "save_json_report": True,
            "save_final_prompt": True,
        },
        "openrouter": {
            "api_key_env": "OPENROUTER_API_KEY",
            "base_url": "https://openrouter.ai/api/v1",
        },
        "gigachat": {
            "enabled": False,
            "credentials_env": "GIGACHAT_CREDENTIALS",
            "base_url": None,
        },
    }


def load_dotenv(path: str | Path = ".env", *, override: bool = True) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def read_text_file(path: str | Path, *, label: str) -> str:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise ConfigError(f"{label} file is missing or empty")
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ConfigError(f"{label} file is missing or empty")
    return content


def _provider_config(data: dict[str, Any], defaults: ProviderConfig) -> ProviderConfig:
    values = {
        "api_key_env": data.get("api_key_env", defaults.api_key_env),
        "credentials_env": data.get("credentials_env", defaults.credentials_env),
        "base_url": data.get("base_url", defaults.base_url),
        "enabled": data.get("enabled", defaults.enabled),
    }
    return ProviderConfig(**values)


def config_from_dict(data: dict[str, Any]) -> AppConfig:
    defaults = AppConfig()
    output_data = data.get("output") or {}
    output = OutputConfig(
        dir=output_data.get("dir", defaults.output.dir),
        save_markdown_report=output_data.get(
            "save_markdown_report", defaults.output.save_markdown_report
        ),
        save_json_report=output_data.get("save_json_report", defaults.output.save_json_report),
        save_final_prompt=output_data.get("save_final_prompt", defaults.output.save_final_prompt),
    )
    return AppConfig(
        provider=data.get("provider", defaults.provider),
        model=data.get("model", defaults.model),
        target_tests=int(data.get("target_tests", defaults.target_tests)),
        iterations=int(data.get("iterations", defaults.iterations)),
        candidates=int(data.get("candidates", defaults.candidates)),
        pass_k=int(data.get("pass_k", defaults.pass_k)),
        reasoning=data.get("reasoning", defaults.reasoning),
        self_check=bool(data.get("self_check", defaults.self_check)),
        user_tests_only=bool(data.get("user_tests_only", defaults.user_tests_only)),
        output=output,
        openrouter=_provider_config(data.get("openrouter") or {}, defaults.openrouter),
        gigachat=_provider_config(data.get("gigachat") or {}, defaults.gigachat),
    )


def _load_python_mapping(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("prompt_evolve_user_config", path)
    if spec is None or spec.loader is None:
        raise ConfigError(f"Cannot load Python config: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("PROMPT_EVOLVE", "CONFIG", "config"):
        value = getattr(module, name, None)
        if value is not None:
            if not isinstance(value, dict):
                raise ConfigError(f"Python config variable {name} must be a dict")
            return value
    raise ConfigError("Python config must define PROMPT_EVOLVE, CONFIG, or config dict")


def _read_config_mapping(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    if config_path.suffix.lower() == ".py":
        return _load_python_mapping(config_path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a mapping")
    return data


def _text_or_file(value: Any, *, label: str) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, str):
        if "\n" in value or len(value) > 260:
            return value, None
        return None, value
    if not isinstance(value, dict):
        raise ConfigError(f"{label} config must be a string or mapping")
    text = value.get("text")
    file_path = value.get("file") or value.get("path")
    if text is not None and file_path is not None:
        raise ConfigError(f"{label} config must use either text or file, not both")
    return text, file_path


def scenario_from_dict(data: dict[str, Any]) -> ScenarioConfig:
    settings_data = data.get("settings")
    if settings_data is None:
        settings_data = {
            key: value
            for key, value in data.items()
            if key not in {"task", "prompt", "tests"}
        }
    if not isinstance(settings_data, dict):
        raise ConfigError("settings config must be a mapping")
    task_text, task_file = _text_or_file(data.get("task"), label="task")
    prompt_text, prompt_file = _text_or_file(data.get("prompt"), label="prompt")
    tests_value = data.get("tests")
    tests_data = None
    tests_file = None
    if isinstance(tests_value, list):
        tests_data = tests_value
    elif isinstance(tests_value, str):
        tests_file = tests_value
    elif isinstance(tests_value, dict):
        tests_data = tests_value.get("cases")
        tests_file = tests_value.get("file") or tests_value.get("path")
        if tests_data is not None and tests_file is not None:
            raise ConfigError("tests config must use either cases or file, not both")
    elif tests_value is not None:
        raise ConfigError("tests config must be a list, string, or mapping")
    return ScenarioConfig(
        app=config_from_dict(settings_data),
        inputs=ScenarioInputs(
            task_text=task_text,
            task_file=task_file,
            prompt_text=prompt_text,
            prompt_file=prompt_file,
            tests_data=tests_data,
            tests_file=tests_file,
        ),
    )


def load_config(path: str | Path | None = None) -> AppConfig:
    load_dotenv()
    if path is None:
        return AppConfig()
    data = _read_config_mapping(path)
    return config_from_dict(data)


def load_scenario_config(path: str | Path | None = None) -> ScenarioConfig:
    load_dotenv()
    if path is None:
        return ScenarioConfig(app=AppConfig())
    return scenario_from_dict(_read_config_mapping(path))


def merge_cli_overrides(config: AppConfig, overrides: dict[str, Any]) -> AppConfig:
    clean = {key: value for key, value in overrides.items() if value is not None}
    output_dir = clean.pop("out", None)
    output = config.output
    if output_dir is not None:
        output = replace(config.output, dir=str(output_dir))
    if output is not config.output:
        clean["output"] = output
    return replace(config, **clean)


def validate_runtime_config(config: AppConfig) -> None:
    if config.provider not in {"openrouter", "gigachat", "mock"}:
        raise ConfigError("Unsupported provider")
    if not 1 <= config.target_tests <= 500:
        raise ConfigError("target-tests must be between 1 and 500")
    if not 1 <= config.iterations <= 50:
        raise ConfigError("iterations must be between 1 and 50")
    if not 1 <= config.candidates <= 20:
        raise ConfigError("candidates must be between 1 and 20")
    if config.pass_k > config.candidates:
        raise ConfigError("pass-k cannot be greater than candidates")


def write_default_config(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_text(yaml.safe_dump(default_config_dict(), sort_keys=False), encoding="utf-8")
    return output_path
