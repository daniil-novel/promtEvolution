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


OPENROUTER_REASONING_ALIASES = {
    "max": "xhigh",
    "maximum": "xhigh",
}

OPENROUTER_REASONING_EFFORTS = {"xhigh", "high", "medium", "low", "minimal", "none"}


def _is_missing_secret(value: str | None) -> bool:
    if value is None:
        return True
    normalized = value.strip()
    if not normalized:
        return True
    lowered = normalized.lower()
    return lowered.startswith("paste_") or lowered.startswith("your_")


def _openrouter_reasoning(reasoning: str | None) -> dict[str, str] | None:
    if not reasoning:
        return None
    effort = OPENROUTER_REASONING_ALIASES.get(reasoning.strip().lower(), reasoning.strip().lower())
    if effort not in OPENROUTER_REASONING_EFFORTS:
        raise ConfigError(
            "OpenRouter reasoning must be one of: xhigh, high, medium, low, minimal, none."
        )
    if effort == "none":
        return None
    return {"effort": effort}


def _safe_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:500] if text else response.reason_phrase
    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or error.get("status") or error
        return str(message)[:500]
    return json.dumps(data, ensure_ascii=False)[:500]


@dataclass
class OpenRouterProvider:
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-4.1"
    client: httpx.Client | None = None
    name: str = "openrouter"

    def check_configured(self) -> None:
        if _is_missing_secret(os.getenv(self.api_key_env)):
            raise ConfigError(
                f"OpenRouter API key is missing. Set {self.api_key_env} in .env or the shell."
            )

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
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
            if response.status_code >= 400:
                detail = _safe_error_message(response)
                raise ProviderError(
                    f"OpenRouter request failed with HTTP {response.status_code}: {detail}"
                )
            return response.json()
        except ProviderError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc

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
        reasoning_payload = _openrouter_reasoning(reasoning)
        if reasoning_payload:
            payload["reasoning"] = reasoning_payload
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        try:
            data = self._post_chat_completion(payload)
        except ProviderError:
            if response_format != "json" or "response_format" not in payload:
                raise
            fallback_payload = dict(payload)
            fallback_payload.pop("response_format", None)
            data = self._post_chat_completion(fallback_payload)
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
        if _is_missing_secret(os.getenv(self.credentials_env)):
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
        if "тесткей" in text or "test cases" in text or "testcases" in text:
            content = json.dumps(
                [
                    {
                        "id": "TC-001",
                        "name": "Явно завершённый ответ агента",
                        "type": "happy_path",
                        "priority": "high",
                        "input": "Агент сообщил: задача выполнена, тесты пройдены, отчёт сохранён, открытых вопросов нет.",
                        "expected_behavior": "Вернуть JSON с decision=continue_to_final.",
                        "evaluation_criteria": [
                            "Ответ является валидным JSON-объектом",
                            "decision равен continue_to_final",
                            "Нет текста вне JSON",
                        ],
                    }
                ]
            )
        elif "evaluate" in text or "оцени" in text:
            content = json.dumps(
                {
                    "passed": True,
                    "score": 0.95,
                    "reason": "Mock-ответ соответствует критериям.",
                    "failed_criteria": [],
                    "error_type": None,
                }
            )
        elif "guideline" in text or "scope" in text:
            content = json.dumps(
                {
                    "corrective": ["Перед ответом проверяй точный JSON-формат и допустимые значения decision."],
                    "enhancement": ["Явно различай завершённый ответ, сомнение, блокер и нарушение формата."],
                }
            )
        else:
            content = (
                "## Роль\n"
                "Ты ревьюер качества ответа агента.\n\n"
                "---\n\n"
                "## Задача\n"
                "Определи, можно ли переходить к финальному ответу или нужно вернуть управление координатору.\n\n"
                "---\n\n"
                "## Правила принятия решения\n"
                "- Если ответ агента явно завершён, проверен и не содержит открытых вопросов — выбери `continue_to_final`.\n"
                "- Если есть блокер, недоделка, неясность, отсутствие проверки или любое сомнение — выбери `reroute_to_coordinator`.\n"
                "- НИКОГДА не выбирай `continue_to_final`, если завершённость ответа не доказана.\n\n"
                "---\n\n"
                "## Формат ответа\n"
                "Отвечай только JSON-объектом:\n"
                "{\"decision\":\"continue_to_final|reroute_to_coordinator\",\"reason\":\"краткое обоснование\"}\n\n"
                "---\n\n"
                "<self_check>\n"
                "Перед отправкой проверь:\n"
                "□ Ответ является валидным JSON.\n"
                "□ Поле decision содержит только допустимое значение.\n"
                "□ При любом сомнении выбран reroute_to_coordinator.\n"
                "□ Нет Markdown и текста вне JSON.\n"
                "□ reason краткий и конкретный.\n"
                "Если хоть один пункт не выполнен — исправь до отправки.\n"
                "</self_check>"
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
            base_url=config.gigachat.base_url or os.getenv("GIGACHAT_BASE_URL"),
            default_model=config.model or "GigaChat-Pro",
        )
    raise ConfigError("Unsupported provider")
