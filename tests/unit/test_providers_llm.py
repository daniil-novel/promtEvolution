import json

import httpx
import pytest

from prompt_evolve.config import AppConfig, ConfigError
from prompt_evolve.llm import LLMJsonError, generate_json, parse_json_response
from prompt_evolve.providers import (
    GigaChatProvider,
    MockProvider,
    OpenRouterProvider,
    ProviderError,
    provider_from_config,
)


def test_provider_factory_mock():
    assert provider_from_config(AppConfig(provider="mock")).name == "mock"


def test_mock_provider_returns_russian_prompt():
    response = MockProvider().generate([{"role": "user", "content": "Создай промпт"}])
    assert "## Роль" in response.content
    assert "reroute_to_coordinator" in response.content


def test_gigachat_factory_reads_base_url_from_env(monkeypatch):
    monkeypatch.setenv("GIGACHAT_BASE_URL", "https://gigachat.env.test")
    provider = provider_from_config(AppConfig(provider="gigachat"))
    assert provider.base_url == "https://gigachat.env.test"


def test_openrouter_missing_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider().check_configured()


def test_openrouter_placeholder_key_is_missing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "PASTE_OPENROUTER_API_KEY_HERE")
    with pytest.raises(ConfigError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider().check_configured()


def test_gigachat_missing_credentials(monkeypatch):
    monkeypatch.delenv("GIGACHAT_CREDENTIALS", raising=False)
    with pytest.raises(ConfigError, match="GIGACHAT_CREDENTIALS"):
        GigaChatProvider(base_url="https://example.test").check_configured()


def test_gigachat_placeholder_credentials_are_missing(monkeypatch):
    monkeypatch.setenv("GIGACHAT_CREDENTIALS", "your_gigachat_credentials_here")
    with pytest.raises(ConfigError, match="GIGACHAT_CREDENTIALS"):
        GigaChatProvider(base_url="https://example.test").check_configured()


def test_gigachat_missing_base_url(monkeypatch):
    monkeypatch.setenv("GIGACHAT_CREDENTIALS", "secret")
    with pytest.raises(ConfigError, match="base_url"):
        GigaChatProvider().check_configured()


def test_openrouter_generate_with_mock_http(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        payload = json.loads(request.content)
        assert payload["reasoning"]["effort"] == "xhigh"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "hello"}}],
                "usage": {"total_tokens": 3},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    response = OpenRouterProvider(client=client).generate(
        [{"role": "user", "content": "Hi"}],
        reasoning="max",
    )
    assert response.content == "hello"
    assert response.usage["total_tokens"] == 3


def test_openrouter_rejects_unknown_reasoning(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    with pytest.raises(ConfigError, match="OpenRouter reasoning"):
        OpenRouterProvider().generate([{"role": "user", "content": "Hi"}], reasoning="turbo")


def test_openrouter_error_includes_api_message(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"code": 400, "message": "Invalid reasoning effort"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="Invalid reasoning effort"):
        OpenRouterProvider(client=client).generate([{"role": "user", "content": "Hi"}])


def test_openrouter_json_response_format_retries_without_structured_output(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        calls.append(payload)
        if "response_format" in payload:
            return httpx.Response(
                400,
                json={"error": {"code": 400, "message": "response_format is not supported"}},
            )
        return httpx.Response(200, json={"choices": [{"message": {"content": "{\"ok\": true}"}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    response = OpenRouterProvider(client=client).generate(
        [{"role": "user", "content": "Return JSON"}],
        response_format="json",
    )
    assert response.content == "{\"ok\": true}"
    assert len(calls) == 2
    assert "response_format" not in calls[1]


def test_gigachat_generate_with_mock_http(monkeypatch):
    monkeypatch.setenv("GIGACHAT_CREDENTIALS", "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = GigaChatProvider(base_url="https://gigachat.test", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert provider.generate([{"role": "user", "content": "Hi"}]).content == "ok"


def test_parse_json_response_fenced():
    assert parse_json_response("```json\n{\"a\": 1}\n```") == {"a": 1}


def test_parse_json_response_invalid():
    with pytest.raises(LLMJsonError):
        parse_json_response("not-json")


def test_generate_json_retries_invalid():
    class RetryProvider(MockProvider):
        def __init__(self):
            self.calls = 0

        def generate(self, messages, *, model=None, reasoning=None, response_format=None):
            self.calls += 1
            if self.calls == 1:
                return type("Resp", (), {"content": "bad"})()
            return type("Resp", (), {"content": json.dumps({"ok": True})})()

    provider = RetryProvider()
    assert generate_json(provider, [{"role": "user", "content": "x"}]) == {"ok": True}
    assert provider.calls == 2
