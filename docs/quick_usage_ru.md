# Быстрый сценарий: улучшить промпт и сгенерировать тесты

## 1. Подготовить локальный запуск

```powershell
.\scripts\setup-local.ps1
.\scripts\init-env.ps1 -Provider openrouter -Force
notepad .env
```

В `.env` вставь реальный `OPENROUTER_API_KEY`.

Для локальной проверки без ключей используй `provider: mock` в Python-конфиге.

## 2. Описать промпт в Python-конфиге

Открой `examples/prompt_project.py`.

Там есть:

- `RAW_PROMPT` — сырой промпт, который нужно улучшить.
- `task.text` — что именно нужно получить после улучшения.
- `tests.cases` — ручные тесты.
- `settings.target_tests` — сколько тестов должно быть в итоге.
- `settings.iterations` — сколько циклов улучшения.
- `settings.candidates` — сколько вариантов промпта пробовать.
- `settings.output.dir` — куда сохранять результат.

## 3. Сгенерировать только тесты

```powershell
.\scripts\run-local.ps1 generate-tests --config examples\prompt_project.py --out runs\reviewer_prompt_tests.json
```

Результат:

```text
runs/reviewer_prompt_tests.json
```

## 4. Улучшить промпт

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_project.py
```

Результат:

```text
runs/reviewer_prompt/final_prompt.md
runs/reviewer_prompt/report.md
runs/reviewer_prompt/report.json
runs/reviewer_prompt/tests.json
```

Главный файл — `final_prompt.md`. Его и копируй в свой проект.

## 5. Быстрый дешёвый прогон

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_project.py --target-tests 4 --iterations 1 --candidates 2 --pass-k 2 --out runs\quick_reviewer_prompt
```

## 6. Реальный OpenRouter-прогон

В `examples/prompt_project.py` поменяй:

```python
"provider": "openrouter",
"model": "openai/gpt-4.1",
```

Затем:

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_project.py
```
