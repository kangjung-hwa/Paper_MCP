from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.validator import validate_workflow


def gt_success(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> bool:
    vals, artifacts = validate_workflow(workflow, task, registry, full_metadata=True)
    if workflow.goal not in artifacts:
        return False
    deficits = [d for v in vals for d in v.deficits.values() if d > 0]
    if not deficits:
        return True
    if task.severity == "minor":
        return max(deficits) <= 0.25 and task.oracle_conditions.get("minor_success_tolerated", False)
    return False
