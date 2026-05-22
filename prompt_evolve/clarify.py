"""Task clarification and executable task specification helpers."""

from __future__ import annotations

from .llm import generate_json
from .models import LLMProvider, TaskSpec
from .providers import FatalProviderError


DEFAULT_CLARIFICATION_QUESTIONS = [
    "Какой результат считается безусловно успешным?",
    "Какие ошибки недопустимы даже в редких случаях?",
    "Какой формат ответа должен быть строго соблюдён?",
    "Какие входные данные типичны, а какие считаются пограничными?",
    "Какие инструменты агенту разрешено использовать?",
    "Когда агент должен остановиться и запросить уточнение?",
]


def build_clarification_questions(task: str, prompt: str | None = None, *, max_questions: int = 8) -> list[str]:
    text = f"{task}\n{prompt or ''}".lower()
    questions = list(DEFAULT_CLARIFICATION_QUESTIONS)
    if "json" in text:
        questions.insert(0, "Какая точная JSON-схема ответа обязательна?")
    if "tool" in text or "mcp" in text or "инструмент" in text:
        questions.insert(0, "Какие tool calls разрешены, запрещены и требуют подтверждения?")
    if "сомнен" in text or "uncertain" in text:
        questions.insert(0, "Какую политику применять при сомнении или неполной информации?")
    return questions[:max_questions]


def build_task_spec(
    task: str,
    prompt: str | None,
    provider: LLMProvider,
    *,
    max_questions: int = 8,
    model: str | None = None,
    reasoning: str | None = None,
) -> TaskSpec:
    questions = build_clarification_questions(task, prompt, max_questions=max_questions)
    messages = [
        {
            "role": "system",
            "content": (
                "Ты архитектор eval-спецификаций для промптов. "
                "Верни только JSON с полями objective, input_contract, output_contract, "
                "success_criteria, failure_modes, tool_requirements."
            ),
        },
        {
            "role": "user",
            "content": (
                "<task>\n"
                f"{task}\n"
                "</task>\n\n"
                "<prompt>\n"
                f"{prompt or ''}\n"
                "</prompt>\n\n"
                "Собери исполнимую спецификацию для тестирования и улучшения промпта."
            ),
        },
    ]
    try:
        data = generate_json(provider, messages, model=model, reasoning=reasoning)
    except FatalProviderError:
        raise
    except Exception:
        data = {}
    success = data.get("success_criteria") if isinstance(data, dict) else None
    failures = data.get("failure_modes") if isinstance(data, dict) else None
    tools = data.get("tool_requirements") if isinstance(data, dict) else None
    return TaskSpec(
        objective=str(data.get("objective") or task.strip().splitlines()[0]) if isinstance(data, dict) else task,
        input_contract=str(data.get("input_contract") or "Пользовательский запрос или тестовый вход.") if isinstance(data, dict) else "Пользовательский запрос или тестовый вход.",
        output_contract=str(data.get("output_contract") or "Ответ должен строго соответствовать формату промпта.") if isinstance(data, dict) else "Ответ должен строго соответствовать формату промпта.",
        success_criteria=[str(item) for item in success] if isinstance(success, list) and success else [
            "Результат решает задачу пользователя.",
            "Соблюдён требуемый формат ответа.",
            "Нет неподтверждённых фактов или лишних допущений.",
        ],
        failure_modes=[str(item) for item in failures] if isinstance(failures, list) and failures else [
            "Нарушен формат ответа.",
            "Потеряно важное требование.",
            "Добавлена неподтверждённая информация.",
        ],
        clarification_questions=questions,
        tool_requirements=[str(item) for item in tools] if isinstance(tools, list) else [],
    )
