from copy import deepcopy

import pytest

from src.mcp.registry import ToolRegistry
from src.models.workflow import WorkflowNode
from src.orchestration.repair_candidates import RepairCandidate, apply_repair
from src.oracle.success import gt_success
from src.oracle.validity import gt_valid
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


REGISTRY = ToolRegistry()
NORMAL = {
    "position": {"reference_frame": "ENU", "unit": "meter", "age": 1, "confidence": 0.9, "provenance": "verified"},
    "threat": {"reference_frame": "ENU", "unit": "meter", "age": 2, "confidence": 0.82, "provenance": "verified"},
    "weather": {"age": 5, "confidence": 0.82, "provenance": "verified"},
    "comm": {"reference_frame": "ENU", "age": 2, "confidence": 0.84, "provenance": "verified"},
}


def _task(family: str, violation_type: str, patches=None, severity: str = "critical"):
    task = deepcopy(next(t for t in generate_tasks(42) if t.family == family))
    task.severity = severity
    task.violation_type = violation_type if severity != "normal" else "none"
    task.initial_state.update(deepcopy(NORMAL))
    for artifact, values in (patches or {}).items():
        task.initial_state[artifact].update(values)
    hazard = [[45.0, 45.0, 55.0, 55.0]] if severity == "critical" else []
    task.oracle_world.update(
        outcome_impacted=severity == "critical",
        failure_mode=task.violation_type,
        valid_but_route_blocked=False,
        terrain_obstacles_true=hazard if family == "F1" else [],
        threat_polygons_true=hazard if family in {"F2", "F5", "F6"} else [],
        weather_hazards_true=hazard if family == "F3" else [],
        communication_regions_true=[[0.0, 0.0, 40.0, 40.0]] if family == "F4" and hazard else [[0.0, 0.0, 100.0, 100.0]],
    )
    return task


def _repair(workflow, target, tool, reason="test"):
    return apply_repair(
        workflow,
        RepairCandidate(f"{tool}_for_{target}", [tool], target, reason),
        REGISTRY,
    )


def test_matching_position_repair_restores_f1_success():
    task = _task("F1", "coordinate", {"position": {"reference_frame": "WGS84"}})
    assert gt_success(_repair(initial_workflow("F1"), "position", "T09"), task, REGISTRY)


def test_arbitrary_inserted_nodes_do_not_restore_f1_success():
    task = _task("F1", "coordinate", {"position": {"reference_frame": "WGS84"}})
    assert not gt_success(initial_workflow("F1"), task, REGISTRY)
    assert not gt_success(_repair(initial_workflow("F1"), "position", "T10"), task, REGISTRY)
    assert not gt_success(_repair(initial_workflow("F1"), "terrain", "T10"), task, REGISTRY)


def test_partial_compound_position_repair_does_not_restore_success():
    task = _task("F1", "compound", {"position": {"reference_frame": "WGS84", "age": 25, "confidence": 0.55}})
    assert not gt_success(_repair(initial_workflow("F1"), "position", "T09"), task, REGISTRY)


def test_unnecessary_repair_does_not_change_normal_scenario_success():
    task = _task("F1", "none", severity="normal")
    original = initial_workflow("F1")
    repaired = original.clone()
    repaired.nodes.insert(0, WorkflowNode("unrelated", "T15", {"data": "threat"}, {"data": "unused"}, inserted=True))
    assert gt_success(original, task, REGISTRY)
    assert gt_success(repaired, task, REGISTRY)


@pytest.mark.parametrize(
    ("family", "artifact", "patch", "right_tool", "wrong_target", "wrong_tool"),
    [
        ("F2", "threat", {"age": 20}, "T12", "position", "T10"),
        ("F3", "weather", {"confidence": 0.65}, "T14", "position", "T10"),
        ("F4", "comm", {"reference_frame": "WGS84"}, "T09", "position", "T10"),
        ("F6", "threat", {"age": 20}, "T12", "position", "T10"),
    ],
)
def test_family_specific_repairs_restore_success_but_unrelated_repairs_do_not(
    family, artifact, patch, right_tool, wrong_target, wrong_tool
):
    task = _task(family, "family_input", {artifact: patch})
    original = initial_workflow(family)
    assert not gt_success(original, task, REGISTRY)
    assert gt_success(_repair(original, artifact, right_tool), task, REGISTRY)
    assert not gt_success(_repair(original, wrong_target, wrong_tool), task, REGISTRY)


def test_f5_compound_requires_all_failure_causes_to_be_repaired():
    task = _task("F5", "compound", {"position": {"reference_frame": "WGS84"}, "threat": {"age": 20}})
    partial = _repair(initial_workflow("F5", variant_index=2), "position", "T09")
    complete = _repair(partial, "threat", "T12")
    assert not gt_success(partial, task, REGISTRY)
    assert gt_success(complete, task, REGISTRY)


def test_f5_threat_map_repair_is_not_blocked_by_unrelated_t17_input_deficit():
    task = _task(
        "F5",
        "coordinate",
        {"weather": {"confidence": 0.1}},
    )
    workflow = initial_workflow("F5", variant_index=2)
    t16_index = next(i for i, node in enumerate(workflow.nodes) if node.tool_id == "T16")
    workflow.nodes.insert(
        t16_index,
        WorkflowNode(
            "unrelated_situation_analysis",
            "T17",
            {"position": "position", "threat": "threat", "weather": "weather"},
            {"situation": "unused_situation"},
        ),
    )
    repaired = _repair(workflow, "threat_map", "T26")

    t20 = next(node for node in repaired.nodes if node.tool_id == "T20")
    assert t20.inputs["threat_map"] == "threat_map_T26_repaired"
    assert not gt_valid(repaired, task, REGISTRY)  # T17 still sees the unrelated weather deficit.
    assert gt_success(repaired, task, REGISTRY)


@pytest.mark.parametrize("tolerated_patch", [{"confidence": 0.72}, {"age": 6}])
def test_tsr_allows_operational_margins_without_becoming_strict_conformance(tolerated_patch):
    task = _task(
        "F2",
        "coordinate",
        {"position": {"reference_frame": "WGS84"}, "threat": tolerated_patch},
    )
    repaired = _repair(initial_workflow("F2"), "position", "T09")
    assert not gt_valid(repaired, task, REGISTRY)
    assert gt_success(repaired, task, REGISTRY)
