from __future__ import annotations

from src.baselines.direct_tool_planning import build_workflow
from src.models.workflow import WorkflowNode

DISPLAY_NAME = "Tool-MVR-inspired"

_INITIAL_ARTIFACTS = {
    "platform_id": "str",
    "mission_id": "str",
    "area_id": "str",
    "constraints": "Constraints",
    "image": "image",
}

_PRODUCERS = {
    "Position": ["T01", "T04", "T03"],
    "ThreatInfo": ["T07"],
    "Weather": ["T05"],
    "TerrainMap": ["T06"],
    "CommStatus": ["T08"],
    "ThreatMap": ["T16"],
    "Situation": ["T17"],
    "CommAssessment": ["T18"],
    "Route": ["T19", "T20", "T21", "T22"],
    "ValidationResult": ["T23"],
    "Visualization": ["T24"],
}


def _semantic(cond: dict) -> str | None:
    return cond.get("semantic_type") or cond.get("schema_type")


def _compatible(required: str | None, actual: str | None) -> bool:
    if required is None:
        return True
    if actual is None:
        return False
    return required == actual or (required == "SpatialData" and actual in {"Position", "ThreatInfo", "TerrainMap", "ObjectPosition"})


def _public_execute_until_error(workflow, registry, start_index: int = 0):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    available = dict(_INITIAL_ARTIFACTS)
    for node in workflow.nodes[:start_index]:
        spec = public[node.tool_id]
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = _semantic(cond)
            if semantic is None and node.inputs:
                semantic = available.get(next(iter(node.inputs.values())))
            available[aid] = semantic or out_name
    executed: list[str] = []
    for idx, node in enumerate(workflow.nodes[start_index:], start_index):
        spec = public[node.tool_id]
        executed.append(node.tool_id)
        for inp, aid in node.inputs.items():
            req = _semantic(spec["inputs"].get(inp, {}))
            actual = available.get(aid)
            if not _compatible(req, actual):
                return available, {"kind": "public_execution_error", "index": idx, "node_id": node.node_id, "input": inp, "artifact": aid, "required": req, "actual": actual}, executed
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = _semantic(cond)
            if semantic is None and node.inputs:
                semantic = available.get(next(iter(node.inputs.values())))
            available[aid] = semantic or out_name
    if workflow.goal not in available:
        return available, {"kind": "final_artifact_missing", "index": len(workflow.nodes), "artifact": workflow.goal, "required": "goal"}, executed
    return available, None, executed


def _choose_post_execution_producer(error: dict, task, registry) -> str | None:
    required = error.get("required")
    candidates = list(_PRODUCERS.get(required or "", []))
    if required == "Route":
        if "통신" in task.query:
            candidates = ["T22", "T19", "T20", "T21"]
        elif "기상" in task.query and "위협" not in task.query:
            candidates = ["T21", "T19", "T20", "T22"]
        elif "위협" in task.query:
            candidates = ["T20", "T19", "T21", "T22"]
        else:
            candidates = ["T19", "T20", "T21", "T22"]
    for tid in candidates:
        if tid in registry.specs:
            return tid
    return None


def _available_before(workflow, registry, index: int) -> dict[str, str]:
    partial = dict(_INITIAL_ARTIFACTS)
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    for node in workflow.nodes[:index]:
        spec = public[node.tool_id]
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = _semantic(cond)
            if semantic is None and node.inputs:
                semantic = partial.get(next(iter(node.inputs.values())))
            partial[aid] = semantic or out_name
    return partial


def _bind_inputs(tool_id: str, workflow, registry, index: int) -> dict[str, str]:
    spec = registry.get(tool_id).public_spec(full_metadata=False)
    available = _available_before(workflow, registry, index)
    by_semantic = {sem: aid for aid, sem in available.items()}
    inputs: dict[str, str] = {}
    for inp, cond in spec["inputs"].items():
        sem = _semantic(cond)
        if inp in _INITIAL_ARTIFACTS:
            inputs[inp] = inp
        elif inp == "position":
            inputs[inp] = by_semantic.get("Position", "position")
        elif inp == "threat":
            inputs[inp] = by_semantic.get("ThreatInfo", "threat")
        elif inp == "weather":
            inputs[inp] = by_semantic.get("Weather", "weather")
        elif inp == "comm":
            inputs[inp] = by_semantic.get("CommStatus", "comm")
        elif sem:
            inputs[inp] = by_semantic.get(sem, inp)
        else:
            inputs[inp] = inp
    return inputs


