"""MCP/tool policy extension point.

The project does not start external MCP servers by itself. This module keeps a
stable contract for future connectors and records which tools an optimized
prompt is allowed to rely on.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .models import TaskSpec, ToolPolicy


def infer_tool_policy(task_spec: TaskSpec, *, mcp_config: dict[str, Any] | None = None) -> ToolPolicy:
    servers = (mcp_config or {}).get("servers") or {}
    allowed = sorted(servers) if isinstance(servers, dict) else []
    notes = [
        "Не вызывай внешние инструменты, если задача решается по входному контексту.",
        "Не раскрывай секреты, ключи и содержимое переменных окружения.",
        "Фиксируй, какие данные были получены через инструменты, если это влияет на ответ.",
    ]
    if task_spec.tool_requirements:
        notes.extend(task_spec.tool_requirements)
    return ToolPolicy(
        allowed_tools=allowed,
        blocked_tools=["shell_destructive", "secret_exfiltration"],
        approval_required=["write_files", "network_side_effects", "production_changes"],
        production_notes=notes,
    )


def load_mcp_config(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    return data if isinstance(data, dict) else {}
