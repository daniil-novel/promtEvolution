"""Пример Python-сценария для улучшения промпта ревьюера качества.

Локальный безопасный запуск без реальных LLM-запросов:
    .\scripts\run-local.ps1 run --config examples\prompt_project.py

Чтобы использовать OpenRouter, поменяй provider/model в settings и вставь ключ в .env.
"""

RAW_PROMPT = """
Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.
"""

PROMPT_EVOLVE = {
    "task": {
        "text": f"""
# Задача

Преобразуй сырой промпт ревьюера качества в структурированный production-ready
системный промпт на русском языке.

<raw_prompt>
{RAW_PROMPT}
</raw_prompt>

---

## Что должен делать итоговый промпт

- Проверять, завершён ли ответ агента.
- Если завершённость очевидна, выбирать `continue_to_final`.
- Если есть любое сомнение, блокер, недоделка, неясность или нарушение формата,
  выбирать `reroute_to_coordinator`.
- Возвращать только JSON-объект.
- Не добавлять Markdown, комментарии или текст вне JSON.

---

## Техники prompt engineering, которые нужно применить

### 1. Секции
- `## Роль`
- `## Задача`
- `## Правила принятия решения`
- `## Формат ответа`
- `## Примеры`
- `<self_check>`

### 2. Точный JSON-контракт
Опиши схему:
`{{"decision":"continue_to_final|reroute_to_coordinator","reason":"..."}}`

### 3. Критичный запрет
Используй один критичный запрет через `НИКОГДА`: не выбирать `continue_to_final`,
если есть хотя бы одно сомнение.

### 4. Самопроверка
Добавь 5-8 пунктов проверки перед ответом.

---

## Формат результата

Готовый системный промпт в Markdown. Без объяснений — только промпт для копирования.
""",
    },
    "prompt": {
        "text": RAW_PROMPT,
    },
    "tests": {
        "cases": [
            {
                "id": "TC-001",
                "name": "Явно завершённый ответ агента",
                "type": "happy_path",
                "priority": "high",
                "input": "Агент сообщил: задача выполнена, тесты пройдены, отчёт сохранён, открытых вопросов нет.",
                "expected_behavior": "Вернуть только JSON с decision=continue_to_final.",
                "evaluation_criteria": [
                    "Ответ является валидным JSON-объектом",
                    "decision равен continue_to_final",
                    "reason кратко объясняет, что работа завершена",
                    "Нет текста вне JSON",
                ],
            },
            {
                "id": "TC-002",
                "name": "Есть сомнение в завершённости",
                "type": "edge_case",
                "priority": "high",
                "input": "Агент написал: почти всё готово, но я не запускал интеграционный тест.",
                "expected_behavior": "Вернуть только JSON с decision=reroute_to_coordinator.",
                "evaluation_criteria": [
                    "При сомнении выбран reroute_to_coordinator",
                    "reason указывает на отсутствующую проверку",
                    "Нет Markdown и текста вне JSON",
                ],
            },
        ],
    },
    "settings": {
        "provider": "mock",
        "model": "mock",
        "target_tests": 8,
        "iterations": 2,
        "candidates": 3,
        "pass_k": 3,
        "reasoning": "max",
        "self_check": True,
        "user_tests_only": False,
        "output": {
            "dir": "runs/reviewer_prompt",
            "save_markdown_report": True,
            "save_json_report": True,
            "save_final_prompt": True,
        },
    },
}
