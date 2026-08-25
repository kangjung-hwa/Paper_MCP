from src.mcp.registry import ToolRegistry
from src.models.contracts import ExecutionCondition
from src.orchestration.deficit import condition_deficits, violation_score
from src.orchestration.dependency import dependency_impact
from src.orchestration.proposed import run_proposed
from src.orchestration.repair_candidates import candidates_for_workflow
from src.orchestration.repair_optimizer import optimize_repair
from src.orchestration.risk import workflow_risk
from src.oracle.counterfactual import unnecessary_repairs
from src.oracle.success import gt_success
from src.oracle.validity import gt_valid
from src.tasks.generator import generate_tasks
from src.tasks.gold_workflows import initial_workflow


def test_deficit_coordinate_freshness_confidence():
    actual = ExecutionCondition(semantic_type="Position", reference_frame="WGS84", timestamp=-12, confidence=0.6)
    req = ExecutionCondition(semantic_type="Position", reference_frame="ENU", max_age=6, min_confidence=0.8)
    d = condition_deficits(actual, req, now=0)
    assert d["reference_frame"] == 1
    assert d["freshness"] == 1
    assert round(d["confidence"], 2) == 0.25
    assert 0 <= violation_score(d) <= 1


def test_task_generation_reproducibility_and_distribution():
    a = generate_tasks(42)
    b = generate_tasks(42)
    assert [x.to_dict() for x in a] == [x.to_dict() for x in b]
    assert len(a) == 300
    for f in {t.family for t in a}:
        xs = [t for t in a if t.family == f]
        assert sum(t.severity == "normal" for t in xs) == 20
        assert sum(t.severity == "minor" for t in xs) == 15
        assert sum(t.severity == "critical" for t in xs) == 15


def test_dependency_weight_and_risk():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.family == "F2" and t.severity == "critical")
    wf = initial_workflow(task.family)
    assert 0 <= dependency_impact(wf, registry, wf.nodes[0].node_id) <= 1
    r, edges = workflow_risk(wf, task, registry)
    assert 0 <= r <= 1
    assert edges


def test_candidate_generation_and_optimization():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.violation_type in {"freshness", "confidence", "compound"} and t.severity == "critical")
    wf = initial_workflow(task.family)
    risk, edges = workflow_risk(wf, task, registry)
    cands = candidates_for_workflow(wf, edges)
    assert cands
    best, rows = optimize_repair(wf, task, registry, cands, 0.25)
    assert best is not None
    assert rows


def test_oracle_valid_success_and_counterfactual():
    registry = ToolRegistry()
    normal = next(t for t in generate_tasks(42) if t.severity == "normal")
    wf = initial_workflow(normal.family)
    assert gt_valid(wf, normal, registry)
    assert gt_success(wf, normal, registry)
    prop = run_proposed(wf, normal, registry, theta=0.3, lam=0.25)
    assert unnecessary_repairs(prop["final_workflow"], normal, registry) == 0


def test_proposed_repairs_critical():
    registry = ToolRegistry()
    task = next(t for t in generate_tasks(42) if t.severity == "critical" and t.violation_type == "freshness")
    wf = initial_workflow(task.family)
    assert not gt_success(wf, task, registry)
    prop = run_proposed(wf, task, registry, theta=0.05, lam=0.0)
    assert prop["repair_decision"]
