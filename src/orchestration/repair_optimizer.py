from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.repair_candidates import RepairCandidate, apply_repair
from src.orchestration.risk import workflow_risk


def repair_cost(candidate: RepairCandidate, original_nodes: int, registry: ToolRegistry, betas: dict | None = None) -> dict:
    betas = betas or {"latency": 0.25, "tool_calls": 0.25, "agent_calls": 0.25, "workflow_modification": 0.25}
    latency = min(1.0, sum(registry.get(t).base_latency_ms for t in candidate.tools) / 1500.0)
    tool_calls = min(1.0, len(candidate.tools) / 3.0)
    agent_calls = min(1.0, sum(1 for t in candidate.tools if registry.get(t).is_agent) / 3.0)
    modification = min(1.0, len(candidate.tools) / max(1, original_nodes))
    total = betas["latency"] * latency + betas["tool_calls"] * tool_calls + betas["agent_calls"] * agent_calls + betas["workflow_modification"] * modification
    return {"latency": latency, "tool_calls": tool_calls, "agent_calls": agent_calls, "workflow_modification": modification, "total": total}


def optimize_repair(workflow: Workflow, task: TaskInstance, registry: ToolRegistry, candidates: list[RepairCandidate], lam: float, no_cost: bool = False, full_metadata: bool = True):
    best = None
    rows = []
    for c in candidates:
        repaired = apply_repair(workflow, c, registry)
        residual, _ = workflow_risk(repaired, task, registry, full_metadata=full_metadata)
        cost = repair_cost(c, len(workflow.nodes), registry)
        j = residual if no_cost else residual + lam * cost["total"]
        row = {"candidate": c.to_dict(), "residual_risk": residual, "cost": cost, "J": j}
        rows.append(row)
        if best is None or j < best["J"]:
            best = row | {"workflow": repaired, "candidate_obj": c}
    return best, rows
