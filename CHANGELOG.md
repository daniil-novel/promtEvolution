# ChangeLog

## 2026-05-21 — Commit: pending

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
