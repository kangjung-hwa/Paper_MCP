from src.models.task import TaskInstance
from src.tasks.gold_workflows import initial_workflow


class DeterministicPlanner:
    def __init__(self, model_name: str = "deterministic-planner", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature

    def plan(self, task: TaskInstance, registry):
        return initial_workflow(task.family)
