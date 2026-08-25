from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow
from src.orchestration.proposed import run_proposed


def repair(workflow: Workflow, task: TaskInstance, registry: ToolRegistry, lam: float = 0.25):
    return run_proposed(workflow, task, registry, theta=0.0, lam=lam, strict=True)
