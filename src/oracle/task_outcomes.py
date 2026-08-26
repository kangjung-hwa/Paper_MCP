from __future__ import annotations

from src.models.workflow import Workflow
from src.oracle.environment import rectangle_intersects_route, route_coverage, world_from_task


def route_outcome(workflow: Workflow, task) -> tuple[bool, str]:
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
    repaired = any(n.inserted for n in workflow.nodes)
    impacted = world.outcome_impacted and not repaired
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
