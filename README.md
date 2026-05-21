# Prompt Evolution CLI

## Что это

Prompt Evolution CLI is a Python command-line utility for generating, evaluating, and improving prompts with the SCOPE cycle.

## Возможности

- Generate or improve prompts.
- Generate, validate, and extend test cases.
- Evaluate prompt candidates with mocked or real LLM providers.
- Calculate pass@1, pass@k, and additional quality metrics.
- Save Markdown and JSON reports.

## Установка

```bash
python -m pip install -e .[dev]
```

## Быстрый старт

```bash
prompt-evolve run --task examples/task.md --provider mock --out runs/latest
```

## Настройка .env

Copy `.env.example` to `.env` and fill only local credentials. Never commit `.env`.

## OpenRouter

Set `OPENROUTER_API_KEY` and run with `--provider openrouter`.

## GigaChat

Set `GIGACHAT_CREDENTIALS` and run with `--provider gigachat`.

## Основные команды

```bash
prompt-evolve run --task examples/task.md
prompt-evolve generate-tests --task examples/task.md --target-tests 40 --out runs/tests.json
prompt-evolve evaluate --task examples/task.md --prompt examples/prompt.md --tests examples/tests.json
prompt-evolve init-config --out prompt-evolve.yaml
```

## Формат task.md

Markdown file describing the task and requirements.

## Формат prompt.md

Markdown file with the baseline prompt to improve.

## Формат tests.json

JSON array of test cases with `id`, `name`, `type`, `priority`, `input`, `expected_behavior`, and `evaluation_criteria`.

## Метрики

The CLI reports `pass@1`, `pass@k`, `format_pass_rate`, `critical_pass_rate`, `average_score`, `improvement_delta`, `failed_tests_count`, `token_usage`, and `estimated_cost` when usage data is available.

## SCOPE-цикл

Candidate prompt -> test execution -> evaluation -> error analysis -> guideline generation -> prompt update -> next iteration.

## Примеры запуска

```bash
prompt-evolve run --task examples/task.md --prompt examples/prompt.md --tests examples/tests.json --provider mock
```

## Тестирование

```bash
pytest
```

## Проверка покрытия

```bash
pytest --cov=prompt_evolve --cov-report=term-missing --cov-report=html
```

## Структура проекта

Core code is in `prompt_evolve/`; unit and integration tests are in `tests/`.

## Troubleshooting

- Missing OpenRouter key: set `OPENROUTER_API_KEY` in `.env` or the shell.
- Missing GigaChat credentials: set `GIGACHAT_CREDENTIALS`.
- For offline testing, use `--provider mock`.

## Гид по заливке проекта

See `docs/deployment_guide.md`. The detailed guide will be added after the user provides it.

## ChangeLog

See `CHANGELOG.md`.

## License

MIT.
