from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.dependency import branching_factor, dependency_impact, downstream_depth
from src.orchestration.validator import validate_workflow


def _structural_multiplier(workflow: Workflow, registry: ToolRegistry, node_id: str) -> float:
    depth = downstream_depth(workflow, node_id)
    branch = branching_factor(workflow, node_id)
    path = 1.0 if dependency_impact(workflow, registry, node_id) > 0 else 0.0
    if not path:
        return 0.0
    # Objective structural information only: descendant depth and direct fan-out.
    return min(1.0, (depth + branch + path) / 6.0)


def workflow_risk(
    workflow: Workflow,
    task: TaskInstance,
    registry: ToolRegistry,
    binary: bool = False,
    full_metadata: bool = True,
    risk_mode: str = "max",
    structural_dependency: bool = False,
) -> tuple[float, list[dict]]:
    validations, _ = validate_workflow(workflow, task, registry, full_metadata=full_metadata, binary=binary)
    rows = []
    scores = []
    for v in validations:
        multiplier = _structural_multiplier(workflow, registry, v.node_id) if structural_dependency else 1.0
        risk = max(0.0, min(1.0, v.violation_score * multiplier))
        scores.append(risk)
        rows.append({
            "node_id": v.node_id,
            "tool_id": v.tool_id,
            "input_name": v.input_name,
            "artifact_id": v.artifact_id,
            "deficits": v.deficits,
            "violation_score": v.violation_score,
            "structural_multiplier": multiplier,
            "downstream_impact": multiplier,
            "risk_score": risk,
        })
    if not scores:
        return 0.0, rows
    if risk_mode == "mean":
        total = sum(scores) / len(scores)
    elif risk_mode == "sum_normalized":
        total = min(1.0, sum(scores) / max(1, len(scores)))
    else:
        total = max(scores)
    return max(0.0, min(1.0, total)), rows
