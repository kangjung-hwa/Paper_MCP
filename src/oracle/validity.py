from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.validator import validate_workflow


def gt_valid(workflow: Workflow, task: TaskInstance, registry: ToolRegistry) -> bool:
    vals, artifacts = validate_workflow(workflow, task, registry, full_metadata=True)
    return all(not any(v.deficits.values()) for v in vals) and workflow.goal in artifacts
