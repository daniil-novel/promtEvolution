"""Минимальный prompt-only пример.

Обычно здесь нужно менять только RAW_PROMPT и настройки в settings.
Поле task отсутствует намеренно: CLI автоматически подставит универсальную
задачу апгрейда промпта.
"""

RAW_PROMPT = """
Ты ассистент, который превращает грубые заметки встречи в короткий статус-апдейт.
Сохраняй факты, удаляй повторы, показывай action items. Отвечай Markdown-списком.
""".strip()


PROMPT_EVOLVE = {
    "prompt": {"text": RAW_PROMPT},
    "settings": {
        "provider": "mock",
        "model": "mock",
        "target_tests": 4,
        "iterations": 1,
        "candidates": 2,
        "pass_k": 2,
        "reasoning": "max",
        "self_check": True,
        "output": {"dir": "runs/prompt_only_example"},
    },
}
