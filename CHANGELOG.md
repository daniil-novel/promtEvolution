# ChangeLog

## 2026-05-22 — Commit: pending

### Что изменено

- Версия проекта поднята до `0.2.0`.
- Добавлена команда `prompt-evolve workbench` для advanced prompt workbench.
- Добавлены слои `clarify`, `mcp_tools`, `rewards`, `trajectories`, `inspo`, `workbench`.
- Реализован INSPO-like цикл: популяция инструкций, reward scoring, elite selection, mutation через reflection и replay buffer.
- Добавлены артефакты `task_spec.yaml`, `tool_policy.yaml`, `reward_config.yaml`, `replay_buffer.json`, `population.json`, `failure_analysis.md`, `promptfoo.yaml`.
- Добавлен пример `examples/advanced_prompt_project.py`.
- README и русские инструкции дополнены режимом Workbench.

### Для чего это нужно

- Это переводит проект из простого SCOPE-улучшателя промптов в более мощный PromptOps/workbench-инструмент для реальных проектов.
- Пользователь получает не только финальный промпт, но и спецификацию задачи, policy инструментов, регрессионный export и историю слабых траекторий.

### Почему это сделано именно так

- Workbench добавлен отдельной командой, чтобы не ломать стабильные команды `run`, `generate-tests` и `evaluate`.
- MCP реализован как безопасная extension point/policy layer, без автоматического запуска внешних серверов и без риска side effects.
- INSPO-like подход эволюционирует инструкции и policy-текст без попытки обучать веса модели внутри CLI.

### Затронутые файлы

- `pyproject.toml`
- `prompt_evolve/cli.py`
- `prompt_evolve/models.py`
- `prompt_evolve/clarify.py`
- `prompt_evolve/mcp_tools.py`
- `prompt_evolve/rewards.py`
- `prompt_evolve/trajectories.py`
- `prompt_evolve/inspo.py`
- `prompt_evolve/workbench.py`
- `prompt_evolve/report.py`
- `tests/unit/test_workbench_components.py`
- `tests/integration/test_cli.py`
- `examples/advanced_prompt_project.py`
- `docs/advanced_workbench_ru.md`
- `docs/quick_usage_ru.md`
- `README.md`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`
- CLI smoke через `workbench` с mock provider покрыт integration-тестом.

### Риски

- Workbench пока не запускает реальные MCP-серверы сам; он создаёт policy/export слой для безопасной интеграции.
- INSPO-like режим оптимизирует инструкции по eval reward, но не выполняет RL-обучение весов модели.

## 2026-05-21 — Commit: be73146

### Что изменено

- Пример `examples/prompt_project.py` переписан под реальный промпт ревьюера качества.
- Fallback-генерация тесткейсов теперь создаёт русские, разнообразные и предметные тесты вместо одинаковых generic-примеров.
- Базовый seed prompt и mock provider теперь возвращают русскоязычный структурированный системный промпт с prompt engineering техниками и `<self_check>`.
- Выбор лучшего промпта теперь предпочитает структурированные кандидаты при равных метриках, а не короткий baseline.
- После удаления дублей тесткейсы добираются до `target_tests` и перенумеровываются последовательно.
- Повторяющиеся `SCOPE Guidelines` больше не накапливаются в финальном промпте.
- Добавлена короткая русская инструкция `docs/quick_usage_ru.md`.

### Для чего это нужно

- Локальный запуск без реального LLM теперь даёт понятный результат и показывает правильный workflow для генерации тестов и улучшения промпта.

### Почему это сделано именно так

- `mock` остаётся безопасным демонстрационным режимом, а реальные качественные улучшения можно запускать через OpenRouter после настройки `.env`.

### Затронутые файлы

- `prompt_evolve/prompts.py`
- `prompt_evolve/testcases.py`
- `prompt_evolve/providers.py`
- `prompt_evolve/scope.py`
- `examples/task.md`
- `examples/prompt_project.py`
- `docs/quick_usage_ru.md`
- `README.md`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`
- Smoke-run `generate-tests` и `run` для `examples/prompt_project.py`.

### Риски

