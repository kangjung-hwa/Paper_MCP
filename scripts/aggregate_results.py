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
            theta = float(value) if field == "theta" else float(cfg.get("theta", 0.05))
            lam = float(value) if field == "lambda" else float(cfg.get("lambda", 0.25))
            row = run_one(t, "proposed", registry, theta, lam, cfg.get("model_name", "deterministic-planner"), float(cfg.get("temperature", 0.0)))
            row["method"] = f"{field}={value}"
            rows.append(row)
        out.extend(summarize(rows))
    return out


def _depth_bucket(d):
    if d <= 1:
        return "depth_0_1"
    if d == 2:
        return "depth_2"
    return "depth_ge_3"


def _branch_bucket(b):
    if b <= 1:
        return "branch_0_1"
    return "branch_ge_2"


def _sanity_warnings(rows):
    warnings = []
    by_method = {}
    for r in rows:
        sig = (r["GT_valid"], r["GT_success"], r["repair_decision"], r["tool_calls"], round(float(r["simulated_latency_ms"]), 6), r.get("final_workflow"))
        by_method.setdefault(r["method"], []).append((r["task_id"], sig))
    methods = sorted(by_method)
    for i, a in enumerate(methods):
        for b in methods[i+1:]:
            if by_method[a] == by_method[b]:
                warnings.append(f"WARNING: two methods produced identical outputs for all tasks: {a}, {b}. Check whether implementations are effectively identical.")
    for metric in ["outcome_unnecessary_repairs", "validity_unnecessary_repairs"]:
        vals = [r.get(metric, 0) for r in rows]
        if vals and (all(v == 0 for v in vals) or all(v > 0 for v in vals)):
            warnings.append("WARNING: repair metric may be degenerate.")
            break
    if rows and all(r["GT_valid"] == r["GT_success"] for r in rows):
        warnings.append("WARNING: validity and outcome ground truths are not sufficiently independent.")
    risks = {round(float(r.get("predicted_risk", 0.0)), 12) for r in rows}
    if len(risks) <= 1:
        warnings.append("WARNING: Risk score is identical for all tasks.")
    return warnings


def main():
    root = Path("results/v2")
    raw_dir = root / "raw"
    summary_dir = root / "summary"
    rows = []
    main_methods = {"react", "schema_aware", "strict", "proposed"}
    for path in raw_dir.glob("*_all.jsonl"):
        if path.name.startswith("ablation"):
            continue
        rows.extend([r for r in read_jsonl(path) if r.get("method") in main_methods])
    summary = summarize(rows)
    write_csv(summary_dir / "main_results.csv", summary)
    write_csv(summary_dir / "by_task_family.csv", summarize(rows, "family"))
    write_csv(summary_dir / "by_violation_type.csv", summarize(rows, "violation_type"))
    write_csv(summary_dir / "by_severity.csv", summarize(rows, "severity"))
    ablation_rows = read_jsonl(raw_dir / "ablation_all.jsonl")
    depth_rows = []
    for r in rows + ablation_rows:
        if r["method"] in {"proposed", "A1_no_downstream", "A5_full_proposed"}:
            x = dict(r)
            x["depth_bucket"] = _depth_bucket(int(r.get("downstream_depth", 0)))
            depth_rows.append(x)
    write_csv(summary_dir / "by_downstream_depth.csv", summarize(depth_rows, "depth_bucket"))
    branch_rows = []
    for r in rows + ablation_rows:
        if r["method"] in {"proposed", "A1_no_downstream", "A5_full_proposed"}:
            x = dict(r)
            x["branch_bucket"] = _branch_bucket(int(r.get("branching_factor", 0)))
            branch_rows.append(x)
    write_csv(summary_dir / "by_branching_factor.csv", summarize(branch_rows, "branch_bucket"))

    cfg_path = Path("configs/experiment.yaml")
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text())
        tasks = _load_tasks(cfg)
        write_csv(summary_dir / "theta_sensitivity.csv", _sensitivity(tasks, cfg, "theta", [0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]))
        write_csv(summary_dir / "lambda_sensitivity.csv", _sensitivity(tasks, cfg, "lambda", [0,0.1,0.25,0.5,1,2]))

    (root / "figures").mkdir(parents=True, exist_ok=True)
    write_csv(root / "figures" / "figure_source_main.csv", summary)
    warnings = _sanity_warnings(rows)
    (summary_dir / "sanity_warnings.txt").write_text("\n".join(warnings) + ("\n" if warnings else ""))
    for w in warnings:
        print(w)
    print("wrote v2 summary CSV files")


if __name__ == "__main__":
    main()
