from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.repair_candidates import RepairCandidate, apply_repair
from src.orchestration.risk import workflow_risk


def repair_cost(candidate: RepairCandidate, registry: ToolRegistry, beta_latency: float = 0.5, beta_calls: float = 0.5) -> dict:
    added_latency_ms = sum(registry.get(t).base_latency_ms for t in candidate.tools)
    added_calls = len(candidate.tools)
    normalized_latency = min(1.0, added_latency_ms / 1000.0)
    normalized_calls = min(1.0, added_calls / 3.0)
    total = beta_latency * normalized_latency + beta_calls * normalized_calls
    return {
        "added_latency_ms": added_latency_ms,
        "added_calls": added_calls,
        "normalized_latency": normalized_latency,
        "normalized_calls": normalized_calls,
        "total": total,
    }


def optimize_repair(
    workflow: Workflow,
    task: TaskInstance,
    registry: ToolRegistry,
    candidates: list[RepairCandidate],
    lam: float,
    no_cost: bool = False,
    full_metadata: bool = True,
    risk_mode: str = "max",
    structural_dependency: bool = False,
    epsilon: float = 0.0,
):
    before, _ = workflow_risk(workflow, task, registry, full_metadata=full_metadata, risk_mode=risk_mode, structural_dependency=structural_dependency)
    best = None
    rows = []
    for c in candidates:
        repaired = apply_repair(workflow, c, registry)
        residual, _ = workflow_risk(repaired, task, registry, full_metadata=full_metadata, risk_mode=risk_mode, structural_dependency=structural_dependency)
        reduction = before - residual
        cost = repair_cost(c, registry)
        if reduction < epsilon:
            row = {"candidate": c.to_dict(), "residual_risk": residual, "risk_reduction": reduction, "cost": cost, "J": None, "filtered": True}
            rows.append(row)
            continue
        j = residual if no_cost else residual + lam * cost["total"]
        row = {"candidate": c.to_dict(), "residual_risk": residual, "risk_reduction": reduction, "cost": cost, "J": j, "filtered": False}
        rows.append(row)
        if best is None or j < best["J"]:
            best = row | {"candidate_obj": c, "workflow": repaired}
    return best, rows
