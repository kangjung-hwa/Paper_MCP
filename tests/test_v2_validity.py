from pathlib import Path

from src.baselines import react, schema_aware
from src.mcp.registry import ToolRegistry
from src.oracle.counterfactual import unnecessary_repair_counts
from src.oracle.success import gt_success
from src.oracle.validity import gt_valid
from src.orchestration.proposed import run_proposed
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


def test_baseline_independence():
    registry = ToolRegistry()
    different = False
    for task in generate_tasks(42):
        rw, _, _ = react.plan(task, registry)
        sw, _, _ = schema_aware.plan(task, registry)
        if rw.to_dict() != sw.to_dict():
            different = True
            break
    assert different


def test_oracle_does_not_import_proposed_validator():
    for path in Path("src/oracle").glob("*.py"):
        text = path.read_text()
        assert "src.orchestration.validator" not in text
        assert "validate_workflow" not in text


def test_minor_validity_and_success_can_diverge():
    registry = ToolRegistry()
    found = False
    for task in generate_tasks(42):
        if task.severity != "minor":
            continue
        wf = initial_workflow(task.family, task.seed)
        if not gt_valid(wf, task, registry) and gt_success(wf, task, registry):
            found = True
            break
    assert found


def test_outcome_unnecessary_repairs_can_occur():
    registry = ToolRegistry()
    found = False
    for task in generate_tasks(42):
        wf = initial_workflow(task.family, task.seed)
        prop = run_proposed(wf, task, registry, theta=0.05, lam=0.25, strict=True)
        counts = unnecessary_repair_counts(prop["final_workflow"], task, registry)
        if counts["OURR_count"] > 0:
            found = True
            break
    assert found


def test_critical_repair_success_exists():
    registry = ToolRegistry()
    found = False
    for task in generate_tasks(42):
        if task.severity != "critical":
            continue
        wf = initial_workflow(task.family, task.seed)
        prop = run_proposed(wf, task, registry, theta=0.0, lam=0.0, strict=True)
        if not gt_success(wf, task, registry) and gt_success(prop["final_workflow"], task, registry):
            found = True
            break
    assert found
