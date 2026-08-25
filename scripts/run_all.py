#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main():
    py = sys.executable
    run([py, "scripts/generate_tasks.py", "--seed", "42"])
    for method in ["react", "schema_aware", "strict", "proposed"]:
        run([py, "scripts/run_experiment.py", "--config", "configs/experiment.yaml", "--method", method])
    run([py, "scripts/run_ablation.py"])
    run([py, "scripts/aggregate_results.py"])


if __name__ == "__main__":
    main()
