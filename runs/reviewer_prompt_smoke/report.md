# Prompt Evolution Report

## 1. Summary

Provider: `mock`
Model: `mock`

## 2. Input Task

# Задача

Преобразуй сырой промпт ревьюера качества в структурированный production-ready
системный промпт на русском языке.

<raw_prompt>

Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.

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
`{"decision":"continue_to_final|reroute_to_coordinator","reason":"..."}`

### 3. Критичный запрет
Используй один критичный запрет через `НИКОГДА`: не выбирать `continue_to_final`,
если есть хотя бы одно сомнение.

### 4. Самопроверка
Добавь 5-8 пунктов проверки перед ответом.

---

## Формат результата

Готовый системный промпт в Markdown. Без объяснений — только промпт для копирования.

## 3. Provider and Model

mock / mock

## 4. Baseline Prompt

Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.

## 5. Final Prompt

Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.

SCOPE Guidelines:
- Перед ответом проверяй точный JSON-формат и допустимые значения decision.
- Явно различай завершённый ответ, сомнение, блокер и нарушение формата.

SCOPE Guidelines:
- Перед ответом проверяй точный JSON-формат и допустимые значения decision.
- Явно различай завершённый ответ, сомнение, блокер и нарушение формата.


## 6. Metrics

| Metric | Final |
|---|---:|
| pass@1 | 1.00 |
| pass@k | 1.00 |
| average_score | 0.95 |
| failed_tests_count | 0 |

## 7. Test Cases Summary

Total test cases: 8

## 8. Failed Tests

No failed tests.

## 9. Generated SCOPE Guidelines

- corrective: Перед ответом проверяй точный JSON-формат и допустимые значения decision.
- enhancement: Явно различай завершённый ответ, сомнение, блокер и нарушение формата.
- corrective: Перед ответом проверяй точный JSON-формат и допустимые значения decision.
- enhancement: Явно различай завершённый ответ, сомнение, блокер и нарушение формата.

## 10. Iteration History

Best candidate: `iteration_2_baseline`

## 11. Recommendations

Review failed cases and run another iteration if quality is below target.