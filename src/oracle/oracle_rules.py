from src.oracle.success import gt_success
from src.oracle.validity import gt_valid


def evaluate(workflow, task, registry):
    return {"GT_valid": int(gt_valid(workflow, task, registry)), "GT_success": int(gt_success(workflow, task, registry))}
