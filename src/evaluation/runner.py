from __future__ import annotations

import random
from pathlib import Path

from src.baselines import react, schema_aware
from src.baselines.strict_constraint import repair as strict_repair
from src.mcp.registry import ToolRegistry
from src.models.execution_state import ExecutionState
from src.models.task import TaskInstance
from src.oracle.counterfactual import repair_required as gt_repair_required, unnecessary_repair_counts
from src.oracle.oracle_rules import evaluate
from src.oracle.success import gt_success
from src.orchestration.dependency import branching_factor, downstream_depth
from src.orchestration.proposed import run_proposed
from src.orchestration.repair_candidates import candidates_for_workflow
from src.orchestration.risk import workflow_risk
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow
from src.utils.serialization import read_jsonl, write_jsonl
from src.utils.seeds import set_global_seed


def simulate_execution(workflow, registry: ToolRegistry, seed: int):
    rng = random.Random(seed)
    state = ExecutionState()
    for node in workflow.nodes:
        spec = registry.get(node.tool_id)
        state.tool_calls += 1
        if spec.is_agent:
            state.agent_calls += 1
        state.simulated_latency_ms += spec.base_latency_ms + rng.random() * spec.jitter_ms
    return state


def _normalize_plan(plan_result):
    if isinstance(plan_result, tuple):
        wf, trace, observations = plan_result
        return wf, trace, observations
    return plan_result, [], []


def _annotate_edges(workflow, task, registry, edges):
    annotated = []
    for e in edges:
        row = dict(e)
        row["edge"] = f"{e['artifact_id']}->{e['tool_id']}.{e['input_name']}"
        row["deficit_vector"] = row.pop("deficits", {})
        row["risk"] = row.get("risk_score", 0.0)
        row["downstream_depth"] = downstream_depth(workflow, e["node_id"])
        row["branching_factor"] = branching_factor(workflow, e["node_id"])
        row["oracle_outcome_impact"] = bool(task.oracle_world.get("outcome_impacted", False) and row["risk"] > 0)
        annotated.append(row)
    return annotated


def run_one(task: TaskInstance, method: str, registry: ToolRegistry, theta: float, lam: float, model_name: str, temperature: float, ablation_flags: dict | None = None, planner_mode: str = "deterministic", max_tool_calls: int = 20, metadata_mode: str = "full"):
    set_global_seed(task.seed)
    initial = initial_workflow(task.family, task.seed)
    planner_trace = []
    tool_observations = []
    llm_calls = 1 if planner_mode == "llm" else 0
    base_risk, base_edges = workflow_risk(initial, task, registry)
    base_candidates = candidates_for_workflow(initial, base_edges)

    if method in {"react", "react_llm"}:
        final, planner_trace, tool_observations = _normalize_plan(react.plan(task, registry, max_tool_calls=max_tool_calls, planner_mode=planner_mode))
        prop = {"initial_risk": 0.0, "repair_decision": False, "repair_candidates": [], "selected_repair": None, "residual_risk": 0.0, "risk_edges": []}
    elif method in {"schema_aware", "schema_aware_llm"}:
        final, planner_trace, tool_observations = _normalize_plan(schema_aware.plan(task, registry, planner_mode=planner_mode))
        prop = {"initial_risk": 0.0, "repair_decision": False, "repair_candidates": [], "selected_repair": None, "residual_risk": 0.0, "risk_edges": []}
    elif method == "strict":
        prop = strict_repair(initial, task, registry, lam)
        final = prop["final_workflow"]
    else:
        prop = run_proposed(initial, task, registry, theta, lam, full_metadata=(metadata_mode == "full"), **(ablation_flags or {}))
        final = prop["final_workflow"]

    state = simulate_execution(final, registry, task.seed)
    state.llm_calls = llm_calls
    ev = evaluate(final, task, registry)
    original_success = gt_success(initial, task, registry)
    required = gt_repair_required(initial, [c.to_dict() for c in base_candidates], task, registry)
    inserted = [n for n in final.nodes if n.inserted]
    counts = unnecessary_repair_counts(final, task, registry)
    risk_edges = _annotate_edges(initial, task, registry, prop.get("risk_edges", base_edges))
    depth = max([e["downstream_depth"] for e in risk_edges if e["risk"] > 0] or [0])
    branch = max([e["branching_factor"] for e in risk_edges if e["risk"] > 0] or [0])
    return {
        "experiment_id": "v2",
        "task_id": task.task_id,
        "family": task.family,
        "severity": task.severity,
        "violation_type": task.violation_type,
        "method": method,
        "seed": task.seed,
        "initial_workflow": initial.to_dict(),
        "final_workflow": final.to_dict(),
        "GT_valid": ev["GT_valid"],
        "GT_success": ev["GT_success"],
        "GT_success_original": int(original_success),
        "GT_repair": int(required),
        "predicted_risk": prop["initial_risk"],
        "repair_decision": bool(prop["repair_decision"]),
        "repair_candidates": prop.get("repair_candidates", []),
        "selected_repair": prop.get("selected_repair"),
        "repair_required": bool(required),
        "repair_correct": bool(prop["repair_decision"]) == bool(required),
        "tool_calls": state.tool_calls,
        "agent_calls": state.agent_calls,
        "llm_calls": state.llm_calls,
        "simulated_latency_ms": state.simulated_latency_ms,
        "wall_clock_latency_ms": state.wall_clock_latency_ms(),
        "workflow_modification_ratio": len(inserted) / max(1, len(initial.nodes)),
        "outcome_unnecessary_repairs": counts["OURR_count"],
        "validity_unnecessary_repairs": counts["VURR_count"],
        "unnecessary_repairs": counts["VURR_count"],
        "residual_risk": prop["residual_risk"],
        "theta": theta,
        "lambda": lam,
        "model_name": model_name,
        "temperature": temperature,
        "planner_mode": planner_mode,
        "planner_trace": planner_trace,
        "tool_observations": tool_observations,
        "risk_edges": risk_edges,
        "violation_location": task.oracle_world.get("failure_mode", task.violation_type),
        "downstream_depth": depth,
        "branching_factor": branch,
        "oracle_actual_failure_reason": ev["oracle_actual_failure_reason"],
    }


def load_tasks(path: Path, seed: int) -> list[TaskInstance]:
    rows = read_jsonl(path)
    if not rows:
        return generate_tasks(seed)
    return [TaskInstance.from_dict(r) for r in rows]


def run_tasks(method: str, config: dict, task_path: Path, out_path: Path, split: str | None = None) -> list[dict]:
    registry = ToolRegistry()
    tasks = load_tasks(task_path, int(config.get("seed", 42)))
    if split:
        tasks = [t for t in tasks if t.split == split]
    planner_mode = config.get("planner_mode", "deterministic")
    rows = [run_one(t, method, registry, float(config.get("theta", 0.05)), float(config.get("lambda", 0.25)), config.get("model_name", "deterministic-planner"), float(config.get("temperature", 0.0)), planner_mode=planner_mode, max_tool_calls=int(config.get("max_tool_calls", 20)), metadata_mode=config.get("metadata_mode", "full")) for t in tasks]
    write_jsonl(out_path, rows)
    return rows
