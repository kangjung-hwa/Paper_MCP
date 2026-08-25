from __future__ import annotations

from dataclasses import dataclass

from src.mcp.registry import ToolRegistry
from src.models.contracts import DataArtifact, ExecutionCondition
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.deficit import condition_deficits, violation_score


@dataclass
class EdgeValidation:
    node_id: str
    tool_id: str
    input_name: str
    artifact_id: str
    deficits: dict[str, float]
    violation_score: float


def artifact_from_task(name: str, task: TaskInstance) -> DataArtifact:
    attrs = task.initial_state.get(name, {})
    cond = ExecutionCondition(
        schema_type="Constraints" if name == "constraints" else "str" if name in {"platform_id", "mission_id", "area_id"} else None,
        semantic_type={"position": "Position", "destination": "Position", "threat": "ThreatInfo", "weather": "Weather", "terrain": "TerrainMap", "comm": "CommStatus"}.get(name),
        unit=attrs.get("unit"),
        reference_frame=attrs.get("reference_frame"),
        timestamp=-float(attrs.get("age", 0)),
        confidence=attrs.get("confidence"),
        provenance=attrs.get("provenance"),
    )
    return DataArtifact(name, cond, {}, produced_by="initial")


def _merge_task_observation(cond: ExecutionCondition, artifact_name: str, task: TaskInstance) -> ExecutionCondition:
    attrs = task.initial_state.get(artifact_name)
    if not attrs:
        return cond
    return ExecutionCondition(
        schema_type=cond.schema_type,
        semantic_type=cond.semantic_type,
        unit=attrs.get("unit", cond.unit),
        reference_frame=attrs.get("reference_frame", cond.reference_frame),
        timestamp=-float(attrs["age"]) if "age" in attrs else cond.timestamp,
        max_age=cond.max_age,
        confidence=attrs.get("confidence", cond.confidence),
        min_confidence=cond.min_confidence,
        provenance=attrs.get("provenance", cond.provenance),
    )


def validate_workflow(workflow: Workflow, task: TaskInstance, registry: ToolRegistry, full_metadata: bool = True, binary: bool = False) -> tuple[list[EdgeValidation], dict[str, DataArtifact]]:
    artifacts = {k: artifact_from_task(k, task) for k in ["platform_id", "mission_id", "area_id", "constraints", "position", "destination", "threat", "weather", "terrain", "comm"]}
    rows: list[EdgeValidation] = []
    for node in workflow.nodes:
        spec = registry.get(node.tool_id)
        reqs = spec.oracle_inputs if full_metadata else spec.inputs
        for inp, aid in node.inputs.items():
            req = reqs.get(inp, ExecutionCondition())
            actual = artifacts.get(aid, artifact_from_task(aid, task))
            deficits = condition_deficits(actual.condition, req, now=0.0, binary=binary)
            rows.append(EdgeValidation(node.node_id, node.tool_id, inp, aid, deficits, violation_score(deficits)))
        for out_name, aid in node.outputs.items():
            cond = spec.outputs[out_name]
            base = artifacts.get(next(iter(node.inputs.values()), ""), None)
            # Transform/repair tools preserve semantic type when their declared output omits it.
            if node.tool_id in {"T09", "T10", "T13", "T14", "T15"} and base:
                cond = ExecutionCondition(
                    schema_type=cond.schema_type or base.condition.schema_type,
                    semantic_type=cond.semantic_type or base.condition.semantic_type,
                    unit=cond.unit or base.condition.unit,
                    reference_frame=cond.reference_frame or base.condition.reference_frame,
                    timestamp=cond.timestamp if cond.timestamp is not None else base.condition.timestamp,
                    confidence=cond.confidence if cond.confidence is not None else base.condition.confidence,
                    provenance=cond.provenance or base.condition.provenance,
                )
            cond = _merge_task_observation(cond, aid, task)
            artifacts[aid] = DataArtifact(aid, cond, produced_by=node.tool_id)
    return rows, artifacts
