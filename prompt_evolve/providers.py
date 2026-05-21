"""LLM provider adapters."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from .config import AppConfig, ConfigError
from .models import LLMResponse


class ProviderError(RuntimeError):
    """Raised when provider communication fails."""


@dataclass
class OpenRouterProvider:
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-4.1"
    client: httpx.Client | None = None
    name: str = "openrouter"

    def check_configured(self) -> None:
        if not os.getenv(self.api_key_env):
            raise ConfigError(
                f"OpenRouter API key is missing. Set {self.api_key_env} in .env or the shell."
            )

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        reasoning: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.check_configured()
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
        }
        if reasoning:
            payload["reasoning"] = {"effort": reasoning}
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {os.environ[self.api_key_env]}",
            "Content-Type": "application/json",
        }
        client = self.client or httpx.Client(timeout=60)
        try:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(content=content, usage=data.get("usage") or {}, raw=data)


@dataclass
class GigaChatProvider:
    credentials_env: str = "GIGACHAT_CREDENTIALS"
    base_url: str | None = None
    default_model: str = "GigaChat-Pro"
    client: httpx.Client | None = None
    name: str = "gigachat"

    def check_configured(self) -> None:
        if not os.getenv(self.credentials_env):
            raise ConfigError(
                f"GigaChat provider is selected but credentials are missing. Set {self.credentials_env}."
            )
        if not self.base_url:
            raise ConfigError("GigaChat provider is selected but base_url is not configured.")

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        reasoning: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self.check_configured()
        payload = {"model": model or self.default_model, "messages": messages}
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        client = self.client or httpx.Client(timeout=60)
        try:
            response = client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {os.environ[self.credentials_env]}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"GigaChat request failed: {exc}") from exc
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return LLMResponse(content=content, usage=data.get("usage") or {}, raw=data)


class MockProvider:
    name = "mock"

    def check_configured(self) -> None:
        return None

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        reasoning: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        text = "\n".join(message.get("content", "") for message in messages).lower()
        if "test cases" in text or "testcases" in text:
            content = json.dumps(
                [
                    {
                        "id": "TC-001",
                        "name": "Generated happy path",
                        "type": "happy_path",
                        "priority": "high",
                        "input": "Summarize duplicated status notes.",
                        "expected_behavior": "Return concise Markdown and preserve action items.",
                        "evaluation_criteria": ["Uses Markdown", "Preserves action items"],
                    }
                ]
            )
        elif "evaluate" in text:
            content = json.dumps(
                {
                    "passed": True,
                    "score": 0.95,
                    "reason": "Mock response satisfies the criteria.",
                    "failed_criteria": [],
                    "error_type": None,
                }
            )
        elif "guideline" in text:
            content = json.dumps(
                {
                    "corrective": ["Validate required format before answering."],
                    "enhancement": ["Handle happy path and edge cases explicitly."],
                }
            )
        else:
            content = (
                "You are a precise assistant.\n"
                "Goal: solve the user's task faithfully.\n"
                "Rules: preserve facts, follow the requested format, avoid hallucinations, "
                "and self-check before responding."
            )
        return LLMResponse(content=content, usage={"prompt_tokens": 10, "completion_tokens": 10})


def provider_from_config(config: AppConfig):
    if config.provider == "mock":
        return MockProvider()
    if config.provider == "openrouter":
        return OpenRouterProvider(
            api_key_env=config.openrouter.api_key_env,
            base_url=config.openrouter.base_url or "https://openrouter.ai/api/v1",
            default_model=config.model or "openai/gpt-4.1",
        )
    if config.provider == "gigachat":
        return GigaChatProvider(
            credentials_env=config.gigachat.credentials_env,
            base_url=config.gigachat.base_url,
            default_model=config.model or "GigaChat-Pro",
        )
    raise ConfigError("Unsupported provider")
