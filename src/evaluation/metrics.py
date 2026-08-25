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
        unnecessary = sum(r["unnecessary_repairs"] for r in rs)
        row = {
            "method": method,
            group_by or "group": key if group_by else "all",
            "TSR": mean([r["GT_success"] for r in rs]),
            "EPVR": mean([r["GT_valid"] for r in rs]),
            "repair_precision": prec,
            "repair_recall": rec,
            "repair_f1": f1,
            "URR": unnecessary / inserted if inserted else 0.0,
            "avg_tool_calls": mean([r["tool_calls"] for r in rs]),
            "avg_agent_calls": mean([r["agent_calls"] for r in rs]),
            "avg_latency": mean([r["simulated_latency_ms"] for r in rs]),
            "avg_residual_risk": mean([r["residual_risk"] for r in rs]),
        }
        out.append(row)
    return out
