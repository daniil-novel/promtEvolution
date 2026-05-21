"""Example Python scenario config for Prompt Evolution CLI.

Run:
    .\scripts\run-local.ps1 run --config examples/prompt_project.py
"""

PROMPT_EVOLVE = {
    "task": {
        "text": """
# Task

Improve a system prompt for an assistant that rewrites rough meeting notes into
a concise Markdown status update.

# Requirements

- Preserve facts.
- Remove repetitions.
- Keep action items visible.
- Use Markdown bullets.
- Do not add unsupported facts.
""",
    },
    "prompt": {
        "text": """
You are a careful writing assistant. Rewrite rough notes into a concise Markdown
status update. Preserve facts, remove repetition, and keep action items visible.
""",
    },
    "tests": {
        "cases": [
            {
                "id": "TC-001",
                "name": "Basic duplicated notes",
                "type": "happy_path",
                "priority": "high",
                "input": "We shipped auth fix today. Need Lena to check metrics tomorrow. Auth fix shipped.",
                "expected_behavior": "Produce concise Markdown, remove duplicated auth info, and keep Lena's action item.",
                "evaluation_criteria": [
                    "Preserves the auth fix fact",
                    "Removes duplicated content",
                    "Includes Lena's action item",
                    "Uses Markdown bullets",
                ],
            }
        ],
    },
    "settings": {
        "provider": "mock",
        "model": "mock",
        "target_tests": 4,
        "iterations": 1,
        "candidates": 2,
        "pass_k": 2,
        "reasoning": "max",
        "self_check": True,
        "user_tests_only": False,
        "output": {
            "dir": "runs/python-config-example",
            "save_markdown_report": True,
            "save_json_report": True,
            "save_final_prompt": True,
        },
    },
}
