from __future__ import annotations

import random
from pathlib import Path

from src.baselines import react, schema_aware
from src.baselines.strict_constraint import repair as strict_repair
from src.mcp.registry import ToolRegistry
from src.models.execution_state import ExecutionState
from src.models.task import TaskInstance
from src.oracle.counterfactual import repair_required as gt_repair_required, unnecessary_repairs
from src.oracle.oracle_rules import evaluate
from src.orchestration.proposed import run_proposed
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


def run_one(task: TaskInstance, method: str, registry: ToolRegistry, theta: float, lam: float, model_name: str, temperature: float, ablation_flags: dict | None = None):
    set_global_seed(task.seed)
    initial = initial_workflow(task.family)
    llm_calls = 1
    if method == "react":
        final = react.plan(task, registry)
        prop = {"initial_risk": 0.0, "repair_decision": False, "repair_candidates": [], "selected_repair": None, "residual_risk": 0.0}
    elif method == "schema_aware":
        final = schema_aware.plan(task, registry)
        prop = {"initial_risk": 0.0, "repair_decision": False, "repair_candidates": [], "selected_repair": None, "residual_risk": 0.0}
    elif method == "strict":
        prop = strict_repair(initial, task, registry, lam)
        final = prop["final_workflow"]
    else:
        prop = run_proposed(initial, task, registry, theta, lam, **(ablation_flags or {}))
        final = prop["final_workflow"]
    state = simulate_execution(final, registry, task.seed)
    state.llm_calls = llm_calls
    ev = evaluate(final, task, registry)
    required = gt_repair_required(initial, prop.get("repair_candidates", []), task, registry)
    inserted = [n for n in final.nodes if n.inserted]
    return {
        "experiment_id": "default",
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
        "unnecessary_repairs": unnecessary_repairs(final, task, registry),
        "residual_risk": prop["residual_risk"],
        "theta": theta,
        "lambda": lam,
        "model_name": model_name,
        "temperature": temperature,
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
    rows = [run_one(t, method, registry, float(config.get("theta", 0.3)), float(config.get("lambda", 0.25)), config.get("model_name", "deterministic-planner"), float(config.get("temperature", 0.0))) for t in tasks]
    write_jsonl(out_path, rows)
    return rows
