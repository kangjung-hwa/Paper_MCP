from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.repair_candidates import candidates_for_workflow
from src.orchestration.repair_optimizer import optimize_repair
from src.orchestration.risk import workflow_risk


def run_proposed(workflow: Workflow, task: TaskInstance, registry: ToolRegistry, theta: float, lam: float, *, no_downstream=False, no_cost=False, binary_deficit=False, strict=False, full_metadata=True):
    risk, edges = workflow_risk(workflow, task, registry, binary=binary_deficit, no_downstream=no_downstream, full_metadata=full_metadata)
    decision = strict or risk > theta
    candidates = candidates_for_workflow(workflow, edges) if decision else []
    selected = None
    candidate_rows = []
    final = workflow
    residual = risk
    if candidates:
        selected, candidate_rows = optimize_repair(workflow, task, registry, candidates, lam, no_cost=no_cost, full_metadata=full_metadata)
        if selected:
            final = selected["workflow"]
            residual = selected["residual_risk"]
    return {
        "initial_risk": risk,
        "risk_edges": edges,
        "repair_decision": decision,
        "repair_candidates": candidate_rows,
        "selected_repair": selected["candidate"] if selected else None,
        "final_workflow": final,
        "residual_risk": residual,
    }
