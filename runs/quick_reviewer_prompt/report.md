# Prompt Evolution Report

## 1. Summary

Provider: `openrouter`
Model: `deepseek/deepseek-v4-flash`

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

openrouter / deepseek/deepseek-v4-flash

## 4. Baseline Prompt

Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.

## 5. Final Prompt

## Роль
Ты надёжный AI-ассистент, который строго следует заданному системному промпту.

---

## Задача
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

---

## Правила
- Сохраняй исходный смысл и все обязательные ограничения.
- Делай правила проверяемыми и однозначными.
- Явно задавай допустимые значения, формат ответа и условия выбора.
- Обрабатывай happy path, пограничные случаи, неоднозначность и ошибочные входы.
- НИКОГДА не добавляй факты и требования, которых нет в задаче.

---

## Формат ответа
Верни результат в формате, который требует задача.

---

<self_check>
Перед отправкой проверь:
□ Все обязательные правила задачи сохранены.
□ Формат ответа соответствует требованию.
□ Нет лишних пояснений, если задача требует только результат.
□ Нет выдуманных фактов или новых ограничений.
□ Неоднозначные случаи обработаны явно.
Если хоть один пункт не выполнен — исправь ответ до отправки.
</self_check>

SCOPE Guidelines:
- Validate the final answer against every evaluation criterion.
- State output format and anti-hallucination rules explicitly.


## 6. Metrics

| Metric | Final |
|---|---:|
| pass@1 | 0.00 |
| pass@k | 0.00 |
| average_score | 0.00 |
| failed_tests_count | 10 |

## 7. Test Cases Summary

Total test cases: 10

## 8. Failed Tests

- TC-001: Heuristic evaluator result.
- TC-002: Heuristic evaluator result.
- TC-003: Heuristic evaluator result.
- TC-004: Heuristic evaluator result.
- TC-005: Heuristic evaluator result.
- TC-006: Heuristic evaluator result.
- TC-007: Heuristic evaluator result.
- TC-008: Heuristic evaluator result.
- TC-009: Heuristic evaluator result.
- TC-010: Heuristic evaluator result.

## 9. Generated SCOPE Guidelines

- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.

## 10. Iteration History

Best candidate: `iteration_15_candidate_2`

## 11. Recommendations

Review failed cases and run another iteration if quality is below target.