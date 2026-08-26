#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.evaluation.metrics import mean, pr_auc, roc_auc
from src.evaluation.statistics import bootstrap_ci, mcnemar_counts, paired_mean_effect
from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.models.workflow import Workflow, WorkflowNode
from src.oracle.operational_validity import evaluate_operational_validity, workflow_from_dict
from src.utils.serialization import read_jsonl, write_csv, write_jsonl
from src.orchestration.risk import workflow_risk

METHODS = ["react", "schema_aware", "strict", "proposed"]
DISPLAY = {"react": "ReAct", "schema_aware": "Schema-Aware", "strict": "Strict", "proposed": "Proposed"}
ROOT = Path("results/v3_operational_validity")


def _write_ordered_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _seed_from_name(path: Path) -> int:
    m = re.search(r"_seed(\d+)_", path.name)
    if not m:
        return 42
    return int(m.group(1))


def _task_maps() -> dict[tuple[int, str], TaskInstance]:
    out = {}
    for path in Path("data/v3").glob("tasks_seed*.jsonl"):
        seed = int(re.search(r"seed(\d+)", path.name).group(1))
        for row in read_jsonl(path):
            t = TaskInstance.from_dict(row)
            out[(seed, t.task_id)] = t
    return out


def _schema_connectivity(workflow: Workflow, registry: ToolRegistry) -> bool:
    available = {
        "platform_id": "str", "mission_id": "str", "area_id": "str", "constraints": "Constraints", "image": "image",
        "position": "Position", "destination": "Position", "threat": "ThreatInfo", "weather": "Weather", "terrain": "TerrainMap", "comm": "CommStatus", "object_position": "ObjectPosition",
    }
    for node in workflow.nodes:
        spec = registry.get(node.tool_id).public_spec(full_metadata=False)
        for inp, aid in node.inputs.items():
            if aid not in available:
                return False
            req = spec["inputs"].get(inp, {})
            want = req.get("semantic_type") or req.get("schema_type")
            if want and want != available[aid] and not (want == "SpatialData" and available[aid] in {"Position", "ThreatInfo", "TerrainMap", "ObjectPosition"}):
                return False
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            available[aid] = cond.get("semantic_type") or cond.get("schema_type") or out_name
    return workflow.goal in available


def _binary_metrics(labels, preds):
    tp = sum(1 for y, p in zip(labels, preds) if y and p)
    fp = sum(1 for y, p in zip(labels, preds) if not y and p)
    fn = sum(1 for y, p in zip(labels, preds) if y and not p)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _repair_metrics(rows):
    tp = sum(1 for r in rows if r["repair_decision"] and r["repair_required"])
    fp = sum(1 for r in rows if r["repair_decision"] and not r["repair_required"])
    fn = sum(1 for r in rows if not r["repair_decision"] and r["repair_required"])
    p = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * rc / (p + rc) if p + rc else 0.0
    return p, rc, f1


def _summarize(rows, group_key=None):
    groups = defaultdict(list)
    for r in rows:
        key = (r["method"], r[group_key]) if group_key else (r["method"], "all")
        groups[key].append(r)
    out = []
    for (method, group), rs in sorted(groups.items()):
        labels = [1 - r["GT_operational_valid"] for r in rs]
        scores = [r["operational_risk_score"] for r in rs]
        preds = [r["operational_risk_prediction"] for r in rs]
        ip, ir, if1 = _binary_metrics(labels, preds)
        rp, rr, rf1 = _repair_metrics(rs)
        inserted = sum(len(r.get("selected_repair", {}).get("tools", [])) if r.get("selected_repair") else 0 for r in rs)
        ourr = sum(r.get("outcome_unnecessary_repairs", 0) for r in rs)
        row = {
            "Method": DISPLAY.get(method, method),
            "method": method,
            "group": group,
            "SchemaConnectivityRate": mean([r["GT_schema_connected"] for r in rs]),
            "SCCR": mean([r["GT_strict_valid"] for r in rs]),
            "EPVR": mean([r["GT_strict_valid"] for r in rs]),
            "OEPVR": mean([r["GT_operational_valid"] for r in rs]),
            "TSR": mean([r["GT_success"] for r in rs]),
            "InvalidPlanPrecision": ip,
            "InvalidPlanRecall": ir,
            "InvalidPlanF1": if1,
            "InvalidPlanROC_AUC": roc_auc(labels, scores),
            "InvalidPlanPR_AUC": pr_auc(labels, scores),
            "RepairPrecision": rp,
            "RepairRecall": rr,
            "RepairF1": rf1,
            "OURR": ourr / inserted if inserted else 0.0,
            "RepairRate": mean([1.0 if r["repair_decision"] else 0.0 for r in rs]),
            "AvgToolCalls": mean([r["tool_calls"] for r in rs]),
            "AvgAddedCalls": mean([r.get("average_added_calls", 0.0) for r in rs]),
            "AvgLatency": mean([r["simulated_latency_ms"] for r in rs]),
            "AvgAddedLatency": mean([r.get("average_added_latency", 0.0) for r in rs]),
        }
        out.append(row)
    return out


