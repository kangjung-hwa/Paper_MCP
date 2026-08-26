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
from src.utils.serialization import read_jsonl, write_jsonl


def stratified_sample(tasks, n):
    buckets = {}
    for t in tasks:
        buckets.setdefault((t.family, t.severity), []).append(t)
    keys = sorted(buckets)
    out = []
    index = 0
    while len(out) < n and any(index < len(buckets[k]) for k in keys):
        for key in keys:
            if len(out) >= n:
                break
            if index < len(buckets[key]):
                out.append(buckets[key][index])
        index += 1
    return out


def main():
    cfg = yaml.safe_load(Path("configs/experiment.yaml").read_text())
    cfg["planner_mode"] = "llm"
    rows = read_jsonl(Path(cfg["task_path"]))
    tasks = [TaskInstance.from_dict(r) for r in rows] if rows else generate_tasks(int(cfg["seed"]))
    tasks = stratified_sample(tasks, int(cfg.get("llm_sample_size", 60)))
    registry = ToolRegistry()
    out = []
    for method in ["react_llm", "schema_aware_llm", "proposed_llm"]:
        for t in tasks:
            out.append(run_one(t, method, registry, float(cfg["theta"]), float(cfg["lambda"]), cfg["model_name"], float(cfg["temperature"]), planner_mode="llm", max_tool_calls=int(cfg.get("max_tool_calls", 20))))
    write_jsonl(Path("results/v3/raw/llm_validation.jsonl"), out)
    print(f"wrote {len(out)} LLM validation rows")


if __name__ == "__main__":
    main()
