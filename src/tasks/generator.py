from __future__ import annotations

import random
from pathlib import Path

from src.models.task import TaskInstance
from src.tasks.violations import choose_violation, initial_attributes
from src.utils.serialization import write_jsonl

FAMILIES = {
    "F1": "basic_route",
    "F2": "threat_aware_route",
    "F3": "weather_aware_route",
    "F4": "communication_aware_route",
    "F5": "multi_constraint_route",
    "F6": "situation_route_recommendation",
}

QUERIES = {
    "F1": "현재 위치에서 목표지점까지 이동 가능한 경로를 생성하라.",
    "F2": "현재 위협지역을 회피하여 목표지점까지 이동경로를 생성하라.",
    "F3": "현재 기상조건을 고려하여 목표지점까지 이동 가능한 경로를 생성하라.",
    "F4": "이동 중 통신 연결성을 유지할 수 있는 경로를 생성하라.",
    "F5": "현재 위협과 기상조건을 고려하여 안전한 이동경로를 생성하라.",
    "F6": "현재 상황을 분석하고 추천 이동경로와 판단 결과를 제시하라.",
}


def _oracle_world(family: str, violation_type: str, severity: str, rng: random.Random) -> dict:
    impacted = severity == "critical"
    world = {
        "own_position_true": [0.0, 0.0],
        "destination_true": [100.0, 100.0],
        "threat_polygons_true": [],
        "weather_hazards_true": [],
        "communication_regions_true": [[0.0, 0.0, 100.0, 100.0]],
        "terrain_obstacles_true": [],
        "current_time": 0.0,
        "outcome_impacted": impacted,
        "failure_mode": violation_type,
        "valid_but_route_blocked": False,
    }
    if impacted:
        if family in {"F2", "F5", "F6"}:
            world["threat_polygons_true"] = [[45.0, 45.0, 55.0, 55.0]]
        elif family == "F3":
            world["weather_hazards_true"] = [[45.0, 45.0, 55.0, 55.0]]
        elif family == "F4":
            world["communication_regions_true"] = [[0.0, 0.0, 40.0, 40.0]]
        else:
            world["terrain_obstacles_true"] = [[45.0, 45.0, 55.0, 55.0]]
        if rng.random() < 0.1:
            world["valid_but_route_blocked"] = True
    return world


def generate_tasks(seed: int = 42) -> list[TaskInstance]:
    rng = random.Random(seed)
    tasks = []
    for f in FAMILIES:
        severities = ["normal"] * 20 + ["minor"] * 15 + ["critical"] * 15
        rng.shuffle(severities)
        for i, sev in enumerate(severities, 1):
            vt = choose_violation(rng, sev)
            task_seed = seed * 10000 + int(f[1]) * 100 + i
            split = "dev" if i <= 15 else "test"
            tasks.append(TaskInstance(
                task_id=f"{f}_{i:03d}",
                family=f,
                query=QUERIES[f],
                initial_state=initial_attributes(vt, sev),
                violation_type=vt,
                severity=sev,
                oracle_conditions={"minor_success_tolerated": sev == "minor", "outcome_impacted": sev == "critical"},
                seed=task_seed,
                split=split,
                oracle_world=_oracle_world(f, vt, sev, rng),
            ))
    return tasks


def save_tasks(path: Path, seed: int = 42) -> list[TaskInstance]:
    tasks = generate_tasks(seed)
    write_jsonl(path, [t.to_dict() for t in tasks])
    return tasks
