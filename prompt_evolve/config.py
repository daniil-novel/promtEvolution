"""Configuration loading and validation."""

from __future__ import annotations

import os
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


def load_dotenv(path: str | Path = ".env") -> None:
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
        if key and key not in os.environ:
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


def load_config(path: str | Path | None = None) -> AppConfig:
    load_dotenv()
    if path is None:
        return AppConfig()
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML mapping")
    return config_from_dict(data)


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
