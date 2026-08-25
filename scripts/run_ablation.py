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
    task_path = Path(cfg["task_path"])
    rows = read_jsonl(task_path)
    tasks = [TaskInstance.from_dict(r) for r in rows] if rows else generate_tasks(int(cfg["seed"]))
    registry = ToolRegistry()
    out = []
    settings = {
        "A1_no_downstream": {"method": "proposed", "flags": {"no_downstream": True}},
        "A2_no_cost": {"method": "proposed", "flags": {"no_cost": True}},
        "A3_strict_repair": {"method": "proposed", "flags": {"strict": True}},
        "A4_no_deficit_magnitude": {"method": "proposed", "flags": {"binary_deficit": True}},
        "A5_full_proposed": {"method": "proposed", "flags": {}},
    }
    for label, s in settings.items():
        for t in tasks:
            row = run_one(t, s["method"], registry, float(cfg["theta"]), float(cfg["lambda"]), cfg["model_name"], float(cfg["temperature"]), s["flags"])
            row["method"] = label
            out.append(row)
    write_jsonl(Path("results/raw/ablation_all.jsonl"), out)
    from src.evaluation.metrics import summarize

    write_csv(Path("results/summary/ablation.csv"), summarize(out))
    print(f"wrote {len(out)} ablation rows")


if __name__ == "__main__":
    main()
