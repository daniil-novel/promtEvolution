"""Prompt candidate generation and selection."""

from __future__ import annotations

from .llm import generate_text
from .models import LLMProvider, PromptCandidate, PromptRunResult
from .providers import FatalProviderError


PROMPT_ENGINEERING_TECHNIQUES = """
## Техники усиления промпта

Применяй только там, где это помогает задаче:

### 1. Секции и заголовки
- `## Роль`
- `## Задача`
- `## Входные данные`
- `## Правила принятия решения`
- `## Формат ответа`
- `## Самопроверка`

### 2. Явные ограничения
- Один критичный запрет можно выделить через `НИКОГДА`.
- Остальные правила формулируй спокойно и проверяемо.

### 3. Структурированные значения
- Для enum-значений используй backticks.
- Для JSON-формата показывай точную схему.
- Для неизменяемых правил используй отдельный блок.

### 4. Самопроверка
- Добавляй `<self_check>` с 5-8 конкретными пунктами.
- Если пункт не выполнен, модель должна исправить ответ до отправки.

### 5. Токенное разделение
- Списки: `элемент1, элемент2, элемент3`.
- Коды и enum: `continue_to_final`, `reroute_to_coordinator`.
- Длинные инструкции разбивай на короткие абзацы и списки.
""".strip()


DEFAULT_PROMPT_UPGRADE_TASK = """
Преобразуй сырой промпт пользователя в структурированный production-ready системный промпт.

Сохрани исходную задачу, смысл, ограничения и обязательный формат ответа. Не добавляй
требования, которых нет в исходном промпте. Усиль промпт лучшими практиками
prompt engineering: ясная роль, цель, границы ответственности, правила, формат ответа,
обработка пограничных случаев, политика при неопределённости и блок самопроверки.

Итоговый промпт должен быть на русском языке, если исходный промпт не требует другого языка.
Верни только готовый промпт в Markdown, без пояснений вне промпта.
""".strip()


def build_seed_prompt(task: str) -> str:
    return (
        "## Роль\n"
        "Ты надёжный AI-ассистент, который строго следует заданному системному промпту.\n\n"
        "---\n\n"
        "## Задача\n"
        f"{task.strip()}\n\n"
        "---\n\n"
        "## Правила\n"
        "- Сохраняй исходный смысл и все обязательные ограничения.\n"
        "- Делай правила проверяемыми и однозначными.\n"
        "- Явно задавай допустимые значения, формат ответа и условия выбора.\n"
        "- Обрабатывай happy path, пограничные случаи, неоднозначность и ошибочные входы.\n"
        "- НИКОГДА не добавляй факты и требования, которых нет в задаче.\n\n"
        "---\n\n"
        "## Формат ответа\n"
        "Верни результат в формате, который требует задача.\n\n"
        "---\n\n"
        "<self_check>\n"
        "Перед отправкой проверь:\n"
        "□ Все обязательные правила задачи сохранены.\n"
        "□ Формат ответа соответствует требованию.\n"
        "□ Нет лишних пояснений, если задача требует только результат.\n"
        "□ Нет выдуманных фактов или новых ограничений.\n"
        "□ Неоднозначные случаи обработаны явно.\n"
        "Если хоть один пункт не выполнен — исправь ответ до отправки.\n"
        "</self_check>\n"
    )


def generate_prompt_candidates(
    task: str,
    baseline_prompt: str | None,
    provider: LLMProvider,
    *,
    count: int,
    iteration: int,
    model: str | None = None,
    reasoning: str | None = None,
) -> list[PromptCandidate]:
    candidates: list[PromptCandidate] = []
    if baseline_prompt:
        candidates.append(PromptCandidate(id=f"iteration_{iteration}_baseline", content=baseline_prompt, iteration=iteration))
    while len(candidates) < count:
        candidate_number = len(candidates) + 1
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты senior prompt engineer. Улучши системный промпт на русском языке. "
                    "Верни только готовый промпт в Markdown, без объяснений."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Преобразуй сырой промпт в структурированный production-ready системный промпт.\n\n"
                    "<raw_task>\n"
                    f"{task}\n"
                    "</raw_task>\n\n"
                    "<raw_prompt>\n"
                    f"{baseline_prompt or 'Создай промпт с нуля на основе задачи.'}\n"
                    "</raw_prompt>\n\n"
                    f"{PROMPT_ENGINEERING_TECHNIQUES}\n\n"
                    "## Требования к результату\n"
                    "- Сохрани исходный смысл.\n"
                    "- Разбей промпт на понятные секции.\n"
                    "- Добавь точный формат ответа.\n"
                    "- Добавь правила для спорных и пограничных случаев.\n"
                    "- Добавь блок `<self_check>`.\n"
                    "- Не добавляй объяснений вне промпта.\n\n"
                    f"Создай вариант промпта №{candidate_number}."
                ),
            },
        ]
        try:
            content = generate_text(provider, messages, model=model, reasoning=reasoning)
        except FatalProviderError:
            raise
        except Exception:
            content = build_seed_prompt(task)
        candidates.append(
            PromptCandidate(
                id=f"iteration_{iteration}_candidate_{candidate_number}",
                content=content,
                iteration=iteration,
            )
        )
    return candidates[:count]


def select_best_prompt(results: list[PromptRunResult]) -> PromptRunResult:
    if not results:
        raise ValueError("No prompt results to select from")

    def structure_score(prompt: str) -> int:
        markers = [
            "## Роль",
            "## Задача",
            "## Правила",
            "## Формат ответа",
            "<self_check>",
            "decision",
            "reroute_to_coordinator",
            "continue_to_final",
        ]
        return sum(1 for marker in markers if marker in prompt)

    def key(result: PromptRunResult) -> tuple[float, float, float, int, int, int, int]:
        total = max(len(result.evaluations), 1)
        pass_rate = sum(1 for item in result.evaluations if item.passed) / total
        critical = [
            item
            for item in result.evaluations
            if item.test_case_id and item.error_type != "non_critical_marker"
        ]
        critical_rate = sum(1 for item in critical if item.passed) / max(len(critical), 1)
        avg_score = sum(item.score for item in result.evaluations) / total
        format_violations = sum(1 for item in result.evaluations if item.error_type == "format_violation")
        is_baseline = 1 if result.candidate.id.endswith("_baseline") else 0
        return (
            pass_rate,
            critical_rate,
            avg_score,
            structure_score(result.candidate.content),
            -format_violations,
            -is_baseline,
            -len(result.candidate.content),
        )

    return max(results, key=key)
