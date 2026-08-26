from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.dependency import dependency_impact
from src.orchestration.validator import validate_workflow


def workflow_risk(workflow: Workflow, task: TaskInstance, registry: ToolRegistry, binary: bool = False, no_downstream: bool = False, full_metadata: bool = True) -> tuple[float, list[dict]]:
    validations, _ = validate_workflow(workflow, task, registry, full_metadata=full_metadata, binary=binary)
    rows = []
    max_r = 0.0
    for v in validations:
        impact = 1.0 if no_downstream else dependency_impact(workflow, registry, v.node_id)
        risk = v.violation_score * impact
        max_r = max(max_r, risk)
        rows.append({
            "node_id": v.node_id,
            "tool_id": v.tool_id,
            "input_name": v.input_name,
            "artifact_id": v.artifact_id,
            "deficits": v.deficits,
            "violation_score": v.violation_score,
            "downstream_impact": impact,
            "risk_score": risk,
        })
    return max_r, rows
