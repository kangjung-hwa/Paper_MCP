from __future__ import annotations

from src.models.workflow import Workflow
from src.oracle.environment import rectangle_intersects_route, route_coverage, world_from_task


ROUTE_PLANNERS = {"T19", "T20", "T21", "T22"}


def _impact_was_remediated(workflow: Workflow, oracle_rows: list[dict] | None) -> bool:
    """Return whether an inserted repair actually normalized the route input.

    Merely finding an inserted node is not evidence of recovery.  A repair must be
    on the data lineage consumed by a route planner, and that planner must observe
    no remaining execution-condition deficit on the repaired artifact.  The rows
    come from the oracle simulator rather than the orchestration validator so the
    outcome evaluation remains independent of the proposed method's validator.
    """
    if oracle_rows is None:
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

    planner_rows = [row for row in oracle_rows if row["tool_id"] in ROUTE_PLANNERS]
    repaired_lineage_reached_planner = any(
        has_inserted_ancestor(row["artifact_id"]) for row in planner_rows
    )
    return repaired_lineage_reached_planner and bool(planner_rows) and all(
        not any(value > 0 for value in row["deficits"].values())
        for row in planner_rows
    )


def route_outcome(workflow: Workflow, task, oracle_rows: list[dict] | None = None) -> tuple[bool, str]:
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
    impacted = world.outcome_impacted and not _impact_was_remediated(workflow, oracle_rows)
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
