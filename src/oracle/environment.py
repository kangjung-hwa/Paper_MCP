from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.models.contracts import DataArtifact, ExecutionCondition
from src.models.task import TaskInstance


@dataclass
class OracleWorldState:
    own_position_true: tuple[float, float]
    destination_true: tuple[float, float]
    threat_polygons_true: list[tuple[float, float, float, float]]
    weather_hazards_true: list[tuple[float, float, float, float]]
    communication_regions_true: list[tuple[float, float, float, float]]
    terrain_obstacles_true: list[tuple[float, float, float, float]]
    current_time: float
    outcome_impacted: bool
    failure_mode: str


def world_from_task(task: TaskInstance) -> OracleWorldState:
    w = task.oracle_world or {}
    return OracleWorldState(
        own_position_true=tuple(w.get("own_position_true", (0.0, 0.0))),
        destination_true=tuple(w.get("destination_true", (100.0, 100.0))),
        threat_polygons_true=[tuple(x) for x in w.get("threat_polygons_true", [])],
        weather_hazards_true=[tuple(x) for x in w.get("weather_hazards_true", [])],
        communication_regions_true=[tuple(x) for x in w.get("communication_regions_true", [(0.0, 0.0, 100.0, 100.0)])],
        terrain_obstacles_true=[tuple(x) for x in w.get("terrain_obstacles_true", [])],
        current_time=float(w.get("current_time", 0.0)),
        outcome_impacted=bool(w.get("outcome_impacted", task.severity == "critical")),
        failure_mode=w.get("failure_mode", task.violation_type),
    )


def initial_artifact(name: str, task: TaskInstance) -> DataArtifact:
    attrs = task.initial_state.get(name, {})
    cond = ExecutionCondition(
        schema_type="Constraints" if name == "constraints" else "str" if name in {"platform_id", "mission_id", "area_id", "image"} else None,
        semantic_type={
            "position": "Position",
            "destination": "Position",
            "threat": "ThreatInfo",
            "weather": "Weather",
            "terrain": "TerrainMap",
            "comm": "CommStatus",
            "object_position": "ObjectPosition",
        }.get(name),
        unit=attrs.get("unit"),
        reference_frame=attrs.get("reference_frame"),
        timestamp=-float(attrs.get("age", 0)),
        confidence=attrs.get("confidence"),
        provenance=attrs.get("provenance"),
    )
    value: dict[str, Any] = {"name": name}
    world = world_from_task(task)
    if name == "position":
        value["point"] = world.own_position_true
    elif name == "destination":
        value["point"] = world.destination_true
    return DataArtifact(name, cond, value, produced_by="initial")


def rectangle_intersects_route(rect: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = rect
    return min(x1, x2) <= 50 <= max(x1, x2) and min(y1, y2) <= 50 <= max(y1, y2)


def route_coverage(regions: list[tuple[float, float, float, float]]) -> float:
    if any(min(r[0], r[2]) <= 0 <= max(r[0], r[2]) and min(r[1], r[3]) <= 0 <= max(r[1], r[3]) and min(r[0], r[2]) <= 100 <= max(r[0], r[2]) and min(r[1], r[3]) <= 100 <= max(r[1], r[3]) for r in regions):
        return 1.0
    return 0.6
