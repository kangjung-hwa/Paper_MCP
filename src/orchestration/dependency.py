from __future__ import annotations

from src.mcp.registry import ToolRegistry
from src.models.workflow import Workflow


def dependency_impact(workflow: Workflow, registry: ToolRegistry, source_node_id: str) -> float:
    index = {n.node_id: i for i, n in enumerate(workflow.nodes)}
    src_i = index[source_node_id]
    out_ids = set(workflow.nodes[src_i].outputs.values())
    best = 0.0
    frontier = [(src_i, out_ids, 1.0)]
    while frontier:
        i, artifacts, impact = frontier.pop()
        if i == len(workflow.nodes) - 1:
            best = max(best, impact)
        for j in range(i + 1, len(workflow.nodes)):
            n = workflow.nodes[j]
            used = sum(1 for a in n.inputs.values() if a in artifacts)
            if used:
                req_count = max(1, len(registry.get(n.tool_id).oracle_inputs))
                new_impact = impact * min(1.0, used / req_count)
                frontier.append((j, artifacts | set(n.outputs.values()), new_impact))
    return best


def downstream_depth(workflow: Workflow, source_node_id: str) -> int:
    index = {n.node_id: i for i, n in enumerate(workflow.nodes)}
    src_i = index[source_node_id]
    artifacts = set(workflow.nodes[src_i].outputs.values())
    best = 0
    frontier = [(src_i, artifacts, 0)]
    while frontier:
        i, arts, depth = frontier.pop()
        best = max(best, depth)
        for j in range(i + 1, len(workflow.nodes)):
            n = workflow.nodes[j]
            if any(a in arts for a in n.inputs.values()):
                frontier.append((j, arts | set(n.outputs.values()), depth + 1))
    return best


def branching_factor(workflow: Workflow, source_node_id: str) -> int:
    idx = {n.node_id: i for i, n in enumerate(workflow.nodes)}[source_node_id]
    outs = set(workflow.nodes[idx].outputs.values())
    return sum(1 for n in workflow.nodes[idx + 1:] if any(a in outs for a in n.inputs.values()))
