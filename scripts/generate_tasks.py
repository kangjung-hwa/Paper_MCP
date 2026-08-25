#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tasks.generator import save_tasks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="data/tasks/tasks_seed42.jsonl")
    args = p.parse_args()
    tasks = save_tasks(Path(args.out), args.seed)
    print(f"wrote {len(tasks)} tasks to {args.out}")


if __name__ == "__main__":
    main()
