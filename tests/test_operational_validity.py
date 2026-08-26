from pathlib import Path

from src.mcp.registry import ToolRegistry
from src.oracle.operational_validity import evaluate_operational_validity
from src.oracle.success import gt_success
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


def test_operational_validity_module_independent_from_validator():
    text = Path("src/oracle/operational_validity.py").read_text()
    assert "src.orchestration.validator" not in text
    assert "validate_workflow" not in text


def test_strict_and_operational_validity_can_differ():
    registry = ToolRegistry()
    found = False
    for task in generate_tasks(42):
        wf = initial_workflow(task.family, task.seed)
        op = evaluate_operational_validity(wf, task, registry)
        if op["GT_strict_valid"] == 0 and op["GT_operational_valid"] == 1:
            found = True
            break
    assert found


def test_operational_validity_not_identical_to_success_by_construction():
    registry = ToolRegistry()
    pairs = set()
    for task in generate_tasks(42):
        wf = initial_workflow(task.family, task.seed)
        op = evaluate_operational_validity(wf, task, registry)
        pairs.add((op["GT_operational_valid"], int(gt_success(wf, task, registry))))
    assert len(pairs) >= 2
    assert any(o != s for o, s in pairs)
