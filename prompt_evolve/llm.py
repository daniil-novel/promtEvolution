"""LLM helper utilities."""

from __future__ import annotations

import json
from typing import Any

from .models import LLMProvider


class LLMJsonError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""


def parse_json_response(content: str) -> Any:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMJsonError("LLM returned invalid JSON") from exc


def generate_json(
    provider: LLMProvider,
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    reasoning: str | None = None,
) -> Any:
    first = provider.generate(
        messages,
        model=model,
        reasoning=reasoning,
        response_format="json",
    )
    try:
        return parse_json_response(first.content)
    except LLMJsonError:
        retry_messages = messages + [
            {
                "role": "user",
                "content": "Return only valid JSON. Do not include Markdown fences or commentary.",
            }
        ]
        second = provider.generate(
            retry_messages,
            model=model,
            reasoning=reasoning,
            response_format="json",
        )
        return parse_json_response(second.content)


def generate_text(
    provider: LLMProvider,
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    reasoning: str | None = None,
) -> str:
    return provider.generate(messages, model=model, reasoning=reasoning).content.strip()
