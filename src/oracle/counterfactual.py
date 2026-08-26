from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.oracle.success import gt_success
from src.oracle.validity import gt_valid
from src.orchestration.repair_candidates import RepairCandidate, apply_repair


def _remove_repair_node(workflow: Workflow, node_id: str) -> Workflow:
    reduced = workflow.clone()
    node = next((n for n in reduced.nodes if n.node_id == node_id), None)
    if node is None:
        return reduced
    in_artifact = next(iter(node.inputs.values()), None)
    out_artifact = next(iter(node.outputs.values()), None)
    reduced.nodes = [n for n in reduced.nodes if n.node_id != node_id]
    if in_artifact and out_artifact:
        for n in reduced.nodes:
            for key, value in list(n.inputs.items()):
                if value == out_artifact:
                    n.inputs[key] = in_artifact
    return reduced


def unnecessary_repair_counts(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> dict[str, int]:
    ourr = 0
    vurr = 0
    with_success = gt_success(workflow, task, registry)
    for node in [n for n in workflow.nodes if n.inserted]:
        reduced = _remove_repair_node(workflow, node.node_id)
        if with_success and gt_success(reduced, task, registry):
            ourr += 1
        if gt_valid(reduced, task, registry):
            vurr += 1
    return {"OURR_count": ourr, "VURR_count": vurr}


def unnecessary_repairs(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> int:
    return unnecessary_repair_counts(workflow, task, registry)["VURR_count"]


def _candidate_workflow(original: Workflow, candidate_row, registry: ToolRegistry):
    if isinstance(candidate_row, dict) and "workflow" in candidate_row:
        return candidate_row["workflow"]
    cdata = candidate_row.get("candidate", candidate_row) if isinstance(candidate_row, dict) else None
    if not cdata:
        return None
    candidate = RepairCandidate(cdata["name"], cdata["tools"], cdata["target_artifact"], cdata["reason"])
    return apply_repair(original, candidate, registry)


def repair_required(original: Workflow, candidates: list, task: TaskInstance, registry: ToolRegistry) -> bool:
    if gt_success(original, task, registry):
        return False
    return any(gt_success(wf, task, registry) for wf in (_candidate_workflow(original, c, registry) for c in candidates) if wf is not None)
