from __future__ import annotations

from dataclasses import dataclass

from src.mcp.registry import ToolRegistry
from src.models.contracts import ExecutionCondition
from src.models.task import TaskInstance
from src.models.workflow import Workflow, WorkflowNode
from src.oracle.environment import world_from_task
from src.oracle.simulator import simulate_oracle


@dataclass(frozen=True)
class OperationalRequirement:
    strict: ExecutionCondition
    operational: ExecutionCondition


def operational_requirement(strict: ExecutionCondition) -> OperationalRequirement:
    # Hard requirements remain unchanged: schema, semantic type, unit, and reference frame.
    # Tolerable requirements are based on simulator meaning, not experiment outcomes:
    # confidence has a 0.05 interpretation margin for usable sensor outputs, and
    # freshness allows 40% additional age when the world model can remain unchanged.
    op = ExecutionCondition(
        schema_type=strict.schema_type,
        semantic_type=strict.semantic_type,
        unit=strict.unit,
        reference_frame=strict.reference_frame,
        timestamp=strict.timestamp,
        max_age=(strict.max_age * 1.4) if strict.max_age is not None else None,
        confidence=strict.confidence,
        min_confidence=max(0.0, strict.min_confidence - 0.05) if strict.min_confidence is not None else None,
        provenance=strict.provenance,
    )
    return OperationalRequirement(strict=strict, operational=op)


def _deficits(actual: ExecutionCondition, required: ExecutionCondition, now: float) -> dict[str, float]:
    out: dict[str, float] = {}
    for field in ["schema_type", "semantic_type", "unit", "reference_frame", "provenance"]:
        req = getattr(required, field)
        if req is not None:
            out[field] = 0.0 if getattr(actual, field) == req else 1.0
    if required.max_age is not None:
        age = now - actual.timestamp if actual.timestamp is not None else required.max_age + 1
        out["freshness"] = min(1.0, max(0.0, (age - required.max_age) / required.max_age))
    if required.min_confidence is not None:
        conf = actual.confidence if actual.confidence is not None else 0.0
        out["confidence"] = min(1.0, max(0.0, (required.min_confidence - conf) / required.min_confidence))
    return out


def evaluate_operational_validity(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> dict:
    world = world_from_task(task)
    strict_rows, artifacts = simulate_oracle(workflow, task, registry)
    artifact_map = artifacts
    op_rows = []
    complete = workflow.goal in artifacts
    for node in workflow.nodes:
        spec = registry.get(node.tool_id)
        for inp, aid in node.inputs.items():
            actual = artifact_map.get(aid)
            strict = spec.oracle_inputs.get(inp, ExecutionCondition())
            op_req = operational_requirement(strict).operational
            if actual is None:
                deficits = {"missing_input": 1.0}
            else:
                deficits = _deficits(actual.condition, op_req, world.current_time)
            op_rows.append({
                "node_id": node.node_id,
                "tool_id": node.tool_id,
                "input_name": inp,
                "artifact_id": aid,
                "operational_deficits": deficits,
                "operationally_violated": any(v > 0 for v in deficits.values()),
            })
    strict_valid = complete and all(not r["violated"] for r in strict_rows)
    operational_valid = complete and all(not r["operationally_violated"] for r in op_rows)
    return {
        "GT_strict_valid": int(strict_valid),
        "GT_operational_valid": int(operational_valid),
        "operational_edges": op_rows,
        "strict_edges": strict_rows,
        "execution_complete": int(complete),
    }


def workflow_from_dict(data: dict) -> Workflow:
    return Workflow([WorkflowNode(**node) for node in data["nodes"]], data.get("goal", "validation"))
