#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.metrics import summarize
from src.evaluation.runner import run_one
from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.tasks.generator import generate_tasks
from src.utils.serialization import read_jsonl, write_csv


def _load_tasks(cfg):
    rows = read_jsonl(Path(cfg.get("task_path", "data/tasks/tasks_seed42.jsonl")))
    return [TaskInstance.from_dict(r) for r in rows] if rows else generate_tasks(int(cfg.get("seed", 42)))


def _sensitivity(tasks, cfg, field, values):
    registry = ToolRegistry()
    out = []
    for value in values:
        rows = []
        for t in tasks:
            theta = float(value) if field == "theta" else float(cfg.get("theta", 0.3))
            lam = float(value) if field == "lambda" else float(cfg.get("lambda", 0.25))
            row = run_one(t, "proposed", registry, theta, lam, cfg.get("model_name", "deterministic-planner"), float(cfg.get("temperature", 0.0)))
            row["method"] = f"{field}={value}"
            rows.append(row)
        out.extend(summarize(rows))
    return out


def main():
    raw_dir = Path("results/raw")
    rows = []
    main_methods = {"react", "schema_aware", "strict", "proposed"}
    for path in raw_dir.glob("*_all.jsonl"):
        if path.name.startswith("ablation"):
            continue
        rows.extend([r for r in read_jsonl(path) if r.get("method") in main_methods])
    summary = summarize(rows)
    write_csv(Path("results/summary/main_results.csv"), summary)
    write_csv(Path("results/summary/by_task_family.csv"), summarize(rows, "family"))
    write_csv(Path("results/summary/by_violation_type.csv"), summarize(rows, "violation_type"))
    write_csv(Path("results/summary/by_severity.csv"), summarize(rows, "severity"))

    cfg_path = Path("configs/experiment.yaml")
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text())
        tasks = _load_tasks(cfg)
        write_csv(Path("results/summary/theta_sensitivity.csv"), _sensitivity(tasks, cfg, "theta", [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]))
        write_csv(Path("results/summary/lambda_sensitivity.csv"), _sensitivity(tasks, cfg, "lambda", [0,0.1,0.25,0.5,1,2]))

    Path("results/figures").mkdir(parents=True, exist_ok=True)
    write_csv(Path("results/figures/figure_source_main.csv"), summary)
    print("wrote summary CSV files")


if __name__ == "__main__":
    main()
