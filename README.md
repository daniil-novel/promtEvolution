# Prompt Evolution CLI

## Что это

Prompt Evolution CLI is a Python command-line utility for generating, evaluating, and improving prompts with the SCOPE cycle: Self-evolving Context Optimization via Prompt Evolution.

It is built for local terminal usage, including the VS Code terminal. It is not a web service.

## Возможности

- Generate or improve prompts.
- Generate, validate, and extend test cases.
- Evaluate prompt candidates with mocked or real LLM providers.
- Calculate pass@1, pass@k, and additional quality metrics.
- Save Markdown and JSON reports.
- Keep provider credentials in environment variables only.

## Установка

```bash
python -m pip install -e .[dev]
```

If your Windows environment has a broken global `pytest` executable, use `python -m pytest`.

Recommended local Windows setup uses an isolated `.venv` and avoids global `prompt-evolve.exe` conflicts:

```powershell
.\scripts\setup-local.ps1
.\scripts\run-local.ps1 --help
```

If global pip fails with `Failed to write executable` or `.deleteme`, do not fight the global Python install. Use the local setup above, then run commands through `.\scripts\run-local.ps1`.

## Быстрый старт

```bash
prompt-evolve run --task examples/task.md --provider mock --out runs/latest
```

Local `.venv` equivalent:

```powershell
.\scripts\run-local.ps1 run --task examples/task.md --provider mock --out runs/latest
```

The `mock` provider is deterministic and works offline. Use it for local smoke tests and CI-like checks.

## Настройка .env

Copy `.env.example` to `.env` and fill only local credentials. Never commit `.env`.

Recommended initialization on Windows PowerShell:

```powershell
.\scripts\init-env.ps1 -Provider openrouter
notepad .env
```

Or pass secrets through environment variables before running the script:

```powershell
$env:OPENROUTER_API_KEY = "paste_real_key_here"
.\scripts\init-env.ps1 -Provider openrouter -Force
```

Linux/macOS or Git Bash:

```bash
sh scripts/init-env.sh
$EDITOR .env
```

Or:

```bash
export OPENROUTER_API_KEY="paste_real_key_here"
FORCE=1 sh scripts/init-env.sh
```

The scripts create `.env` and `prompt-evolve.yaml`. Replace `PASTE_*` placeholders in `.env` with real secrets, then run the CLI.

## OpenRouter

Set `OPENROUTER_API_KEY` and run with `--provider openrouter`.

```bash
prompt-evolve run --task examples/task.md --provider openrouter --model openai/gpt-4.1
```

The key is read from the environment and is never written to reports or logs.

## GigaChat

Set `GIGACHAT_CREDENTIALS` and run with `--provider gigachat`.

```bash
prompt-evolve run --task examples/task.md --provider gigachat --model GigaChat-Pro
```

The GigaChat integration is isolated behind the provider interface. If `GIGACHAT_CREDENTIALS` or `base_url` is missing, the CLI exits with a clear configuration error.

For GigaChat, set either `gigachat.base_url` in `prompt-evolve.yaml` or `GIGACHAT_BASE_URL` in `.env`.

## Docker

Build the image:

```bash
docker compose build
```

Offline smoke test with the mock provider:

```bash
docker compose run --rm prompt-evolve run --task examples/task.md --provider mock --target-tests 2 --iterations 1 --candidates 2 --pass-k 2 --out runs/docker-smoke
```

Real OpenRouter run after editing `.env`:

```bash
docker compose run --rm prompt-evolve run --config prompt-evolve.yaml --task examples/task.md
```

For real project prompts, mount or keep your files under the repository folder and pass their paths, for example:

```bash
docker compose run --rm prompt-evolve run --config prompt-evolve.yaml --task my_project/task.md --prompt my_project/prompt.md --tests my_project/tests.json --out runs/my_project
```

## Основные команды

```bash
prompt-evolve run --task examples/task.md
prompt-evolve generate-tests --task examples/task.md --target-tests 40 --out runs/tests.json
prompt-evolve evaluate --task examples/task.md --prompt examples/prompt.md --tests examples/tests.json
prompt-evolve init-config --out prompt-evolve.yaml
```

