from src.models.task import TaskInstance
from src.tasks.gold_workflows import initial_workflow


def plan(task: TaskInstance, registry):
    return initial_workflow(task.family)
