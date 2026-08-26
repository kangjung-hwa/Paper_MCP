from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.contracts import DataArtifact, ExecutionCondition
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.oracle.artifact_semantics import any_violation, compare_condition
from src.oracle.environment import initial_artifact, world_from_task

BASE_ARTIFACTS = ["platform_id", "mission_id", "area_id", "constraints", "image", "position", "destination", "threat", "weather", "terrain", "comm", "object_position"]


def merge_observed(cond: ExecutionCondition, artifact_name: str, task: TaskInstance, produced_by: str) -> ExecutionCondition:
    if produced_by not in {"T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08"}:
        return cond
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


def output_condition(tool_id: str, out_name: str, base: DataArtifact | None, registry: ToolRegistry, task: TaskInstance) -> ExecutionCondition:
    cond = registry.get(tool_id).outputs[out_name]
    if tool_id in {"T09", "T10", "T13", "T14", "T15", "T25", "T26"} and base:
        cond = ExecutionCondition(
            schema_type=cond.schema_type or base.condition.schema_type,
            semantic_type=cond.semantic_type or base.condition.semantic_type,
            unit=cond.unit or base.condition.unit,
            reference_frame=cond.reference_frame or base.condition.reference_frame,
            timestamp=cond.timestamp if cond.timestamp is not None else base.condition.timestamp,
            confidence=cond.confidence if cond.confidence is not None else base.condition.confidence,
            provenance=cond.provenance or base.condition.provenance,
        )
    return merge_observed(cond, out_name, task, tool_id)


def simulate_oracle(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> tuple[list[dict], dict[str, DataArtifact]]:
    world = world_from_task(task)
    artifacts = {k: initial_artifact(k, task) for k in BASE_ARTIFACTS}
    rows: list[dict] = []
    for node in workflow.nodes:
        spec = registry.get(node.tool_id)
        for inp, aid in node.inputs.items():
            actual = artifacts.get(aid, initial_artifact(aid, task))
            required = spec.oracle_inputs.get(inp, ExecutionCondition())
            deficits = compare_condition(actual.condition, required, world.current_time)
            rows.append({
                "node_id": node.node_id,
                "tool_id": node.tool_id,
                "input_name": inp,
                "artifact_id": aid,
                "deficits": deficits,
                "violated": any_violation(deficits),
            })
        base = artifacts.get(next(iter(node.inputs.values()), ""))
        for out_name, aid in node.outputs.items():
            artifacts[aid] = DataArtifact(aid, output_condition(node.tool_id, out_name, base, registry, task), {"produced_by": node.tool_id}, node.tool_id)
    return rows, artifacts
