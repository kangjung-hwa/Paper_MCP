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
                oracle_conditions={"minor_success_tolerated": sev == "minor"},
                seed=task_seed,
                split=split,
            ))
    return tasks


def save_tasks(path: Path, seed: int = 42) -> list[TaskInstance]:
    tasks = generate_tasks(seed)
    write_jsonl(path, [t.to_dict() for t in tasks])
    return tasks