Useful options:

- `--target-tests`: target number of test cases.
- `--iterations`: SCOPE improvement iterations.
- `--candidates`: prompt candidates per iteration.
- `--pass-k`: k value for pass@k; must be less than or equal to candidates.
- `--user-tests-only`: do not generate extra tests when a tests file is supplied.
- `--reasoning`: reasoning effort hint passed to providers when supported.
- `--self-check`: enable self-check regulators.
- `--config`: load YAML configuration, with CLI options taking priority.

## Python config

You can describe the whole run in a Python file instead of passing long CLI commands.

```powershell
.\scripts\run-local.ps1 run --config examples/prompt_project.py
```

Inside the Python config, use `PROMPT_EVOLVE = {...}` with `task`, `prompt`, optional `tests`, and `settings`.

```python
PROMPT_EVOLVE = {
    "task": {"text": "Describe what the final prompt must do."},
    "prompt": {"text": "Paste your current prompt here."},
    "settings": {
        "provider": "openrouter",
        "model": "openai/gpt-4.1",
        "target_tests": 20,
        "iterations": 2,
        "candidates": 3,
        "pass_k": 3,
        "output": {"dir": "runs/my_prompt_project"},
    },
}
```

See `docs/python_config_guide.md` for a detailed guide.

Русская короткая инструкция для сценария “сгенерировать тесты и улучшить промпт”:
`docs/quick_usage_ru.md`.

## Формат task.md

Markdown file describing the task and requirements.

## Формат prompt.md

Markdown file with the baseline prompt to improve.

## Формат tests.json

JSON array of test cases with `id`, `name`, `type`, `priority`, `input`, `expected_behavior`, and `evaluation_criteria`.

```json
[
  {
    "id": "TC-001",
    "name": "Basic happy path",
    "type": "happy_path",
    "priority": "high",
    "input": "Raw user input",
    "expected_behavior": "Expected assistant behavior",
    "evaluation_criteria": ["Preserves meaning", "Uses Markdown"]
  }
]
```

## Метрики

The CLI reports `pass@1`, `pass@k`, `format_pass_rate`, `critical_pass_rate`, `average_score`, `improvement_delta`, `failed_tests_count`, `token_usage`, and `estimated_cost` when usage data is available.

- `pass@1 = passed_tests / total_tests` for the best single prompt.
- `pass@k = tests passed by at least one of k candidates / total_tests`.

## SCOPE-цикл

Candidate prompt -> test execution -> evaluation -> error analysis -> guideline generation -> prompt update -> next iteration.

Generated guidelines are split into corrective and enhancement rules, then appended to the evolving prompt.

## Примеры запуска

```bash
prompt-evolve run --task examples/task.md --prompt examples/prompt.md --tests examples/tests.json --provider mock
```

## Тестирование

```bash
pytest
python -m pytest
```

## Проверка покрытия

```bash
pytest --cov=prompt_evolve --cov-report=term-missing --cov-report=html
python -m pytest --cov=prompt_evolve --cov-report=term-missing --cov-report=html
```

## Структура проекта

```text
prompt_evolve/
  cli.py
  config.py
  llm.py
  providers.py
  testcases.py
  prompts.py
  evaluator.py
  metrics.py
  scope.py
  report.py
tests/
  unit/
  integration/
examples/
runs/
```

## Troubleshooting

- Missing OpenRouter key: set `OPENROUTER_API_KEY` in `.env` or the shell.
- Missing GigaChat credentials: set `GIGACHAT_CREDENTIALS`.
- For offline testing, use `--provider mock`.
- `pass-k cannot be greater than candidates`: lower `--pass-k` or increase `--candidates`.
- Invalid tests file: ensure `tests.json` is a JSON array with all required fields.

## Гид по заливке проекта

See `docs/deployment_guide.md`. The detailed guide will be added after the user provides it.

## ChangeLog

See `CHANGELOG.md`.

## License

MIT.
