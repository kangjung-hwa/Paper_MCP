from __future__ import annotations

from dataclasses import asdict

from src.baselines.direct_tool_planning import build_workflow
from src.models.workflow import WorkflowNode

DISPLAY_NAME = "MIRROR-inspired"

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


def _public_artifacts_until(workflow, registry, stop: int | None = None):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    available = dict(_INITIAL_ARTIFACTS)
    limit = len(workflow.nodes) if stop is None else stop
    for node in workflow.nodes[:limit]:
        spec = public[node.tool_id]
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = _semantic(cond)
            if semantic is None and node.inputs:
                semantic = available.get(next(iter(node.inputs.values())))
            available[aid] = semantic or out_name
    return available


def _reflect_trajectory(workflow, registry) -> list[dict]:
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    available = dict(_INITIAL_ARTIFACTS)
    issues: list[dict] = []
    seen_signature: set[tuple] = set()
    for idx, node in enumerate(workflow.nodes):
        spec = public[node.tool_id]
        signature = (node.tool_id, tuple(sorted(node.inputs.items())))
        if signature in seen_signature:
            issues.append({"kind": "duplicate_tool", "index": idx, "node_id": node.node_id})
        seen_signature.add(signature)
        for inp, aid in node.inputs.items():
            req = _semantic(spec["inputs"].get(inp, {}))
            actual = available.get(aid)
            if not _compatible(req, actual):
                issues.append({"kind": "missing_or_incompatible_input", "index": idx, "node_id": node.node_id, "input": inp, "artifact": aid, "required": req, "actual": actual})
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = _semantic(cond)
            if semantic is None and node.inputs:
                semantic = available.get(next(iter(node.inputs.values())))
            available[aid] = semantic or out_name
    if workflow.goal not in available:
        issues.append({"kind": "goal_missing", "index": len(workflow.nodes), "artifact": workflow.goal, "required": "goal"})
    return issues


def _choose_producer(required: str | None, query: str, registry, existing_tools: set[str]) -> str | None:
    candidates = list(_PRODUCERS.get(required or "", []))
    if not candidates:
        return None
    if required == "Route":
        if "통신" in query:
            candidates = ["T22", "T19", "T20", "T21"]
        elif "기상" in query and "위협" not in query:
            candidates = ["T21", "T19", "T20", "T22"]
        elif "위협" in query:
            candidates = ["T20", "T19", "T21", "T22"]
        else:
            candidates = ["T19", "T20", "T21", "T22"]
    for tid in candidates:
        if tid in registry.specs:
            return tid
    return None


def _bind_inputs_for_producer(tool_id: str, artifact_id: str, workflow, registry, insert_index: int) -> dict[str, str]:
    spec = registry.get(tool_id).public_spec(full_metadata=False)
    available = _public_artifacts_until(workflow, registry, insert_index)
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
        elif inp == "route":
            inputs[inp] = by_semantic.get("Route", "route")
        elif sem:
            inputs[inp] = by_semantic.get(sem, inp)
        else:
            inputs[inp] = inp
    return inputs


def _apply_pre_execution_corrections(workflow, task, registry, max_rounds: int = 6):
    workflow = workflow.clone()
    corrections = 0
    trace: list[dict] = []
    changed = False
    for _ in range(max_rounds):
        issues = _reflect_trajectory(workflow, registry)
        if not issues:
            break
        issue = issues[0]
        if issue["kind"] == "duplicate_tool":
            removed = workflow.nodes.pop(issue["index"])
            trace.append({"phase": "pre_correction", "action": "remove_duplicate_tool", "tool": removed.tool_id, "node_id": removed.node_id, "reason": issue})
            corrections += 1
            changed = True
            continue
        required = issue.get("required")
        producer = _choose_producer(required, task.query, registry, {n.tool_id for n in workflow.nodes})
        if producer is None:
            break
        insert_index = min(issue.get("index", len(workflow.nodes)), len(workflow.nodes))
        spec = registry.get(producer).public_spec(full_metadata=False)
        out_name, _ = next(iter(spec["outputs"].items()))
        artifact = issue.get("artifact", out_name)
        inputs = _bind_inputs_for_producer(producer, artifact, workflow, registry, insert_index)
        node = WorkflowNode(f"mirror_pre_fix_{corrections + 1}", producer, inputs, {out_name: artifact})
        workflow.nodes.insert(insert_index, node)
        trace.append({"phase": "pre_correction", "action": "insert_missing_dependency", "tool": producer, "node_id": node.node_id, "reason": issue})
        corrections += 1
        changed = True
    return workflow, trace, corrections, changed


def _apply_limited_post_execution_correction(workflow, task, registry):
    issues = _reflect_trajectory(workflow, registry)
    if not issues:
        return workflow, [], 0, False
    corrected, trace, corrections, changed = _apply_pre_execution_corrections(workflow, task, registry, max_rounds=1)
    for item in trace:
        item["phase"] = "post_correction"
    return corrected, trace, corrections, changed


def _base_latency(trace: list[dict], registry) -> float:
    return sum(registry.get(e["tool"]).base_latency_ms for e in trace if e.get("tool") in registry.specs)


def plan(task, registry, **kwargs):
    initial, direct_trace, observations = build_workflow(task, registry, prefix="mirror")
    pre_reflection = [{"phase": "pre_reflection", "action": "reflect_trajectory", "observation": "public trajectory review before execution"}]
    workflow, pre_fixes, pre_count, pre_changed = _apply_pre_execution_corrections(initial, task, registry)
    post_reflection = [{"phase": "post_reflection", "action": "review_public_execution_observation", "observation": "single limited post-execution review"}]
    workflow, post_fixes, post_count, post_changed = _apply_limited_post_execution_correction(workflow, task, registry)
    trace = direct_trace + pre_reflection + pre_fixes + post_reflection + post_fixes
    added_calls = len(workflow.nodes) - len(initial.nodes)
    metadata = {
        "initial_tool_calls": len(initial.nodes),
        "pre_reflection_count": 1,
        "pre_correction_count": pre_count,
        "post_reflection_count": 1,
        "post_correction_count": post_count,
        "pre_execution_reflection_count": 1,
        "pre_execution_correction_count": pre_count,
        "post_execution_reflection_count": 1,
        "post_execution_correction_count": post_count,
        "reflection_count": 2,
        "correction_count": pre_count + post_count,
        "post_execution_recovery_count": 1 if post_count else 0,
        "final_tool_calls": len(workflow.nodes),
        "added_tool_calls": max(0, added_calls),
        "added_calls": max(0, added_calls),
        "added_latency": _base_latency(pre_fixes + post_fixes, registry),
        "pre_execution_correction_latency": _base_latency(pre_fixes, registry),
        "post_execution_correction_latency": _base_latency(post_fixes, registry),
        "pre_execution_changed_workflow": bool(pre_changed),
        "post_execution_changed_workflow": bool(post_changed),
        "initial_workflow": initial.to_dict(),
    }
    return workflow, trace, observations, metadata
