from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class WorkflowNode:
    node_id: str
    tool_id: str
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    inserted: bool = False


@dataclass
class Workflow:
    nodes: list[WorkflowNode]
    goal: str = "goal"

    def to_dict(self) -> dict:
        return {"goal": self.goal, "nodes": [asdict(n) for n in self.nodes]}

    def clone(self) -> "Workflow":
        return Workflow([WorkflowNode(**asdict(n)) for n in self.nodes], self.goal)

    def next_id(self, prefix: str) -> str:
        return f"{prefix}_{len(self.nodes) + 1:03d}"
