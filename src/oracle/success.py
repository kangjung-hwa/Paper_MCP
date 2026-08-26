from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.oracle.simulator import simulate_oracle
from src.oracle.task_outcomes import route_outcome


def gt_success(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> bool:
    rows, artifacts = simulate_oracle(workflow, task, registry)
    ok, _ = route_outcome(workflow, task)
    return ok and workflow.goal in artifacts


def failure_reason(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> str:
    _, artifacts = simulate_oracle(workflow, task, registry)
    if workflow.goal not in artifacts:
        return "goal_artifact_missing"
    _, reason = route_outcome(workflow, task)
    return reason
