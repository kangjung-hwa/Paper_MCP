from __future__ import annotations

import math
from collections import defaultdict


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def std(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def ci95(xs):
    return 1.96 * std(xs) / math.sqrt(len(xs)) if xs else 0.0


def roc_auc(labels, scores):
    pairs = sorted(zip(scores, labels), key=lambda x: x[0])
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return 0.0
    rank_sum = sum(i + 1 for i, (_, y) in enumerate(pairs) if y)
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


def pr_auc(labels, scores):
    if not labels or sum(labels) == 0:
        return 0.0
    pairs = sorted(zip(scores, labels), reverse=True)
    tp = 0
    fp = 0
    prev_recall = 0.0
    area = 0.0
    pos = sum(labels)
    for _, y in pairs:
        if y:
            tp += 1
        else:
            fp += 1
        recall = tp / pos
        precision = tp / (tp + fp) if tp + fp else 0.0
        area += precision * max(0.0, recall - prev_recall)
        prev_recall = recall
    return area


def repair_selection_change_rate(rows):
    eligible = [r for r in rows if r.get("multi_candidate_task")]
    if not eligible:
        return 0.0
    return sum(1 for r in eligible if r.get("selection_changed_by_cost")) / len(eligible)


def summarize(rows: list[dict], group_by: str | None = None) -> list[dict]:
    groups = defaultdict(list)
    for r in rows:
        key = (r.get("method", "unknown"), r[group_by]) if group_by else (r.get("method", "unknown"), None)
        groups[key].append(r)
    out = []
    for (method, key), rs in groups.items():
        tp = sum(1 for r in rs if r["repair_decision"] and r["repair_required"])
        fp = sum(1 for r in rs if r["repair_decision"] and not r["repair_required"])
        fn = sum(1 for r in rs if not r["repair_decision"] and r["repair_required"])
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        inserted = sum(len(r.get("selected_repair", {}).get("tools", [])) if r.get("selected_repair") else 0 for r in rs)
        ourr = sum(r.get("outcome_unnecessary_repairs", r.get("unnecessary_repairs", 0)) for r in rs)
        vurr = sum(r.get("validity_unnecessary_repairs", r.get("unnecessary_repairs", 0)) for r in rs)
        labels = [int(r.get("GT_repair", r.get("repair_required", 0))) for r in rs]
        scores = [float(r.get("predicted_risk", 0.0)) for r in rs]
        row = {
            "method": method,
            group_by or "group": key if group_by else "all",
            "TSR": mean([r["GT_success"] for r in rs]),
            "EPVR": mean([r["GT_valid"] for r in rs]),
            "repair_precision": prec,
            "repair_rate": mean([1.0 if r["repair_decision"] else 0.0 for r in rs]),
            "repair_recall": rec,
            "repair_f1": f1,
            "OURR": ourr / inserted if inserted else 0.0,
            "VURR": vurr / inserted if inserted else 0.0,
            "URR": vurr / inserted if inserted else 0.0,
            "repair_auc": roc_auc(labels, scores),
            "repair_pr_auc": pr_auc(labels, scores),
            "avg_tool_calls": mean([r["tool_calls"] for r in rs]),
            "avg_agent_calls": mean([r["agent_calls"] for r in rs]),
            "avg_latency": mean([r["simulated_latency_ms"] for r in rs]),
            "avg_added_calls": mean([r.get("average_added_calls", 0) for r in rs]),
            "avg_added_latency": mean([r.get("average_added_latency", 0.0) for r in rs]),
            "avg_residual_risk": mean([r["residual_risk"] for r in rs]),
            "risk_reduction": mean([r.get("risk_reduction", 0.0) for r in rs]),
            "risk_reduction_per_added_latency": mean([r.get("risk_reduction_per_added_latency", 0.0) for r in rs]),
            "repair_selection_change_rate": repair_selection_change_rate(rs),
        }
        out.append(row)
    return out
