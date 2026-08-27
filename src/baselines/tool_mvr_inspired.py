from __future__ import annotations

from src.baselines.direct_tool_planning import build_workflow
from src.baselines.mirror_inspired import _insert_missing_producers, _public_artifacts

DISPLAY_NAME = "Tool-MVR-inspired"


def plan(task, registry, **kwargs):
    workflow, trace, observations = build_workflow(task, registry, prefix="toolmvr")
    _, errors = _public_artifacts(workflow, registry)
    reflection = []
    corrections = 0
    recovery = 0
    if errors:
        reflection.append({"phase": "error", "observation": errors[0]})
        reflection.append({"phase": "reflection", "action": "diagnose_public_execution_error"})
        workflow, fixes, corrections = _insert_missing_producers(workflow, registry)
        reflection.extend(fixes)
        recovery = 1 if corrections else 0
        reflection.append({"phase": "correction", "action": "retry_corrected_workflow", "corrections": corrections})
    metadata = {
        "reflection_count": len(reflection),
        "pre_execution_reflection_count": 0,
        "post_execution_reflection_count": 1 if errors else 0,
        "correction_count": corrections,
        "post_execution_recovery_count": recovery,
    }
    return workflow, trace + reflection, observations, metadata
