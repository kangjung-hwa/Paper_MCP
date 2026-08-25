from src.mcp.registry import ToolRegistry
from src.orchestration.proposed import run_proposed
from src.tasks.gold_workflows import initial_workflow


ABLATIONS = {
    "A1_no_downstream": {"no_downstream": True},
    "A2_no_cost": {"no_cost": True},
    "A3_strict_repair": {"strict": True},
    "A4_no_deficit_magnitude": {"binary_deficit": True},
    "A5_full_proposed": {},
}


def run_ablation_task(task, theta, lam):
    registry = ToolRegistry()
    out = {}
    for name, kwargs in ABLATIONS.items():
        out[name] = run_proposed(initial_workflow(task.family), task, registry, theta, lam, **kwargs)
    return out
