from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskInstance:
    task_id: str
    family: str
    query: str
    initial_state: dict[str, Any]
    violation_type: str
    severity: str
    oracle_conditions: dict[str, Any]
    seed: int
    split: str = "test"
    oracle_world: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "TaskInstance":
        return TaskInstance(**d)
