from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionCondition:
    schema_type: str | None = None
    semantic_type: str | None = None
    unit: str | None = None
    reference_frame: str | None = None
    timestamp: float | None = None
    max_age: float | None = None
    confidence: float | None = None
    min_confidence: float | None = None
    provenance: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DataArtifact:
    id: str
    condition: ExecutionCondition
    value: dict[str, Any] = field(default_factory=dict)
    produced_by: str | None = None


@dataclass
class ToolSpec:
    tool_id: str
    name: str
    description: str
    inputs: dict[str, ExecutionCondition]
    outputs: dict[str, ExecutionCondition]
    oracle_inputs: dict[str, ExecutionCondition]
    category: str
    base_latency_ms: float
    jitter_ms: float = 0.0
    is_agent: bool = False

    def public_spec(self, full_metadata: bool = True) -> dict[str, Any]:
        reqs = self.oracle_inputs if full_metadata else self.inputs
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "inputs": {k: v.public_dict() for k, v in reqs.items()},
            "outputs": {k: v.public_dict() for k, v in self.outputs.items()},
            "category": self.category,
            "base_latency_ms": self.base_latency_ms,
            "is_agent": self.is_agent,
        }
