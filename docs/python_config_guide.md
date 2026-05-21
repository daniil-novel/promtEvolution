# Python Config Guide

Python scenario configs let you keep a prompt-evolution run in one readable file.

## Minimal File

Create `my_prompt_project.py`:

```python
PROMPT_EVOLVE = {
    "task": {
        "text": """
# Task

Describe what the final prompt must do.
"""
    },
    "prompt": {
        "text": """
Paste your current prompt here. Remove this block if you want to generate from scratch.
"""
    },
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

Run:

```powershell
.\scripts\run-local.ps1 run --config my_prompt_project.py
```

The final prompt will be saved to `runs/my_prompt_project/final_prompt.md`.

## With Manual Tests

```python
PROMPT_EVOLVE = {
    "task": {"file": "my_prompts/task.md"},
    "prompt": {"file": "my_prompts/prompt.md"},
    "tests": {
        "cases": [
            {
                "id": "TC-001",
                "name": "Happy path",
                "type": "happy_path",
                "priority": "high",
                "input": "User input example",
                "expected_behavior": "Expected behavior",
                "evaluation_criteria": [
                    "Criterion one",
                    "Criterion two",
                ],
            }
        ]
    },
    "settings": {
        "provider": "openrouter",
        "model": "openai/gpt-4.1",
        "target_tests": 40,
        "iterations": 3,
        "candidates": 4,
        "pass_k": 4,
        "output": {"dir": "runs/my_prompt_project"},
    },
}
```

If `target_tests` is larger than the manual test count, the CLI generates missing tests unless `user_tests_only` is `True`.

## Common Commands

Generate or improve a prompt:

```powershell
.\scripts\run-local.ps1 run --config my_prompt_project.py
```

Generate tests only:

```powershell
.\scripts\run-local.ps1 generate-tests --config my_prompt_project.py --out my_prompts/tests.json
```

Evaluate a prompt only:

```powershell
.\scripts\run-local.ps1 evaluate --config my_prompt_project.py
```

Override settings from CLI:

```powershell
.\scripts\run-local.ps1 run --config my_prompt_project.py --iterations 1 --target-tests 5 --out runs/quick
```

CLI options always override values from the Python config.
