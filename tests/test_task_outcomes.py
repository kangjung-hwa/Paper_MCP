from copy import deepcopy

from src.mcp.registry import ToolRegistry
from src.models.workflow import WorkflowNode
from src.orchestration.repair_candidates import RepairCandidate, apply_repair
from src.oracle.success import gt_success
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


REGISTRY = ToolRegistry()


def _task(violation_type: str, severity: str = "critical"):
    task = deepcopy(next(t for t in generate_tasks(42) if t.family == "F1"))
    task.severity = severity
    task.violation_type = violation_type if severity != "normal" else "none"
    task.initial_state["position"] = {
        "reference_frame": "WGS84" if violation_type in {"coordinate", "compound"} else "ENU",
        "unit": "meter",
        "age": 25 if violation_type in {"freshness", "compound"} else 1,
        "confidence": 0.55 if violation_type in {"confidence", "compound"} else 0.9,
        "provenance": "verified",
    }
    task.oracle_world.update(
        outcome_impacted=severity == "critical",
        failure_mode=task.violation_type,
        valid_but_route_blocked=False,
        terrain_obstacles_true=[[45.0, 45.0, 55.0, 55.0]] if severity == "critical" else [],
    )
    return task


def _repair(task, tools):
    return apply_repair(
        initial_workflow(task.family),
        RepairCandidate("test_repair", tools, "position", task.violation_type),
        REGISTRY,
    )


def test_matching_repair_normalizes_violation_and_restores_success():
    task = _task("coordinate")
    assert gt_success(_repair(task, ["T09"]), task, REGISTRY)


def test_unrelated_inserted_repair_does_not_restore_success():
    task = _task("coordinate")
    assert not gt_success(_repair(task, ["T10"]), task, REGISTRY)

    unrelated_artifact = apply_repair(
        initial_workflow(task.family),
        RepairCandidate("terrain_repair", ["T10"], "terrain", "unit"),
        REGISTRY,
    )
    assert not gt_success(unrelated_artifact, task, REGISTRY)


def test_missing_repair_does_not_restore_success():
    task = _task("freshness")
    assert not gt_success(initial_workflow(task.family), task, REGISTRY)


def test_partial_compound_repair_does_not_restore_success():
    task = _task("compound")
    assert not gt_success(_repair(task, ["T09"]), task, REGISTRY)


def test_unnecessary_repair_does_not_change_normal_scenario_success():
    task = _task("none", severity="normal")
    original = initial_workflow(task.family)
    repaired = original.clone()
    repaired.nodes.insert(
        0,
        WorkflowNode("unrelated", "T15", {"data": "threat"}, {"data": "unused"}, inserted=True),
    )
    assert gt_success(original, task, REGISTRY)
    assert gt_success(repaired, task, REGISTRY)