- Mock-режим показывает структуру и workflow, но не заменяет реальный OpenRouter-прогон для production-качества.

## 2026-05-21 — Commit: c0e55ec

### Что изменено

- Добавлена поддержка Python scenario config через `PROMPT_EVOLVE = {...}`.
- CLI-команды `run`, `generate-tests` и `evaluate` теперь могут брать task/prompt/tests из config-файла.
- Добавлены пример `examples/prompt_project.py` и подробный guide `docs/python_config_guide.md`.

### Для чего это нужно

- Пользователь может описывать промпт, задачу, тесты и настройки в одном понятном Python-файле вместо длинных команд.

### Почему это сделано именно так

- Python config остаётся простым dict-форматом, а CLI-аргументы сохраняют приоритет для быстрых override.

### Затронутые файлы

- `prompt_evolve/config.py`
- `prompt_evolve/cli.py`
- `prompt_evolve/pipeline.py`
- `examples/prompt_project.py`
- `docs/python_config_guide.md`
- `README.md`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`
- Smoke-run через `.\scripts\run-local.ps1 run --config examples/prompt_project.py`.

### Риски

- Python config исполняется как локальный Python-файл, поэтому использовать нужно только доверенные config-файлы.

## 2026-05-21 — Commit: 324753e

### Что изменено

- Добавлены локальные setup/launcher scripts для запуска без Docker и без зависимости от глобального `prompt-evolve.exe`.
- README дополнен обходом Windows/pip ошибки `Failed to write executable ... .deleteme`.
- Placeholder-секреты `PASTE_*` и `your_*` больше не считаются валидной конфигурацией provider.
- `run-local.ps1` передаёт CLI-аргументы через raw `$args`, чтобы PowerShell не перехватывал флаги вроде `--out`.

### Для чего это нужно

- Пользователь может запускать проект локально через `.venv`, даже если глобальная Python-установка повреждена или конфликтует с console scripts.

### Почему это сделано именно так

- `.venv` изолирует entrypoints и зависимости, а `run-local.ps1` запускает CLI через `python -m prompt_evolve.cli`, обходя проблемную перезапись exe-файлов.

### Затронутые файлы

- `scripts/setup-local.ps1`
- `scripts/run-local.ps1`
- `scripts/setup-local.sh`
- `scripts/run-local.sh`
- `prompt_evolve/providers.py`
- `tests/unit/test_providers_llm.py`
- `README.md`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`
- Локальная проверка CLI через `python -m prompt_evolve.cli --help`.
- Локальный smoke-run через `.\scripts\run-local.ps1 run --task examples/task.md --provider mock ...`.

### Риски

- Скрипт setup требует доступный `python` в PATH на Windows или `python3` на Linux/macOS.

## 2026-05-21 — Commit: a95d736

### Что изменено

- Заменены секретоподобные примеры ключей в requirement-документах на нейтральные placeholders.

### Для чего это нужно

- Репозиторий должен проходить базовый secret-scan без ложных срабатываний на примеры формата ключей.

### Почему это сделано именно так

- Изменены только демонстрационные значения, требования по переменным окружения сохранены.

### Затронутые файлы

- `FRD_Functional_Requirements_Document.txt`
- `Prompt_Evolution_CLI_All_Documents.txt`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- Secret-scan через `git grep` по ключевым паттернам.

### Риски

- Нет функционального риска: это документационная санитарная правка.

## 2026-05-21 — Commit: 4a0add1

### Что изменено

- Добавлена Docker-обвязка: `Dockerfile`, `.dockerignore`, `docker-compose.yml`.
- Добавлены init-скрипты `scripts/init-env.ps1` и `scripts/init-env.sh` для создания `.env` и `prompt-evolve.yaml`.
- Добавлена поддержка `GIGACHAT_BASE_URL` из окружения как fallback для GigaChat provider.
- Расширена документация по Docker, реальным запускам и инициализации секретов.

### Для чего это нужно

- Пользователь может вставить секреты в локальный `.env`, запустить init-скрипт и затем тестировать реальные промпты локально или через Docker.

### Почему это сделано именно так

