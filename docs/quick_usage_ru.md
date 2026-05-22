# Быстрый сценарий: улучшить промпт и сгенерировать тесты

## 1. Подготовить локальный запуск

```powershell
.\scripts\setup-local.ps1
.\scripts\init-env.ps1 -Provider openrouter -Force
notepad .env
```

В `.env` вставь реальный `OPENROUTER_API_KEY`.

Для локальной проверки без ключей используй `provider: mock` в Python-конфиге.

Если используешь OpenRouter с `deepseek/deepseek-v4-flash`, можно оставить
`reasoning: "max"` — CLI автоматически отправит в OpenRouter допустимое значение
`xhigh`. Если модель не поддерживает structured output, CLI повторит JSON-запрос
без `response_format`.

## 2. Описать промпт в Python-конфиге

Открой `examples/prompt_project.py`.

Там есть:

- `RAW_PROMPT` — сырой промпт, который нужно улучшить.
- `task.text` — необязательное поле; если его нет, используется универсальная задача апгрейда промпта.
- `tests.cases` — ручные тесты.
- `settings.target_tests` — сколько тестов должно быть в итоге.
- `settings.iterations` — сколько циклов улучшения.
- `settings.candidates` — сколько вариантов промпта пробовать.
- `settings.output.dir` — куда сохранять результат.

Для обычного сценария достаточно менять только `RAW_PROMPT` и настройки модели. Универсальная задача уже встроена в CLI.

Минимальный обезличенный пример такого файла есть здесь:

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_only_project.py
```

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

## 5. Самый сильный режим Workbench

Если нужен не просто SCOPE-апгрейд, а более мощный prompt engineering workflow с уточнением задачи, популяцией инструкций, replay buffer и export для Promptfoo:

```powershell
.\scripts\run-local.ps1 workbench --config examples\prompt_project.py --population-size 6 --generations 3 --out runs\advanced_reviewer_prompt
```

Для дешёвой проверки:

```powershell
.\scripts\run-local.ps1 workbench --config examples\prompt_project.py --provider mock --population-size 2 --generations 1 --target-tests 2 --pass-k 1 --out runs\workbench_smoke
```

Главные результаты:

```text
runs/advanced_reviewer_prompt/final_prompt.md
runs/advanced_reviewer_prompt/task_spec.yaml
runs/advanced_reviewer_prompt/tool_policy.yaml
runs/advanced_reviewer_prompt/replay_buffer.json
runs/advanced_reviewer_prompt/failure_analysis.md
runs/advanced_reviewer_prompt/promptfoo.yaml
```

`task_spec.yaml` показывает, какую задачу реально оптимизирует система.  
`replay_buffer.json` хранит слабые траектории для reflection.  
`promptfoo.yaml` можно использовать как стартовый regression config.

## 6. Быстрый дешёвый прогон

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_project.py --target-tests 4 --iterations 1 --candidates 2 --pass-k 2 --out runs\quick_reviewer_prompt
```

## 7. Реальный OpenRouter-прогон

В `examples/prompt_project.py` поменяй:

```python
"provider": "openrouter",
"model": "openai/gpt-4.1",
```

Затем:

```powershell
.\scripts\run-local.ps1 run --config examples\prompt_project.py
```
