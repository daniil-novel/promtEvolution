# Prompt Evolution Report

## 1. Summary

Provider: `mock`
Model: `mock`

## 2. Input Task

# Task

Create a system prompt for an assistant that rewrites rough meeting notes into a concise status update.

# Requirements

- Preserve factual meaning.
- Remove repetitions.
- Keep action items visible.
- Use Markdown bullets.

## 3. Provider and Model

mock / mock

## 4. Baseline Prompt

No baseline prompt was provided.

## 5. Final Prompt

You are a precise assistant.
Goal: solve the user's task faithfully.
Rules: preserve facts, follow the requested format, avoid hallucinations, and self-check before responding.

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

Total test cases: 2

## 8. Failed Tests

No failed tests.

## 9. Generated SCOPE Guidelines

- corrective: Validate required format before answering.
- enhancement: Handle happy path and edge cases explicitly.

## 10. Iteration History

Best candidate: `iteration_1_candidate_1`

## 11. Recommendations

Review failed cases and run another iteration if quality is below target.