# Prompt Evolution Report

## 1. Summary

Provider: `mock`
Model: `mock`

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

mock / mock

## 4. Baseline Prompt

You are a careful writing assistant. Rewrite rough notes into a concise Markdown
status update. Preserve facts, remove repetition, and keep action items visible.

## 5. Final Prompt

You are a careful writing assistant. Rewrite rough notes into a concise Markdown
status update. Preserve facts, remove repetition, and keep action items visible.

SCOPE Guidelines:
- Validate required format before answering.
- Handle happy path and edge cases explicitly.


## 6. Metrics

| Metric | Final |
|---|---:|
| pass@1 | 1.00 |
| pass@k | 1.00 |
| average_score | 0.95 |
| failed_tests_count | 0 |

## 7. Test Cases Summary

Total test cases: 4

## 8. Failed Tests

No failed tests.

## 9. Generated SCOPE Guidelines

- corrective: Validate required format before answering.
- enhancement: Handle happy path and edge cases explicitly.

## 10. Iteration History

Best candidate: `iteration_1_baseline`

## 11. Recommendations

Review failed cases and run another iteration if quality is below target.