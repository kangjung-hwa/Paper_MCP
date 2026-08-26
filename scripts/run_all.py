#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

SEEDS = [42, 123, 2026]


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    py = sys.executable
    for seed in SEEDS:
        run([py, "scripts/generate_tasks.py", "--seed", str(seed)])
        for method in ["react", "schema_aware", "strict", "proposed"]:
            run([py, "scripts/run_experiment.py", "--config", "configs/experiment.yaml", "--method", method, "--seed", str(seed)])
    run([py, "scripts/run_ablation.py"])
    run([py, "scripts/aggregate_results.py"])


if __name__ == "__main__":
    main()