def _diagnose_execution_error(error: dict) -> dict:
    cause = "missing_goal_producer" if error["kind"] == "final_artifact_missing" else "missing_or_incompatible_runtime_artifact"
    return {"cause": cause, "required": error.get("required"), "error": error}


def _select_correction(diagnosis: dict, task, registry) -> str | None:
    return _choose_post_execution_producer(diagnosis["error"], task, registry)


def _apply_post_execution_correction(workflow, error: dict, tool_id: str, registry, correction_index: int):
    spec = registry.get(tool_id).public_spec(full_metadata=False)
    out_name, _ = next(iter(spec["outputs"].items()))
    artifact = error.get("artifact", out_name)
    inputs = _bind_inputs(tool_id, workflow, registry, correction_index)
    node = WorkflowNode(f"toolmvr_post_fix_{correction_index}_{tool_id}", tool_id, inputs, {out_name: artifact})
    corrected = workflow.clone()
    corrected.nodes.insert(correction_index, node)
    return corrected, node


def plan(task, registry, **kwargs):
    workflow, direct_trace, observations = build_workflow(task, registry, prefix="toolmvr")
    initial_workflow = workflow.clone()
    _, error, initial_executed = _public_execute_until_error(workflow, registry)
    trace = list(direct_trace)
    reflection_count = 0
    correction_count = 0
    retry_count = 0
    retry_sequences: list[list[str]] = []
    correction_tools: list[str] = []
    recovery_success = False
    rounds = 0
    while error and rounds < 2:
        rounds += 1
        trace.append({"phase": "execution_error", "observation": error})
        diagnosis = _diagnose_execution_error(error)
        trace.append({"phase": "post_reflection", "action": "diagnose_execution_error", "diagnosis": diagnosis})
        reflection_count += 1
        tool_id = _select_correction(diagnosis, task, registry)
        if tool_id is None:
            break
        retry_start = min(error.get("index", len(workflow.nodes)), len(workflow.nodes))
        workflow, node = _apply_post_execution_correction(workflow, error, tool_id, registry, retry_start)
        correction_count += 1
        correction_tools.append(tool_id)
        trace.append({"phase": "post_correction", "action": "insert_runtime_correction", "tool": tool_id, "node_id": node.node_id, "reason": error})
        _, error, retry_executed = _public_execute_until_error(workflow, registry, start_index=retry_start)
        retry_count += 1
        retry_sequences.append(retry_executed)
        if error is None:
            recovery_success = True
            break
    retry_tool_ids = [tid for seq in retry_sequences for tid in seq]
    final_tool_calls = len(initial_executed) + len(correction_tools) + len(retry_tool_ids)
    metadata = {
        "initial_execution_calls": len(initial_executed),
        "initial_executed_tool_ids": initial_executed,
        "execution_error_detected": bool(rounds),
        "reflection_count": reflection_count,
        "correction_count": correction_count,
        "correction_tool_ids": correction_tools,
        "retry_count": retry_count,
        "retry_tool_calls": len(retry_tool_ids),
        "retry_tool_ids": retry_tool_ids,
        "recovery_success": recovery_success,
        "final_tool_calls": final_tool_calls,
        "pre_execution_reflection_count": 0,
        "pre_execution_correction_count": 0,
        "post_execution_reflection_count": reflection_count,
        "post_execution_correction_count": correction_count,
        "post_execution_recovery_count": 1 if recovery_success else 0,
        "added_calls": len(correction_tools) + len(retry_tool_ids),
        "initial_workflow": initial_workflow.to_dict(),
    }
    return workflow, trace, observations, metadata
