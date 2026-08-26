from __future__ import annotations

from src.models.workflow import Workflow, WorkflowNode

INITIAL_ARTIFACTS = {"platform_id", "mission_id", "area_id", "constraints", "image"}


def _tool_inputs_satisfied(spec, artifacts):
    return all((req.get("schema_type") in artifacts or req.get("semantic_type") in artifacts or name in artifacts) for name, req in spec["inputs"].items())


def _bind_inputs(spec, semantic_to_artifact):
    inputs = {}
    for name, req in spec["inputs"].items():
        sem = req.get("semantic_type") or req.get("schema_type") or name
        if name in semantic_to_artifact:
            inputs[name] = semantic_to_artifact[name]
        elif name == "destination" and "destination" in semantic_to_artifact:
            inputs[name] = semantic_to_artifact["destination"]
        elif name == "start" and "Position" in semantic_to_artifact:
            inputs[name] = semantic_to_artifact["Position"]
        else:
            inputs[name] = semantic_to_artifact.get(sem, semantic_to_artifact.get(name, name))
    return inputs


def _desired_tools(query: str) -> list[str]:
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


def plan(task, registry, max_tool_calls: int = 20, planner_mode: str = "deterministic"):
    public = {s["tool_id"]: s for s in registry.public_specs(full_metadata=False)}
    wanted = _desired_tools(task.query)
    nodes: list[WorkflowNode] = []
    trace = []
    observations = []
    semantic_to_artifact = {"str": "platform_id", "Constraints": "constraints", "image": "image", "platform_id": "platform_id", "mission_id": "mission_id", "area_id": "area_id"}
    done = set()
    step = 0
    while step < max_tool_calls and len(done) < len(wanted):
        step += 1
        chosen = None
        for tid in wanted:
            if tid in done:
                continue
            spec = public[tid]
            available_sem = set(semantic_to_artifact) | INITIAL_ARTIFACTS
            if _tool_inputs_satisfied(spec, available_sem):
                chosen = tid
                break
        if chosen is None:
            missing = [tid for tid in wanted if tid not in done]
            trace.append({"thought": "No executable preferred action; stopping", "action": None, "observation": {"missing": missing}})
            break
        spec = public[chosen]
        inputs = _bind_inputs(spec, semantic_to_artifact)
        out_name, out_cond = next(iter(spec["outputs"].items()))
        artifact = out_name if out_name not in semantic_to_artifact.values() else f"{out_name}_{step}"
        nodes.append(WorkflowNode(f"react_{step}", chosen, inputs, {out_name: artifact}))
        out_sem = out_cond.get("semantic_type") or out_cond.get("schema_type") or out_name
        semantic_to_artifact[out_sem] = artifact
        semantic_to_artifact[out_name] = artifact
        if out_name == "destination":
            semantic_to_artifact["destination"] = artifact
        done.add(chosen)
        obs = {"produced": artifact, "semantic_type": out_sem}
        trace.append({"thought": f"Query requires {chosen}; execute when public inputs are available", "action": chosen, "observation": obs})
        observations.append(obs)
    goal = "visualization" if any(n.tool_id == "T24" for n in nodes) else "validation"
    return Workflow(nodes, goal=goal), trace, observations
