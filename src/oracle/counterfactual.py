from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.oracle.success import gt_success
from src.oracle.validity import gt_valid
from src.orchestration.repair_candidates import RepairCandidate, apply_repair


def unnecessary_repairs(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> int:
    count = 0
    for node in [n for n in workflow.nodes if n.inserted]:
        reduced = workflow.clone()
        reduced.nodes = [n for n in reduced.nodes if n.node_id != node.node_id]
        if gt_valid(reduced, task, registry) and gt_success(reduced, task, registry):
            count += 1
    return count


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