def _transition_counts(rows):
    out = []
    for method in METHODS:
        rs = [r for r in rows if r["method"] == method]
        combos = {
            "SCCR0_OEPV1": sum(1 for r in rs if r["GT_strict_valid"] == 0 and r["GT_operational_valid"] == 1),
            "SCCR0_OEPV0": sum(1 for r in rs if r["GT_strict_valid"] == 0 and r["GT_operational_valid"] == 0),
            "SCCR1_OEPV1": sum(1 for r in rs if r["GT_strict_valid"] == 1 and r["GT_operational_valid"] == 1),
            "OEPV1_TSR1": sum(1 for r in rs if r["GT_operational_valid"] == 1 and r["GT_success"] == 1),
            "OEPV1_TSR0": sum(1 for r in rs if r["GT_operational_valid"] == 1 and r["GT_success"] == 0),
            "OEPV0_TSR1": sum(1 for r in rs if r["GT_operational_valid"] == 0 and r["GT_success"] == 1),
            "OEPV0_TSR0": sum(1 for r in rs if r["GT_operational_valid"] == 0 and r["GT_success"] == 0),
        }
        out.append({"method": method, "Method": DISPLAY[method], "n": len(rs), **combos})
    return out


def _strict_proposed_deltas(summary):
    by = {r["method"]: r for r in summary if r["group"] == "all"}
    s, p = by["strict"], by["proposed"]
    keys = ["SCCR", "OEPVR", "TSR", "OURR", "RepairRate", "RepairF1", "AvgLatency", "AvgAddedLatency", "AvgToolCalls"]
    return [{"metric": k, "strict": s[k], "proposed": p[k], "delta_proposed_minus_strict": p[k] - s[k]} for k in keys]


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key, value in list(row.items()):
            try:
                row[key] = float(value)
            except (TypeError, ValueError):
                pass
    return rows


def _paper_tables(summary, violation_summary, cost_summary):
    all_rows = [r for r in summary if r["group"] == "all"]
    main_fields = ["Method", "SCCR", "OEPVR", "TSR", "Repair Precision", "Repair Recall", "Repair F1", "OURR", "Repair Rate", "Avg Tool Calls", "Avg Added Latency"]
    main_rows = [{
        "Method": r["Method"], "SCCR": r["SCCR"], "OEPVR": r["OEPVR"], "TSR": r["TSR"],
        "Repair Precision": r["RepairPrecision"], "Repair Recall": r["RepairRecall"], "Repair F1": r["RepairF1"],
        "OURR": r["OURR"], "Repair Rate": r["RepairRate"], "Avg Tool Calls": r["AvgToolCalls"], "Avg Added Latency": r["AvgAddedLatency"],
    } for r in all_rows]
    _write_ordered_csv(ROOT / "summary" / "paper_table_main.csv", main_rows, main_fields)
    detection_fields = ["Method", "Invalid Plan Precision", "Invalid Plan Recall", "Invalid Plan F1", "Invalid Plan ROC-AUC", "Invalid Plan PR-AUC"]
    detection_rows = [{
        "Method": r["Method"], "Invalid Plan Precision": r["InvalidPlanPrecision"], "Invalid Plan Recall": r["InvalidPlanRecall"], "Invalid Plan F1": r["InvalidPlanF1"], "Invalid Plan ROC-AUC": r["InvalidPlanROC_AUC"], "Invalid Plan PR-AUC": r["InvalidPlanPR_AUC"],
    } for r in all_rows]
    _write_ordered_csv(ROOT / "summary" / "paper_table_validity_detection.csv", detection_rows, detection_fields)
    write_csv(ROOT / "summary" / "paper_table_violation_types.csv", violation_summary)
    if cost_summary:
        write_csv(ROOT / "summary" / "paper_table_cost_ablation.csv", cost_summary)


