#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.runner import run_one
from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.tasks.generator import generate_tasks
from src.utils.serialization import read_jsonl, write_csv, write_jsonl


def main():
    cfg = yaml.safe_load(Path("configs/experiment.yaml").read_text())
    seeds = cfg.get("seeds", [int(cfg.get("seed", 42))])
    tasks = []
    for seed in seeds:
        path = Path(f"data/v3/tasks_seed{seed}.jsonl")
        rows = read_jsonl(path)
        tasks.extend([TaskInstance.from_dict(r) for r in rows] if rows else generate_tasks(int(seed)))
    registry = ToolRegistry()
    out = []
    settings = {
        "A1_strict_repair": {"method": "proposed", "flags": {"strict": True}},
        "A2_risk_only_selective": {"method": "proposed", "flags": {"no_cost": True}},
        "A3_risk_cost_selective": {"method": "proposed", "flags": {}},
    }
    for label, spec in settings.items():
        for t in tasks:
            row = run_one(t, spec["method"], registry, float(cfg["theta"]), float(cfg["lambda"]), cfg["model_name"], float(cfg["temperature"]), spec["flags"], planner_mode=cfg.get("planner_mode", "deterministic"), max_tool_calls=int(cfg.get("max_tool_calls", 20)), metadata_mode=cfg.get("metadata_mode", "full"))
            row["method"] = label
            out.append(row)
    write_jsonl(Path("results/v3/raw/cost_ablation_all.jsonl"), out)

    downstream = []
    for label, flags in {"risk_only": {}, "risk_structural_dependency": {"structural_dependency": True}}.items():
        for t in tasks:
            row = run_one(t, "proposed", registry, float(cfg["theta"]), float(cfg["lambda"]), cfg["model_name"], float(cfg["temperature"]), flags, planner_mode=cfg.get("planner_mode", "deterministic"), max_tool_calls=int(cfg.get("max_tool_calls", 20)), metadata_mode=cfg.get("metadata_mode", "full"))
            row["method"] = label
            downstream.append(row)
    write_jsonl(Path("results/v3/raw/downstream_ablation_all.jsonl"), downstream)

    from src.evaluation.metrics import summarize

    write_csv(Path("results/v3/summary/cost_ablation.csv"), summarize(out))
    write_csv(Path("results/v3/summary/downstream_ablation.csv"), summarize(downstream))
    print(f"wrote {len(out)} cost ablation rows and {len(downstream)} downstream rows")


if __name__ == "__main__":
    main()