- Секреты остаются вне git, Docker использует `env_file`, а CLI сохраняет прежнюю простую архитектуру provider interface.

### Затронутые файлы

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`
- `scripts/init-env.ps1`
- `scripts/init-env.sh`
- `.env.example`
- `prompt_evolve/providers.py`
- `README.md`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing --cov-report=html`
- Docker build/smoke проверяется отдельным запуском.

### Риски

- Реальные провайдеры требуют валидных ключей и корректного GigaChat endpoint.

## 2026-05-21 — Commit: 8b6d76f

### Что изменено

- Расширен README: установка, OpenRouter, GigaChat, команды, форматы файлов, метрики, SCOPE, тестирование и troubleshooting.
- Закреплён диапазон `pytest-cov` для более стабильной установки dev-зависимостей.

### Для чего это нужно

- README теперь позволяет новому разработчику запустить и проверить CLI без дополнительных пояснений.

### Почему это сделано именно так

- Документация следует обязательной структуре из требований, а pin диапазона снижает риск конфликтов в Windows-окружении.

### Затронутые файлы

- `README.md`
- `pyproject.toml`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`

### Риски

- Гид по заливке остаётся placeholder до передачи отдельной инструкции пользователем.

## 2026-05-21 — Commit: e274338

### Что изменено

- Добавлены unit-тесты и integration-тесты для CLI, config, providers, testcases, prompts, evaluator, metrics, SCOPE, reports и pipeline.
- Покрыты mock OpenRouter/GigaChat сценарии, ошибки конфигурации, invalid JSON retry, edge cases CLI и отчёты.

### Для чего это нужно

- Тесты подтверждают ключевые требования FRD/SRS и защищают CLI от регрессий.

### Почему это сделано именно так

- Все LLM-вызовы в тестах замоканы через fake/mock provider и mock HTTP, без реальных запросов к OpenRouter или GigaChat.

### Затронутые файлы

- `tests/unit/*`
- `tests/integration/*`
- `CHANGELOG.md`

### Тесты

- `python -m pytest`
- `python -m pytest --cov=prompt_evolve --cov-report=term-missing`

### Риски

- Реальный e2e с провайдерами остаётся ручным и требует переменных окружения.

## 2026-05-21 — Commit: 3ffc9df

### Что изменено

- Добавлены core-модули CLI: конфигурация, провайдеры, LLM JSON retry, тесткейсы, промпты, evaluator, метрики, SCOPE, отчёты и pipeline.
- Реализованы OpenRouter adapter, GigaChat hook, mock provider и extension point для системных/модельных метрик.

### Для чего это нужно

- Это реализует основной SCOPE-пайплайн генерации, оценки, улучшения промптов и сохранения результатов.

### Почему это сделано именно так

- Логика разделена по простым модулям из SRS/FRD, а провайдеры подключаются через единый интерфейс без смешивания с CLI.

### Затронутые файлы

- `prompt_evolve/*.py`
- `CHANGELOG.md`

### Тесты

- Перед коммитом выполняются `python -m pytest` и `python -m pytest --cov=prompt_evolve --cov-report=term-missing`.

### Риски

- Реальные e2e-вызовы OpenRouter/GigaChat не запускались без предоставленных переменных окружения.

## 2026-05-21 — Commit: babefd0

### Что изменено

- Добавлен каркас Python-пакета Prompt Evolution CLI.
- Добавлены базовые файлы проекта, примеры, `.env.example`, `.gitignore`, README и placeholder гида по заливке.

### Для чего это нужно

- Создаёт безопасную основу для CLI-утилиты и дальнейших атомарных изменений.

### Почему это сделано именно так

- Структура следует требованиям BRD/SRS/FRD и сохраняет проект простой CLI-утилитой.

### Затронутые файлы

- `pyproject.toml`
- `.gitignore`
- `.env.example`
- `prompt_evolve/__init__.py`
- `examples/*`
- `runs/.gitkeep`
- `docs/deployment_guide.md`
- `README.md`
- `CHANGELOG.md`

### Тесты

- Тесты будут добавлены следующими этапами.

### Риски

- Каркас пока не содержит исполняемой CLI-логики.