def _plot_grouped(pathbase, labels, series, ylabel="Rate", ylim=(0, 1), annotate=True):
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    width = 0.8 / len(series)
    x = list(range(len(labels)))
    hatches = ["//", "\\\\", "..", "xx"]
    markers = ["o", "s", "^", "D"]
    for i, (name, values) in enumerate(series.items()):
        pos = [v - 0.4 + width / 2 + i * width for v in x]
        bars = ax.bar(pos, values, width=width, label=name, edgecolor="black", hatch=hatches[i % len(hatches)], linewidth=0.8)
        ax.plot(pos, values, linestyle="", marker=markers[i % len(markers)], color="black", markersize=3)
        if annotate:
            for b, val in zip(bars, values):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + (ylim[1] * 0.015), f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_ylim(*ylim)
    ax.legend(fontsize=9, frameon=False)
    ax.grid(axis="y", linestyle=":", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / f"{pathbase}.png", dpi=300)
    fig.savefig(ROOT / "figures" / f"{pathbase}.pdf")
    plt.close(fig)


def _plot_line_curve(pathbase, xs, ys, label, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.plot(xs, ys, color="black", linestyle="-", marker="o", label=label)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(linestyle=":", linewidth=0.6)
    ax.legend(fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / f"{pathbase}.png", dpi=300)
    fig.savefig(ROOT / "figures" / f"{pathbase}.pdf")
    plt.close(fig)


def _curve_points(labels, scores):
    thresholds = sorted(set(scores), reverse=True) + [-1.0]
    roc = []
    pr = []
    pos = sum(labels)
    neg = len(labels) - pos
    for th in thresholds:
        preds = [s >= th for s in scores]
        tp = sum(1 for y, p in zip(labels, preds) if y and p)
        fp = sum(1 for y, p in zip(labels, preds) if not y and p)
        fn = sum(1 for y, p in zip(labels, preds) if y and not p)
        tn = sum(1 for y, p in zip(labels, preds) if not y and not p)
        tpr = tp / pos if pos else 0.0
        fpr = fp / neg if neg else 0.0
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tpr
        roc.append((fpr, tpr))
        pr.append((recall, precision))
    roc = sorted(set(roc))
    pr = sorted(set(pr))
    return roc, pr


def _make_figures(summary, transitions, violation_summary, cost_summary, raw_rows):
    ROOT.joinpath("figures").mkdir(parents=True, exist_ok=True)
    all_rows = [r for r in summary if r["group"] == "all"]
    labels = [r["Method"] for r in all_rows]
    _plot_grouped("fig_validity_hierarchy", labels, {
        "SCCR": [r["SCCR"] for r in all_rows], "OEPVR": [r["OEPVR"] for r in all_rows], "TSR": [r["TSR"] for r in all_rows]
    })
    sp = [r for r in all_rows if r["method"] in {"strict", "proposed"}]
    _plot_grouped("fig_conformance_operational_gap", [r["Method"] for r in sp], {
        "SCCR": [r["SCCR"] for r in sp], "OEPVR": [r["OEPVR"] for r in sp], "OEPVR-SCCR": [r["OEPVR"] - r["SCCR"] for r in sp]
    })
    _plot_grouped("fig_repair_quality", [r["Method"] for r in sp], {
        "Precision": [r["RepairPrecision"] for r in sp], "Recall": [r["RepairRecall"] for r in sp], "F1": [r["RepairF1"] for r in sp]
    })
    _plot_grouped("fig_repair_efficiency", [r["Method"] for r in sp], {
        "Repair Rate": [r["RepairRate"] for r in sp], "OURR": [r["OURR"] for r in sp]
    })
    _plot_grouped("fig_repair_efficiency_cost", [r["Method"] for r in sp], {
        "Added Calls": [r["AvgAddedCalls"] for r in sp], "Added Latency/100ms": [r["AvgAddedLatency"] / 100.0 for r in sp]
    }, ylabel="Scaled value", ylim=(0, max(1, max(r["AvgAddedLatency"] / 100.0 for r in sp) + 0.2)))
    vtypes = ["coordinate", "unit", "freshness", "confidence", "provenance", "compound"]
    vmap = defaultdict(dict)
    for r in violation_summary:
        vmap[r["group"]][r["method"]] = r
    _plot_grouped("fig_violation_type_effect", vtypes, {
        "OURR delta": [vmap[v].get("proposed", {}).get("OURR", 0) - vmap[v].get("strict", {}).get("OURR", 0) for v in vtypes],
        "Added latency delta/100ms": [(vmap[v].get("proposed", {}).get("AvgAddedLatency", 0) - vmap[v].get("strict", {}).get("AvgAddedLatency", 0)) / 100.0 for v in vtypes],
    }, ylabel="Delta Proposed-Strict", ylim=(-1, 1), annotate=False)
    if cost_summary:
        cs = [r for r in cost_summary if r["method"] in {"A2_risk_only_selective", "A3_risk_cost_selective"}]
        _plot_grouped("fig_risk_cost", [DISPLAY.get(r.get("method"), r.get("Method", "method")) for r in cs], {
            "TSR": [r["TSR"] for r in cs], "Risk Reduction": [r["risk_reduction"] for r in cs], "Added Latency/100ms": [(r.get("AvgAddedLatency", r.get("avg_added_latency", 0.0))) / 100.0 for r in cs]
        }, ylabel="Rate or scaled latency", ylim=(0, 1))
    proposed = [r for r in raw_rows if r["method"] == "proposed"]
    labels_invalid = [1 - r["GT_operational_valid"] for r in proposed]
    scores = [r["operational_risk_score"] for r in proposed]
    roc, pr = _curve_points(labels_invalid, scores)
    _plot_line_curve("fig_invalid_plan_roc", [x for x, _ in roc], [y for _, y in roc], f"AUC={roc_auc(labels_invalid, scores):.3f}", "False Positive Rate", "True Positive Rate")
    _plot_line_curve("fig_invalid_plan_pr", [x for x, _ in pr], [y for _, y in pr], f"AUC={pr_auc(labels_invalid, scores):.3f}", "Recall", "Precision")
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    states = ["Strict conformant", "Operational only", "Operationally invalid"]
    hatches = ["//", "..", "xx"]
    bottom = [0] * len(transitions)
    x = list(range(len(transitions)))
    values = []
    for t in transitions:
        n = t["n"] or 1
        values.append([t["SCCR1_OEPV1"] / n, t["SCCR0_OEPV1"] / n, t["SCCR0_OEPV0"] / n])
    for i, state in enumerate(states):
        vals = [v[i] for v in values]
        ax.bar(x, vals, bottom=bottom, label=state, edgecolor="black", hatch=hatches[i], linewidth=0.8)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(x)
    ax.set_xticklabels([t["Method"] for t in transitions])
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8, frameon=False)
    ax.grid(axis="y", linestyle=":", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig_validity_transition.png", dpi=300)
    fig.savefig(ROOT / "figures" / "fig_validity_transition.pdf")
    plt.close(fig)


def main():
    registry = ToolRegistry()
    tasks = _task_maps()
    raw_rows = []
    for method in METHODS:
        for path in sorted(Path("results/v3/raw").glob(f"{method}_seed*_all.jsonl")):
            dataset_seed = _seed_from_name(path)
            for row in read_jsonl(path):
                task = tasks[(dataset_seed, row["task_id"])]
                wf = workflow_from_dict(row["final_workflow"])
                op = evaluate_operational_validity(wf, task, registry)
                risk, risk_edges = workflow_risk(wf, task, registry, risk_mode="max", structural_dependency=False)
                enriched = dict(row)
                enriched.update(op)
                enriched["GT_schema_connected"] = int(_schema_connectivity(wf, registry))
                enriched["SCCR"] = op["GT_strict_valid"]
                enriched["OEPV"] = op["GT_operational_valid"]
                enriched["operational_risk_score"] = risk
                enriched["operational_risk_prediction"] = int(risk > float(row.get("theta", 0.05)))
                enriched["operational_risk_edges"] = risk_edges
                enriched["dataset_seed"] = dataset_seed
                raw_rows.append(enriched)
    ROOT.joinpath("raw").mkdir(parents=True, exist_ok=True)
    ROOT.joinpath("summary").mkdir(parents=True, exist_ok=True)
    write_jsonl(ROOT / "raw" / "operational_validity_all.jsonl", raw_rows)
    summary = _summarize(raw_rows)
    violation_summary = _summarize(raw_rows, "violation_type")
    seed_summary = _summarize(raw_rows, "dataset_seed")
    transitions = _transition_counts(raw_rows)
    write_csv(ROOT / "summary" / "main_validity_results.csv", summary)
    write_csv(ROOT / "summary" / "main_validity_results_by_seed.csv", seed_summary)
    write_csv(ROOT / "summary" / "validity_transition_counts.csv", transitions)
    write_csv(ROOT / "summary" / "by_violation_type.csv", violation_summary)
    deltas = _strict_proposed_deltas(summary)
    write_csv(ROOT / "summary" / "strict_vs_proposed_deltas.csv", deltas)
    cost_summary = _read_csv(Path("results/v3/summary/cost_contribution.csv"))
    _paper_tables(summary, violation_summary, cost_summary)
    stats = []
    strict = [r for r in raw_rows if r["method"] == "strict"]
    proposed = [r for r in raw_rows if r["method"] == "proposed"]
    for metric in ["GT_strict_valid", "GT_operational_valid", "GT_success"]:
        stats.append({"metric": metric, **mcnemar_counts(strict, proposed, metric)})
    for metric in ["GT_strict_valid", "GT_operational_valid"]:
        s_map = {(r["task_id"], r["seed"]): r[metric] for r in strict}
        diffs = [proposed[i][metric] - s_map[(proposed[i]["task_id"], proposed[i]["seed"])] for i in range(len(proposed))]
        ci = bootstrap_ci(diffs)
        stats.append({"metric": f"delta_{metric}_prop_minus_strict", "mean_difference": mean(diffs), "ci_low": ci["low"], "ci_high": ci["high"], "n": len(diffs)})
    stats.append({"metric": "latency_prop_minus_strict", **paired_mean_effect(strict, proposed, "simulated_latency_ms")})
    stats.append({"metric": "tool_calls_prop_minus_strict", **paired_mean_effect(strict, proposed, "tool_calls")})
    write_csv(ROOT / "summary" / "statistical_tests.csv", stats)
    warnings = []
    if all(r["GT_operational_valid"] == r["GT_strict_valid"] for r in raw_rows):
        warnings.append("WARNING: Operational validity is identical to strict conformance. Check whether operational tolerance was meaningfully defined.")
    if all(r["GT_operational_valid"] == r["GT_success"] for r in raw_rows):
        warnings.append("WARNING: Operational validity is identical to task success. The two metrics may not be independently defined.")
    prop = [r for r in summary if r["method"] == "proposed" and r["group"] == "all"]
    if prop and all(abs(float(prop[0][k]) - 1.0) < 1e-12 for k in ["SCCR", "OEPVR", "TSR", "RepairPrecision", "RepairRecall"]):
        warnings.append("WARNING: Proposed is 1.0 across all key metrics; check artificial dominance.")
    if sum(t["SCCR0_OEPV1"] for t in transitions) == 0:
        warnings.append("WARNING: No SCCR=0 & OEPV=1 cases were observed.")
    (ROOT / "summary" / "sanity_warnings.txt").write_text("\n".join(warnings) + ("\n" if warnings else ""))
    _make_figures(summary, transitions, violation_summary, cost_summary, raw_rows)
    print(f"wrote operational validity results for {len(raw_rows)} rows to {ROOT}")
    for w in warnings:
        print(w)


if __name__ == "__main__":
    main()
