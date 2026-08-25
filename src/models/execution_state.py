from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from .contracts import DataArtifact


@dataclass
class ExecutionState:
    artifacts: dict[str, DataArtifact] = field(default_factory=dict)
    simulated_latency_ms: float = 0.0
    tool_calls: int = 0
    agent_calls: int = 0
    llm_calls: int = 0
    started_at: float = field(default_factory=perf_counter)

    def wall_clock_latency_ms(self) -> float:
        return (perf_counter() - self.started_at) * 1000.0
