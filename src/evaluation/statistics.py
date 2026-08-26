from __future__ import annotations

import math
import random

from src.evaluation.metrics import ci95, mean, std


def _key(r):
    return (r.get("task_id"), r.get("seed"))


def descriptive(rows, field):
    xs = [float(r[field]) for r in rows]
    return {"mean": mean(xs), "std": std(xs), "ci95": ci95(xs), "n": len(xs)}


def mcnemar_counts(rows_a, rows_b, outcome="GT_success"):
    a = {_key(r): int(r[outcome]) for r in rows_a}
    b = {_key(r): int(r[outcome]) for r in rows_b}
    both = sorted(set(a) & set(b))
    b01 = sum(1 for k in both if a[k] == 0 and b[k] == 1)
    b10 = sum(1 for k in both if a[k] == 1 and b[k] == 0)
    stat = ((abs(b01 - b10) - 1) ** 2 / (b01 + b10)) if (b01 + b10) else 0.0
    effect = (b01 - b10) / len(both) if both else 0.0
    return {"b01": b01, "b10": b10, "chi2_cc": stat, "paired_effect": effect, "n": len(both)}


def bootstrap_ci(values, seed=42, samples=1000, alpha=0.05):
    if not values:
        return {"low": 0.0, "high": 0.0}
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        sample = [rng.choice(values) for _ in values]
        means.append(mean(sample))
    means.sort()
    lo = means[int((alpha / 2) * samples)]
    hi = means[min(samples - 1, int((1 - alpha / 2) * samples))]
    return {"low": lo, "high": hi}


def paired_mean_effect(rows_a, rows_b, field):
    a = {_key(r): float(r[field]) for r in rows_a}
    b = {_key(r): float(r[field]) for r in rows_b}
    diffs = [b[k] - a[k] for k in sorted(set(a) & set(b))]
    return {"mean_difference": mean(diffs), "std_difference": std(diffs), "n": len(diffs)}
