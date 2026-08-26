from pathlib import Path

from src.evaluation.runner import run_one
from src.mcp.registry import ToolRegistry
from src.orchestration.repair_candidates import candidates_for_workflow
from src.orchestration.repair_optimizer import optimize_repair, repair_cost
from src.orchestration.risk import workflow_risk
from src.orchestration.validator import validate_workflow
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


def test_v3_default_risk_equals_max_edge_violation_without_structural_multiplier():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.severity == "critical")
    wf = initial_workflow(task.family, task.seed)
    risk, edges = workflow_risk(wf, task, registry, risk_mode="max", structural_dependency=False)
    assert risk == max(e["violation_score"] for e in edges)
    assert all(e["structural_multiplier"] == 1.0 for e in edges)


def test_structural_dependency_is_separate_variant():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.severity == "critical")
    wf = initial_workflow(task.family, task.seed)
    base, _ = workflow_risk(wf, task, registry, structural_dependency=False)
    structural, _ = workflow_risk(wf, task, registry, structural_dependency=True)
    assert 0 <= structural <= 1
    assert 0 <= base <= 1


def test_repair_cost_uses_only_latency_and_calls():
    registry = ToolRegistry()
    cands = []
    wf = None
    for task in generate_tasks(42):
        if task.severity != "critical":
            continue
        wf = initial_workflow(task.family, task.seed)
        _, edges = workflow_risk(wf, task, registry)
        _, artifacts = validate_workflow(wf, task, registry)
        cands = candidates_for_workflow(wf, edges, artifacts)
        if cands:
            break
    assert wf is not None and cands
    cost = repair_cost(cands[0], registry)
    assert set(cost) == {"added_latency_ms", "added_calls", "normalized_latency", "normalized_calls", "total"}


def test_runner_records_cost_selection_fields():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.severity == "critical")
    row = run_one(task, "proposed", registry, theta=0.05, lam=0.25, model_name="deterministic", temperature=0.0)
    assert "risk_only_selected_repair" in row
    assert "cost_aware_selected_repair" in row
    assert "average_added_latency" in row
    assert "risk_reduction" in row


def test_v2_results_are_preserved_pathwise():
    assert Path("results/v2").exists()
