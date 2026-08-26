from src.oracle.success import failure_reason, gt_success
from src.oracle.validity import gt_valid


def evaluate(workflow, task, registry):
    return {
        "GT_valid": int(gt_valid(workflow, task, registry)),
        "GT_success": int(gt_success(workflow, task, registry)),
        "oracle_actual_failure_reason": failure_reason(workflow, task, registry),
    }
