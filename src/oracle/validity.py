from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.oracle.artifact_semantics import any_violation
from src.oracle.simulator import simulate_oracle


def gt_valid(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> bool:
    rows, artifacts = simulate_oracle(workflow, task, registry)
    return all(not any_violation(r["deficits"]) for r in rows) and workflow.goal in artifacts
