from __future__ import annotations

from dataclasses import dataclass

from src.models.workflow import Workflow, WorkflowNode

# HyperAgent-inspired schema-aware baseline; not an exact reproduction of the
# original HyperAgent implementation. It uses only public input/output schema
# and semantic types, never unit/frame/freshness/confidence/provenance or risk.

INITIAL = {
    "platform_id": "str",
    "mission_id": "str",
    "area_id": "str",
    "constraints": "Constraints",
    "image": "image",
}


def _semantic(cond: dict) -> str | None:
    return cond.get("semantic_type") or cond.get("schema_type")


def _goal_for_query(query: str) -> str:
    if "상황" in query or "판단" in query or "제시" in query:
        return "Visualization"
    return "ValidationResult"


def _candidate_tools(registry, semantic: str):
    specs = registry.public_specs(full_metadata=False)
    out = []
    for s in specs:
        if any(_semantic(c) == semantic for c in s["outputs"].values()):
            out.append(s)
    def rank(x):
        self_dep = any(_semantic(c) == semantic for c in x["inputs"].values())
        category_penalty = 0 if x.get("category") == "information" else 1
        return (self_dep, category_penalty, len(x["inputs"]), x["base_latency_ms"], x["tool_id"])
    return sorted(out, key=rank)


def _choose_route_tool(query: str, candidates):
    if "통신" in query:
        pref = "T22"
    elif "기상" in query:
        pref = "T21"
    elif "위협" in query or "안전" in query:
        pref = "T20"
    else:
        pref = "T19"
    for c in candidates:
        if c["tool_id"] == pref:
            return c
    return candidates[0]


def plan(task, registry, planner_mode: str = "deterministic"):
    goal = _goal_for_query(task.query)
    nodes: list[WorkflowNode] = []
    available = dict(INITIAL)
    artifact_for = {v: k for k, v in available.items()}
    trace = []

    visiting = set()

    def ensure(semantic: str, role: str = "") -> str:
        key = (semantic, role)
        if key in visiting:
            fallback = role if role in available else artifact_for.get(semantic)
            if fallback:
                return fallback
            raise RuntimeError(f"schema search cycle for {semantic}/{role}")
        visiting.add(key)
        if role == "start" and "Position" in artifact_for:
            visiting.discard(key)
            return artifact_for["Position"]
        if role == "destination" and "destination" in artifact_for:
            visiting.discard(key)
            return artifact_for["destination"]
        if semantic in artifact_for and role != "destination":
            visiting.discard(key)
            return artifact_for[semantic]
        candidates = _candidate_tools(registry, semantic)
        if semantic == "Position" and role in {"start", "position"} and any(c["tool_id"] == "T01" for c in candidates):
            chosen = next(c for c in candidates if c["tool_id"] == "T01")
        elif semantic == "Position" and role == "destination" and any(c["tool_id"] == "T04" for c in candidates):
            chosen = next(c for c in candidates if c["tool_id"] == "T04")
        elif semantic == "Route":
            chosen = _choose_route_tool(task.query, candidates)
        elif semantic == "Situation" and any(c["tool_id"] == "T17" for c in candidates):
            chosen = next(c for c in candidates if c["tool_id"] == "T17")
        elif semantic == "ThreatMap" and any(c["tool_id"] == "T16" for c in candidates):
            chosen = next(c for c in candidates if c["tool_id"] == "T16")
        elif semantic == "CommAssessment" and any(c["tool_id"] == "T18" for c in candidates):
            chosen = next(c for c in candidates if c["tool_id"] == "T18")
        else:
            chosen = candidates[0]
        inputs = {}
        for inp, cond in chosen["inputs"].items():
            req = _semantic(cond)
            if inp in INITIAL:
                aid = inp
            elif req in INITIAL.values():
                aid = next(k for k, v in INITIAL.items() if v == req)
            elif inp == "destination":
                aid = ensure("Position", "destination")
            elif inp in {"start", "position"}:
                aid = ensure("Position", "start")
            else:
                aid = ensure(req or inp, inp)
            inputs[inp] = aid
        out_name, out_cond = next(iter(chosen["outputs"].items()))
        artifact = out_name if out_name not in available else f"{out_name}_{len(nodes)+1}"
        nodes.append(WorkflowNode(f"schema_{len(nodes)+1}", chosen["tool_id"], inputs, {out_name: artifact}))
        out_sem = _semantic(out_cond) or semantic
        available[artifact] = out_sem
        artifact_for[out_sem] = artifact
        artifact_for[out_name] = artifact
        if out_name == "destination":
            artifact_for["destination"] = artifact
        trace.append({"thought": f"Need {semantic}; selected lowest-cost public producer", "action": chosen["tool_id"], "observation": f"produced {artifact}"})
        visiting.discard(key)
        return artifact

    ensure(goal)
    return Workflow(nodes, goal="visualization" if goal == "Visualization" else "validation"), trace, trace
