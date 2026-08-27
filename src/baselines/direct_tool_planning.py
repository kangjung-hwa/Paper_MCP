from __future__ import annotations

from src.models.workflow import Workflow, WorkflowNode

DISPLAY_NAME = "Direct Tool-Planning"

INITIAL = {
    "platform_id": "platform_id",
    "mission_id": "mission_id",
    "area_id": "area_id",
    "constraints": "constraints",
    "image": "image",
}


def _semantic(cond: dict) -> str | None:
    return cond.get("semantic_type") or cond.get("schema_type")


def _query_plan(query: str) -> list[str]:
    base = ["T01", "T04"]
    if "통신" in query:
        return base + ["T08", "T18", "T22", "T23"]
    if "기상" in query and "위협" not in query:
        return base + ["T05", "T21", "T23"]
    if "위협" in query and "기상" not in query:
        return base + ["T07", "T16", "T20", "T23"]
    if "상황" in query or "판단" in query:
        return base + ["T07", "T05", "T17", "T19", "T23", "T24"]
    if "위협" in query and "기상" in query:
        return base + ["T07", "T05", "T17", "T20", "T23"]
    return base + ["T06", "T19", "T23"]


def _bind_inputs(spec: dict, artifacts_by_name: dict[str, str], artifacts_by_semantic: dict[str, str]) -> dict[str, str]:
    bound = {}
    for name, cond in spec["inputs"].items():
        sem = _semantic(cond) or name
        if name in artifacts_by_name:
            bound[name] = artifacts_by_name[name]
        elif name == "start":
            bound[name] = artifacts_by_semantic.get("Position", "position")
        elif name == "destination":
            bound[name] = artifacts_by_name.get("destination", artifacts_by_semantic.get("Position", "destination"))
        elif name == "position":
            bound[name] = artifacts_by_semantic.get("Position", "position")
        elif name == "terrain":
            bound[name] = artifacts_by_semantic.get("TerrainMap", "terrain")
        elif name == "threat":
            bound[name] = artifacts_by_semantic.get("ThreatInfo", "threat")
        elif name == "weather":
            bound[name] = artifacts_by_semantic.get("Weather", "weather")
        elif name == "comm":
            bound[name] = artifacts_by_semantic.get("CommStatus", "comm")
        elif name == "threat_map":
            bound[name] = artifacts_by_semantic.get("ThreatMap", "threat_map")
        elif name == "comm_assessment":
            bound[name] = artifacts_by_semantic.get("CommAssessment", "comm_assessment")
        elif name == "route":
            bound[name] = artifacts_by_semantic.get("Route", "route")
        elif name == "situation":
            bound[name] = artifacts_by_semantic.get("Situation", "situation")
        else:
            bound[name] = artifacts_by_semantic.get(sem, artifacts_by_name.get(name, name))
    return bound


def build_workflow(task, registry, tool_ids: list[str] | None = None, prefix: str = "direct"):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    artifacts_by_name = dict(INITIAL)
    artifacts_by_semantic = {"str": "platform_id", "Constraints": "constraints", "image": "image"}
    nodes: list[WorkflowNode] = []
    trace = []
    for tid in tool_ids or _query_plan(task.query):
        spec = public[tid]
        inputs = _bind_inputs(spec, artifacts_by_name, artifacts_by_semantic)
        out_name, out_cond = next(iter(spec["outputs"].items()))
        artifact = out_name if out_name not in artifacts_by_name.values() else f"{out_name}_{len(nodes)+1}"
        nodes.append(WorkflowNode(f"{prefix}_{len(nodes)+1}", tid, inputs, {out_name: artifact}))
        out_sem = _semantic(out_cond) or out_name
        artifacts_by_name[out_name] = artifact
        artifacts_by_semantic[out_sem] = artifact
        if out_name == "destination":
            artifacts_by_name["destination"] = artifact
        trace.append({"phase": "plan", "action": tid, "observation": f"planned {tid} -> {artifact}"})
    goal = "visualization" if any(n.tool_id == "T24" for n in nodes) else "validation"
    return Workflow(nodes, goal), trace, []


def plan(task, registry, **kwargs):
    return build_workflow(task, registry, prefix="direct")
