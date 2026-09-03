from __future__ import annotations

from typing import TYPE_CHECKING

from src.models.workflow import Workflow
from src.oracle.artifact_semantics import any_violation, compare_condition
from src.oracle.environment import rectangle_intersects_route, route_coverage, world_from_task
from src.oracle.operational_validity import operational_requirement

if TYPE_CHECKING:
    from src.mcp.registry import ToolRegistry
    from src.models.contracts import DataArtifact


ROUTE_PLANNERS = {"T19", "T20", "T21", "T22"}
FAILURE_CONSUMERS = {
    "terrain": [("T19", {"terrain"})],
    "threat": [
        ("T20", {"threat_map"}),
        ("T17", {"threat"}),
        ("T16", {"threat"}),
    ],
    "weather": [("T21", {"weather"}), ("T17", {"weather"})],
    "communication": [("T22", {"comm_assessment"}), ("T18", {"comm"})],
}
POSITION_FAILURES = {"coordinate", "unit", "freshness", "confidence", "provenance", "compound"}


def _impact_was_remediated(
    workflow: Workflow,
    task,
    artifacts: dict[str, "DataArtifact"] | None,
    registry: "ToolRegistry" | None,
    failure_cause: str,
) -> bool:
    """Return whether a repair removed one concrete outcome failure cause.

    Merely finding an inserted node is not evidence of recovery.  A repair must be
    on the lineage consumed by the most downstream consumer for ``failure_cause``,
    and the cause-relevant inputs of that consumer must be operationally usable.
    Inputs of unrelated analysis tools are intentionally outside this decision.

    Artifact states come from the independent oracle simulator.  This does not
    call the OEPVR evaluator or reuse the proposed method's validator result.
    """
    if artifacts is None or registry is None:
        return False

    producers = {
        artifact_id: node
        for node in workflow.nodes
        for artifact_id in node.outputs.values()
    }

    def has_inserted_ancestor(artifact_id: str) -> bool:
        seen: set[str] = set()
        pending = [artifact_id]
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            producer = producers.get(current)
            if producer is None:
                continue
            if producer.inserted:
                return True
            pending.extend(producer.inputs.values())
        return False

    critical_nodes = []
    relevant_inputs: set[str] = set()
    for tool_id, input_names in FAILURE_CONSUMERS[failure_cause]:
        critical_nodes = [node for node in workflow.nodes if node.tool_id == tool_id]
        if critical_nodes:
            relevant_inputs = input_names
            break
    if not critical_nodes:
        return False

    world = world_from_task(task)
    roots: list[tuple[object, str, str]] = [
        (node, input_name, artifact_id)
        for node in critical_nodes
        for input_name, artifact_id in node.inputs.items()
        if input_name in relevant_inputs
    ]
    if task.violation_type in POSITION_FAILURES:
        roots.extend(
            (node, "start", node.inputs["start"])
            for node in workflow.nodes
            if node.tool_id in ROUTE_PLANNERS and "start" in node.inputs
        )

    def lineage_is_usable(node, input_name: str, artifact_id: str, seen: set[tuple[str, str]]) -> bool:
        key = (node.node_id, input_name)
        if key in seen:
            return True
        seen.add(key)
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            return False
        spec = registry.get(node.tool_id)
        strict = spec.oracle_inputs.get(input_name)
        if strict is not None:
            requirement = operational_requirement(strict).operational
            if any_violation(compare_condition(artifact.condition, requirement, world.current_time)):
                return False
        producer = producers.get(artifact_id)
        if producer is None or producer.inserted:
            return True
        return all(
            lineage_is_usable(producer, upstream_name, upstream_id, seen)
            for upstream_name, upstream_id in producer.inputs.items()
        )

    repaired_lineage_reached_outcome = any(
        has_inserted_ancestor(artifact_id) for _, _, artifact_id in roots
    )
    return bool(roots) and repaired_lineage_reached_outcome and all(
        lineage_is_usable(node, input_name, artifact_id, set())
        for node, input_name, artifact_id in roots
    )


def route_outcome(
    workflow: Workflow,
    task,
    artifacts: dict[str, "DataArtifact"] | None = None,
    registry: "ToolRegistry" | None = None,
) -> tuple[bool, str]:
    world = world_from_task(task)
    tools = [n.tool_id for n in workflow.nodes]
    if "T23" not in tools or not any(t in tools for t in ["T19", "T20", "T21", "T22"]):
        return False, "missing_route_or_validation"
    if task.oracle_world.get("valid_but_route_blocked") and task.severity == "critical":
        return False, "valid_plan_but_environment_blocks_route"
    threat_sensitive = task.family in {"F2", "F5", "F6"}
    weather_sensitive = task.family in {"F3", "F5", "F6"}
    comm_sensitive = task.family == "F4"
    terrain_sensitive = task.family == "F1"
    def unresolved(cause: str) -> bool:
        return world.outcome_impacted and not _impact_was_remediated(
            workflow, task, artifacts, registry, cause
        )

    if terrain_sensitive and any(rectangle_intersects_route(r) for r in world.terrain_obstacles_true) and unresolved("terrain"):
        return False, "route_intersects_terrain_obstacle"
    if threat_sensitive and any(rectangle_intersects_route(r) for r in world.threat_polygons_true) and unresolved("threat"):
        return False, "route_intersects_oracle_threat"
    if weather_sensitive and any(rectangle_intersects_route(r) for r in world.weather_hazards_true) and unresolved("weather"):
        return False, "route_intersects_oracle_weather_hazard"
    if comm_sensitive and route_coverage(world.communication_regions_true) < 0.85 and unresolved("communication"):
        return False, "communication_coverage_below_threshold"
    if task.family == "F6" and "T24" not in tools:
        return False, "missing_visualization"
    return True, "success"
