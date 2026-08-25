from __future__ import annotations

import random

from src.models.contracts import DataArtifact, ExecutionCondition, ToolSpec
from src.models.execution_state import ExecutionState


class BaseTool:
    spec: ToolSpec

    def __init__(self, spec: ToolSpec):
        self.spec = spec

    def execute(self, inputs: dict[str, DataArtifact], state: ExecutionState, rng: random.Random) -> dict[str, DataArtifact]:
        state.tool_calls += 1
        if self.spec.is_agent:
            state.agent_calls += 1
        state.simulated_latency_ms += self.spec.base_latency_ms + rng.random() * self.spec.jitter_ms
        outputs = {}
        for name, cond in self.spec.outputs.items():
            outputs[name] = DataArtifact(
                id=f"{self.spec.tool_id}.{name}.{state.tool_calls}",
                condition=cond,
                value={"source_inputs": list(inputs)},
                produced_by=self.spec.tool_id,
            )
        return outputs


def c(**kwargs) -> ExecutionCondition:
    return ExecutionCondition(**kwargs)
