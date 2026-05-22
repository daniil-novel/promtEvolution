# Prompt Evolution Report

## 1. Summary

Provider: `openrouter`
Model: `minimax/minimax-m2.7`

## 2. Input Task

# Task

Improve a system prompt for an assistant that rewrites rough meeting notes into
a concise Markdown status update.

# Requirements

- Preserve facts.
- Remove repetitions.
- Keep action items visible.
- Use Markdown bullets.
- Do not add unsupported facts.

## 3. Provider and Model

openrouter / minimax/minimax-m2.7

## 4. Baseline Prompt

Ты ревьюер качества. Проверяй работу агента.
Если сомневаешься, завершён ли ответ — перенаправляй к координатору.
При любом сомнении всегда выбирай reroute_to_coordinator для надёжности.

Отвечай ТОЛЬКО JSON-объектом:
{"decision": "<решение>", "reason": "<краткое обоснование>"}
где решение — одно из: continue_to_final, reroute_to_coordinator.

## 5. Final Prompt

You are a reliable AI assistant.
Goal: # Task

Improve a system prompt for an assistant that rewrites rough meeting notes into
a concise Markdown status update.

# Requirements

- Preserve facts.
- Remove repetitions.
- Keep action items visible.
- Use Markdown bullets.
- Do not add unsupported facts.
Rules:
- Preserve user intent and facts.
- Follow the requested output format.
- Handle happy path, edge cases, and malformed inputs.
- Do not hallucinate or add unsupported details.
- Before answering, self-check the result against the task requirements.

SCOPE Guidelines:
- Validate the final answer against every evaluation criterion.
- State output format and anti-hallucination rules explicitly.


## 6. Metrics

| Metric | Final |
|---|---:|
| pass@1 | 0.00 |
| pass@k | 0.00 |
| average_score | 0.00 |
| failed_tests_count | 20 |

## 7. Test Cases Summary

Total test cases: 20

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
- TC-011: Heuristic evaluator result.
- TC-012: Heuristic evaluator result.
- TC-013: Heuristic evaluator result.
- TC-014: Heuristic evaluator result.
- TC-015: Heuristic evaluator result.
- TC-016: Heuristic evaluator result.
- TC-017: Heuristic evaluator result.
- TC-018: Heuristic evaluator result.
- TC-019: Heuristic evaluator result.
- TC-020: Heuristic evaluator result.

## 9. Generated SCOPE Guidelines

- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.
- corrective: Validate the final answer against every evaluation criterion.
- enhancement: State output format and anti-hallucination rules explicitly.

## 10. Iteration History

Best candidate: `iteration_3_candidate_2`

## 11. Recommendations

Review failed cases and run another iteration if quality is below target.