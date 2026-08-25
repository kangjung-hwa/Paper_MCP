from __future__ import annotations

from dataclasses import asdict, dataclass

from src.mcp.registry import ToolRegistry
from src.models.workflow import Workflow, WorkflowNode


@dataclass
class RepairCandidate:
    name: str
    tools: list[str]
    target_artifact: str
    reason: str

    def to_dict(self):
        return asdict(self)


def candidates_for_workflow(workflow: Workflow, risk_edges: list[dict], max_len: int = 3) -> list[RepairCandidate]:
    mapping = {
        "reference_frame": ["T09"],
        "unit": ["T10"],
        "freshness": ["T11", "T12"],
        "confidence": ["T14", "T13"],
        "provenance": ["T15"],
    }
    out = []
    seen = set()
    for edge in risk_edges:
        for deficit, val in edge["deficits"].items():
            if val <= 0:
                continue
            for t in mapping.get(deficit, []):
                key = (t, edge["artifact_id"])
                if key not in seen:
                    seen.add(key)
                    out.append(RepairCandidate(f"{t}_for_{edge['artifact_id']}", [t], edge["artifact_id"], deficit))
    # Compound candidates try up to three distinct repairs against the highest risk artifact.
    if len(out) >= 2:
        combo = out[:max_len]
        out.append(RepairCandidate("compound_" + "_".join(c.tools[0] for c in combo), [c.tools[0] for c in combo], combo[0].target_artifact, "compound"))
    return out


def apply_repair(workflow: Workflow, candidate: RepairCandidate, registry: ToolRegistry | None = None) -> Workflow:
    wf = workflow.clone()
    target = candidate.target_artifact
    current = target
    insert_at = 0
    for i, n in enumerate(wf.nodes):
        if target in n.outputs.values():
            insert_at = i + 1
        for k, v in list(n.inputs.items()):
            if v == target and i >= insert_at:
                n.inputs[k] = current
    new_nodes = []
    for tid in candidate.tools:
        out = f"{current}_{tid}_repaired"
        inp_name = "data"
        if tid == "T11":
            inp_name = "position"
        elif tid == "T12":
            inp_name = "threat"
        elif tid == "T13":
            inp_name = "primary"
        node_inputs = {inp_name: current}
        if tid == "T13":
            node_inputs["secondary"] = current
        output_name = next(iter(registry.get(tid).outputs)) if registry else ("data" if tid not in {"T11", "T12"} else inp_name)
        new_nodes.append(WorkflowNode(wf.next_id("repair"), tid, node_inputs, {output_name: out}, inserted=True))
        current = out
    for n in wf.nodes[insert_at:]:
        for k, v in list(n.inputs.items()):
            if v == target:
                n.inputs[k] = current
    wf.nodes[insert_at:insert_at] = new_nodes
    return wf
