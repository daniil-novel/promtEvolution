# ChangeLog

## 2026-05-21 — Commit: pending

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
