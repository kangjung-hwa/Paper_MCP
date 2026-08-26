#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.metrics import summarize
from src.evaluation.runner import run_one
from src.evaluation.statistics import bootstrap_ci, mcnemar_counts, paired_mean_effect
from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.tasks.generator import generate_tasks
from src.utils.serialization import read_jsonl, write_csv


def _load_tasks(path, seed):
    rows = read_jsonl(Path(path))
    return [TaskInstance.from_dict(r) for r in rows] if rows else generate_tasks(seed)


def _sensitivity(cfg, field, values):
    registry = ToolRegistry()
    out = []
    tasks = _load_tasks(cfg.get("task_path", "data/v3/tasks_seed42.jsonl"), int(cfg.get("seed", 42)))
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


def _sanity_warnings(rows, cost_rows):
    warnings = []
    by_method = {}
    for r in rows:
        sig = (r["task_id"], r["seed"], r["GT_valid"], r["GT_success"], r["repair_decision"], r["tool_calls"], r.get("final_workflow"))
        by_method.setdefault(r["method"], []).append(sig)
    if by_method.get("react") == by_method.get("schema_aware"):
        warnings.append("WARNING: ReAct and Schema-aware produced identical task-level results.")
    if rows and all(r["GT_valid"] == r["GT_success"] for r in rows):
        warnings.append("WARNING: all tasks have GT_valid == GT_success.")
    repair_rows = [r for r in rows if r["method"] in {"strict", "proposed"} and r.get("selected_repair")]
    if repair_rows:
        vals = []
        for method in ["strict", "proposed"]:
            subset = [r for r in repair_rows if r["method"] == method]
            inserted = sum(len(r["selected_repair"].get("tools", [])) for r in subset if r.get("selected_repair"))
            ourr = sum(r.get("outcome_unnecessary_repairs", 0) for r in subset)
            vals.append(ourr / inserted if inserted else 0.0)
        if all(v == 0 for v in vals) or all(v == 1 for v in vals):
            warnings.append("WARNING: OURR is degenerate across repair methods.")
    eligible = [r for r in cost_rows if r.get("multi_candidate_task")]
    if eligible and all(not r.get("selection_changed_by_cost") for r in eligible):
        warnings.append("WARNING: Cost term never changes repair selection. Cost-aware contribution is unsupported by current testbed.")
    proposed = [r for r in rows if r["method"] == "proposed"]
    if proposed and (all(r["repair_decision"] for r in proposed) or all(not r["repair_decision"] for r in proposed)):
        warnings.append("WARNING: Proposed repairs either all tasks or no tasks.")
    return warnings


def main():
    root = Path("results/v3")
    raw_dir = root / "raw"
    summary_dir = root / "summary"
    rows = []
    main_methods = {"react", "schema_aware", "strict", "proposed"}
    for path in raw_dir.glob("*_seed*_all.jsonl"):
        rows.extend([r for r in read_jsonl(path) if r.get("method") in main_methods])
    if not rows:
        for path in raw_dir.glob("*_all.jsonl"):
            if not any(path.name.startswith(prefix) for prefix in ["cost_", "downstream_"]):
                rows.extend([r for r in read_jsonl(path) if r.get("method") in main_methods])
    summary = summarize(rows)
    write_csv(summary_dir / "main_results.csv", summary)
    write_csv(summary_dir / "by_task_family.csv", summarize(rows, "family"))
    write_csv(summary_dir / "by_violation_type.csv", summarize(rows, "violation_type"))
    write_csv(summary_dir / "by_severity.csv", summarize(rows, "severity"))

    cost_rows = read_jsonl(raw_dir / "cost_ablation_all.jsonl")
    downstream_rows = read_jsonl(raw_dir / "downstream_ablation_all.jsonl")
    if cost_rows:
        write_csv(summary_dir / "cost_contribution.csv", summarize(cost_rows))
    if downstream_rows:
        write_csv(summary_dir / "downstream_ablation.csv", summarize(downstream_rows))


    strict_rows = [r for r in rows if r.get("method") == "strict"]
    proposed_rows = [r for r in rows if r.get("method") == "proposed"]
    stats_rows = []
    if strict_rows and proposed_rows:
        for outcome in ["GT_success", "GT_valid"]:
            mc = mcnemar_counts(strict_rows, proposed_rows, outcome)
            stats_rows.append({"comparison": "strict_vs_proposed", "metric": outcome, **mc})
        for field in ["simulated_latency_ms", "tool_calls", "outcome_unnecessary_repairs"]:
            eff = paired_mean_effect(strict_rows, proposed_rows, field)
            ci = bootstrap_ci([float(r[field]) for r in proposed_rows])
            stats_rows.append({"comparison": "strict_vs_proposed", "metric": field, **eff, "proposed_bootstrap_ci_low": ci["low"], "proposed_bootstrap_ci_high": ci["high"]})
        strict_by_id = {(r["task_id"], r["seed"]): r for r in strict_rows}
        prop_by_id = {(r["task_id"], r["seed"]): r for r in proposed_rows}
        diffs = [float(prop_by_id[k]["GT_success"]) - float(strict_by_id[k]["GT_success"]) for k in sorted(set(strict_by_id) & set(prop_by_id))]
        stats_rows.append({"comparison": "strict_vs_proposed", "metric": "TSR_difference_prop_minus_strict", "mean_difference": sum(diffs) / len(diffs) if diffs else 0.0, "n": len(diffs)})
    write_csv(summary_dir / "statistical_tests.csv", stats_rows)

    cfg_path = Path("configs/experiment.yaml")
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text())
        write_csv(summary_dir / "theta_sensitivity.csv", _sensitivity(cfg, "theta", [0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]))
        write_csv(summary_dir / "lambda_sensitivity.csv", _sensitivity(cfg, "lambda", [0,0.1,0.25,0.5,1,2]))

    (root / "figures").mkdir(parents=True, exist_ok=True)
    write_csv(root / "figures" / "figure_source_main.csv", summary)
    warnings = _sanity_warnings(rows, cost_rows)
    (summary_dir / "sanity_warnings.txt").write_text("\n".join(warnings) + ("\n" if warnings else ""))
    for w in warnings:
        print(w)
    print("wrote v3 summary CSV files")


if __name__ == "__main__":
    main()
