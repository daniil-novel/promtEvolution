# Prompt Evolution Report

## 1. Summary

Provider: `mock`
Model: `mock`

## 2. Input Task

Создай production-ready системный промпт для ревьюера качества ответа агента.

Ревьюер должен определить, можно ли переходить к финальному ответу, или нужно
вернуть управление координатору. При любом сомнении выбор должен быть
`reroute_to_coordinator`. Ответ ревьюера должен быть строго валидным JSON.

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


## 6. Metrics

| Metric | Final |
|---|---:|
| pass@1 | 1.00 |
| pass@k | 1.00 |
| average_score | 0.95 |
| failed_tests_count | 0 |

## 7. Test Cases Summary

Total test cases: 2

## 8. Failed Tests

No failed tests.

## 9. Generated SCOPE Guidelines

- corrective: Перед ответом проверяй точный JSON-формат и допустимые значения decision.
- enhancement: Явно различай завершённый ответ, сомнение, блокер и нарушение формата.

## 10. Iteration History

Best candidate: `iteration_1_baseline`

## 11. Workbench Artifacts

Strategy: `inspo_hybrid`
Population size: `2`
Generations: `1`

- `task_spec.yaml`
- `tool_policy.yaml`
- `reward_config.yaml`
- `promptfoo.yaml`
- `replay_buffer.json`
- `population.json`
- `failure_analysis.md`

## 12. Recommendations

Review failed cases and run another iteration if quality is below target.