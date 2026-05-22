RAW_PROMPT = """
Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.
""".strip()


PROMPT_EVOLVE = {
    "task": {
        "text": """
Создай production-ready системный промпт для ревьюера качества ответа агента.

Ревьюер должен определить, можно ли переходить к финальному ответу, или нужно
вернуть управление координатору. При любом сомнении выбор должен быть
`reroute_to_coordinator`. Ответ ревьюера должен быть строго валидным JSON.
""".strip()
    },
    "prompt": {"text": RAW_PROMPT},
    "settings": {
        "provider": "mock",
        "model": "mock",
        "target_tests": 8,
        "iterations": 2,
        "candidates": 4,
        "pass_k": 4,
        "reasoning": "max",
        "self_check": True,
        "output": {"dir": "runs/advanced_reviewer_prompt"},
    },
}
