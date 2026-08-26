#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.runner import run_tasks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--method", choices=["react", "schema_aware", "strict", "proposed", "react_llm", "schema_aware_llm", "proposed_llm"], required=True)
    p.add_argument("--split", choices=["dev", "test", "all"], default="all")
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()
    cfg_path = Path(args.config)
    cfg = yaml.safe_load(cfg_path.read_text())
    seed_suffix = f"_seed{args.seed}" if args.seed is not None else ""
    task_path = Path(f"data/v3/tasks_seed{args.seed}.jsonl") if args.seed is not None else Path(cfg.get("task_path", "data/v3/tasks_seed42.jsonl"))
    if args.seed is not None:
        cfg["seed"] = args.seed
    out = Path("results/v3/raw") / f"{args.method}{seed_suffix}_{args.split}.jsonl"
    rows = run_tasks(args.method, cfg, task_path, out, None if args.split == "all" else args.split)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cfg_path, out.parent / f"{args.method}_{args.split}_config.yaml")
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
