from src.models.task import TaskInstance
from src.tasks.gold_workflows import initial_workflow


def plan(task: TaskInstance, registry):
    # ReAct-style loop is represented deterministically for fair repeated simulation:
    # one reasoning/planning call followed by tool-use workflow execution and retry-on-failure in the runner.
    return initial_workflow(task.family)
