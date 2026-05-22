"""Trajectory and replay-buffer storage for prompt workbench runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import PromptRunResult


@dataclass(frozen=True)
class TrajectoryRecord:
    generation: int
    candidate_id: str
    prompt: str
    reward: float
    responses: dict[str, str]
    evaluations: list[dict[str, Any]]

    @classmethod
    def from_result(cls, *, generation: int, result: PromptRunResult, reward: float) -> "TrajectoryRecord":
        return cls(
            generation=generation,
            candidate_id=result.candidate.id,
            prompt=result.candidate.content,
            reward=reward,
            responses=dict(result.responses),
            evaluations=[item.to_dict() for item in result.evaluations],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation": self.generation,
            "candidate_id": self.candidate_id,
            "prompt": self.prompt,
            "reward": self.reward,
            "responses": dict(self.responses),
            "evaluations": list(self.evaluations),
        }


@dataclass
class ReplayBuffer:
    max_size: int = 100
    records: list[TrajectoryRecord] = field(default_factory=list)

    def add(self, record: TrajectoryRecord) -> None:
        self.records.append(record)
        self.records.sort(key=lambda item: item.reward)
        if len(self.records) > self.max_size:
            self.records = self.records[: self.max_size]

    def worst(self, limit: int = 5) -> list[TrajectoryRecord]:
        return self.records[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {"max_size": self.max_size, "records": [item.to_dict() for item in self.records]}

    def save(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return output
