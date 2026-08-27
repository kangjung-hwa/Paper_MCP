from __future__ import annotations

from src.baselines.direct_tool_planning import build_workflow
from src.models.workflow import WorkflowNode

DISPLAY_NAME = "MIRROR-inspired"

PRODUCER_BY_SEMANTIC = {
    "Position": "T01",
    "ThreatInfo": "T07",
    "Weather": "T05",
    "TerrainMap": "T06",
    "CommStatus": "T08",
    "ThreatMap": "T16",
    "Situation": "T17",
    "CommAssessment": "T18",
    "Route": "T19",
    "ValidationResult": "T23",
    "Visualization": "T24",
}


def _semantic(cond: dict) -> str | None:
    return cond.get("semantic_type") or cond.get("schema_type")


def _public_artifacts(workflow, registry):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    available = {"platform_id": "str", "mission_id": "str", "area_id": "str", "constraints": "Constraints", "image": "image"}
    errors = []
    for idx, node in enumerate(workflow.nodes):
        spec = public[node.tool_id]
        for inp, aid in node.inputs.items():
            req = _semantic(spec["inputs"].get(inp, {}))
            actual = available.get(aid)
            if actual is None or (req and req != actual and not (req == "SpatialData" and actual in {"Position", "ThreatInfo", "TerrainMap", "ObjectPosition"})):
                errors.append({"index": idx, "node_id": node.node_id, "input": inp, "artifact": aid, "required": req, "actual": actual})
        for out_name, aid in node.outputs.items():
            available[aid] = _semantic(spec["outputs"][out_name]) or out_name
    return available, errors


def _insert_missing_producers(workflow, registry):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    corrections = 0
    trace = []
    while True:
        _, errors = _public_artifacts(workflow, registry)
        if not errors:
            break
        err = errors[0]
        producer = PRODUCER_BY_SEMANTIC.get(err["required"])
        if not producer:
            break
        spec = public[producer]
        inputs = {}
        for inp, cond in spec["inputs"].items():
            sem = _semantic(cond)
            if inp in {"platform_id", "mission_id", "area_id", "constraints", "image"}:
                inputs[inp] = inp
            elif sem == "Position":
                inputs[inp] = "position"
            elif sem == "ThreatInfo":
                inputs[inp] = "threat"
            elif sem == "Weather":
                inputs[inp] = "weather"
            elif sem == "Route":
                inputs[inp] = "route"
            else:
                inputs[inp] = inp
        out_name, _ = next(iter(spec["outputs"].items()))
        artifact = err["artifact"]
        node = WorkflowNode(f"mirror_fix_{corrections+1}", producer, inputs, {out_name: artifact})
        workflow.nodes.insert(err["index"], node)
        corrections += 1
        trace.append({"phase": "intra_reflection", "action": "insert_producer", "tool": producer, "reason": err})
        if corrections > 4:
            break
    return workflow, trace, corrections


def plan(task, registry, **kwargs):
    workflow, trace, observations = build_workflow(task, registry, prefix="mirror")
    pre_trace = [{"phase": "intra_reflection", "action": "check_public_schema", "observation": "review planned trajectory before execution"}]
    workflow, fixes, corrections = _insert_missing_producers(workflow, registry)
    post_trace = [{"phase": "inter_reflection", "action": "review_observations", "observation": "no public execution error after correction" if corrections else "no public schema correction needed"}]
    metadata = {
        "reflection_count": 2 + len(fixes),
        "pre_execution_reflection_count": 1 + len(fixes),
        "post_execution_reflection_count": 1,
        "correction_count": corrections,
        "post_execution_recovery_count": 0,
    }
    return workflow, pre_trace + trace + fixes + post_trace, observations, metadata
