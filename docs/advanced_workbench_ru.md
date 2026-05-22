# Advanced Workbench

`workbench` — самый сильный режим Prompt Evolution CLI. Он нужен, когда хочется не просто переписать промпт, а собрать production-ready prompt package: спецификацию задачи, тесты, популяцию кандидатов, replay buffer ошибок, reward-метрики и файлы для дальнейшей регрессии.

## Что делает режим

```text
сырой промпт
→ task_spec.yaml
→ tool_policy.yaml
→ тесты
→ INSPO-like population evolution
→ replay buffer слабых траекторий
→ reflection по ошибкам
→ final_prompt.md
→ promptfoo.yaml
→ report.md / report.json
```

## Запуск

```powershell
.\scripts\run-local.ps1 workbench --config examples\prompt_project.py --population-size 6 --generations 3 --out runs\advanced_prompt
```

Для быстрого локального smoke-теста без ключей:

```powershell
.\scripts\run-local.ps1 workbench --config examples\prompt_project.py --provider mock --population-size 2 --generations 1 --target-tests 2 --pass-k 1 --out runs\workbench_smoke
```

## Важные параметры

- `--population-size` — сколько инструкций живёт в популяции.
- `--generations` — сколько поколений эволюции пройти.
- `--elite-size` — сколько лучших инструкций переносить в следующее поколение.
- `--replay-buffer-size` — сколько слабых траекторий хранить для анализа.
- `--clarify-questions` — сколько уточняющих вопросов включить в `task_spec.yaml`.
- `--mcp-config` — путь к JSON/YAML конфигу MCP-серверов.

## Что такое INSPO-like

Этот режим вдохновлён идеей instruction-policy co-evolution:

1. Система держит популяцию промптов-инструкций.
2. Каждый кандидат прогоняется по тестам.
3. Для кандидата считается reward.
4. Слабые траектории попадают в replay buffer.
5. Лучшие инструкции становятся родителями.
6. Новые инструкции создаются через reflection по ошибкам.

В текущей версии мы не обучаем веса модели через RL. Мы эволюционируем инструкции и policy-текст вокруг задачи, инструментов, формата ответа и самопроверки.

## MCP и инструменты

`workbench` пока не запускает MCP-серверы сам. Он создаёт стабильную точку подключения:

```text
tool_policy.yaml
```

Если передать `--mcp-config`, имена серверов попадут в `allowed_tools`. Это нужно, чтобы финальный промпт и отчёт явно понимали, какие инструменты разрешены, какие запрещены и какие действия требуют подтверждения.

## Результаты

```text
runs/advanced_prompt/
  final_prompt.md
  task_spec.yaml
  tests.json
  reward_config.yaml
  tool_policy.yaml
  replay_buffer.json
  population.json
  failure_analysis.md
  promptfoo.yaml
  report.md
  report.json
```

Главный файл для использования в проекте — `final_prompt.md`.
