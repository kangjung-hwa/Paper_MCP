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
OUTCOME_CRITICAL_TOOLS = {
    "F1": {"T19"},
    "F2": {"T16", "T20"},
    "F3": {"T21"},
    "F4": {"T18", "T22"},
    "F5": {"T16", "T17", "T20"},
    "F6": {"T16", "T17", "T19", "T20", "T24"},
}


def _impact_was_remediated(
    workflow: Workflow,
    task,
    artifacts: dict[str, "DataArtifact"] | None,
    registry: "ToolRegistry" | None,
) -> bool:
    """Return whether a repair made outcome-critical inputs operationally usable.

    Merely finding an inserted node is not evidence of recovery.  A repair must be
    on a lineage consumed by a family-specific outcome-critical tool, and every
    such input must meet its operational requirement.  This deliberately permits
    the bounded confidence/freshness deviations used by the simulator while hard
    semantic, unit, frame, and provenance requirements remain mandatory.

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

    critical_nodes = [
        node for node in workflow.nodes
        if node.tool_id in OUTCOME_CRITICAL_TOOLS.get(task.family, ROUTE_PLANNERS)
    ]
    repaired_lineage_reached_outcome = any(
        has_inserted_ancestor(artifact_id)
        for node in critical_nodes
        for artifact_id in node.inputs.values()
    )
    if not repaired_lineage_reached_outcome or not critical_nodes:
        return False

    world = world_from_task(task)
    for node in critical_nodes:
        spec = registry.get(node.tool_id)
        for input_name, artifact_id in node.inputs.items():
            artifact = artifacts.get(artifact_id)
            if artifact is None:
                return False
            strict = spec.oracle_inputs.get(input_name)
            if strict is None:
                continue
            requirement = operational_requirement(strict).operational
            if any_violation(compare_condition(artifact.condition, requirement, world.current_time)):
                return False
    return True


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
    impacted = world.outcome_impacted and not _impact_was_remediated(
        workflow, task, artifacts, registry
    )
    if terrain_sensitive and any(rectangle_intersects_route(r) for r in world.terrain_obstacles_true) and impacted:
        return False, "route_intersects_terrain_obstacle"
    if threat_sensitive and any(rectangle_intersects_route(r) for r in world.threat_polygons_true) and impacted:
        return False, "route_intersects_oracle_threat"
    if weather_sensitive and any(rectangle_intersects_route(r) for r in world.weather_hazards_true) and impacted:
        return False, "route_intersects_oracle_weather_hazard"
    if comm_sensitive and route_coverage(world.communication_regions_true) < 0.85 and impacted:
        return False, "communication_coverage_below_threshold"
    if task.family == "F6" and "T24" not in tools:
        return False, "missing_visualization"
    return True, "success"
