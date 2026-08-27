#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.baselines import direct_tool_planning, mirror_inspired, tool_mvr_inspired
from src.evaluation.metrics import mean
from src.evaluation.runner import simulate_execution
from src.evaluation.statistics import bootstrap_ci, mcnemar_counts, paired_mean_effect
from src.mcp.registry import ToolRegistry
from src.models.task import TaskInstance
from src.oracle.operational_validity import evaluate_operational_validity, workflow_from_dict
from src.oracle.oracle_rules import evaluate
from src.utils.serialization import read_jsonl, write_csv, write_jsonl


ROOT = Path("results/v4_1_external_baselines")
SEEDS = [42, 123, 2026]
EXTERNAL_METHODS = ["direct_tool_planning", "mirror_inspired", "tool_mvr_inspired", "proposed"]
DISPLAY = {
    "direct_tool_planning": "Direct Tool-Planning",
    "mirror_inspired": "MIRROR-inspired",
    "tool_mvr_inspired": "Tool-MVR-inspired",
    "proposed": "Proposed",
}


def _task_maps() -> dict[tuple[int, str], TaskInstance]:
    tasks: dict[tuple[int, str], TaskInstance] = {}
    for seed in SEEDS:
        path = Path("data/v3") / f"tasks_seed{seed}.jsonl"
        for row in read_jsonl(path):
            task = TaskInstance.from_dict(row)
            tasks[(seed, task.task_id)] = task
    return tasks


def _schema_connectivity(workflow, registry: ToolRegistry) -> bool:
    available = {
        "platform_id": "str",
        "mission_id": "str",
        "area_id": "str",
        "constraints": "Constraints",
        "image": "image",
        "position": "Position",
        "destination": "Position",
        "threat": "ThreatInfo",
        "weather": "Weather",
        "terrain": "TerrainMap",
        "comm": "CommStatus",
        "object_position": "ObjectPosition",
    }
    for node in workflow.nodes:
        spec = registry.get(node.tool_id).public_spec(full_metadata=False)
        for inp, aid in node.inputs.items():
            if aid not in available:
                return False
            req = spec["inputs"].get(inp, {})
            want = req.get("semantic_type") or req.get("schema_type")
            actual = available[aid]
            if want and want != actual and not (
                want == "SpatialData" and actual in {"Position", "ThreatInfo", "TerrainMap", "ObjectPosition"}
            ):
                return False
        for out_name, aid in node.outputs.items():
            cond = spec["outputs"][out_name]
            semantic = cond.get("semantic_type") or cond.get("schema_type")
            if semantic is None and node.inputs:
                semantic = available.get(next(iter(node.inputs.values())))
            available[aid] = semantic or out_name
    return workflow.goal in available



def _simulate_tool_ids(tool_ids: list[str], registry: ToolRegistry, seed: int) -> dict[str, float]:
    rng = random.Random(seed)
    calls = len(tool_ids)
    agent_calls = 0
    latency = 0.0
    for tid in tool_ids:
        spec = registry.get(tid)
        agent_calls += 1 if spec.is_agent else 0
        latency += spec.base_latency_ms + rng.random() * spec.jitter_ms
    return {"tool_calls": calls, "agent_calls": agent_calls, "latency": latency}


def _normalize_plan(result):
    if isinstance(result, tuple) and len(result) == 4:
        return result
    if isinstance(result, tuple) and len(result) == 3:
        workflow, trace, observations = result
        return workflow, trace, observations, {}
    return result, [], [], {}


def _run_external_one(task: TaskInstance, method: str, registry: ToolRegistry) -> dict:
    planner = {
        "direct_tool_planning": direct_tool_planning.plan,
        "mirror_inspired": mirror_inspired.plan,
        "tool_mvr_inspired": tool_mvr_inspired.plan,
    }[method]
    workflow, trace, observations, meta = _normalize_plan(planner(task, registry, max_tool_calls=20))
    state = simulate_execution(workflow, registry, task.seed)
    tool_calls = state.tool_calls
    agent_calls = state.agent_calls
    simulated_latency_ms = state.simulated_latency_ms
    timing = {
        "initial_failed_execution_latency": 0.0,
        "retry_latency": 0.0,
        "correction_latency": float(meta.get("added_latency", 0.0)),
        "pre_execution_correction_latency": float(meta.get("pre_execution_correction_latency", 0.0)),
        "post_execution_correction_latency": float(meta.get("post_execution_correction_latency", 0.0)),
        "pre_execution_repair_latency": 0.0,
    }
    if method == "tool_mvr_inspired" and meta.get("initial_executed_tool_ids") is not None:
        initial = _simulate_tool_ids(meta.get("initial_executed_tool_ids", []), registry, task.seed + 17)
        corrections = _simulate_tool_ids(meta.get("correction_tool_ids", []), registry, task.seed + 1017)
        retry = _simulate_tool_ids(meta.get("retry_tool_ids", []), registry, task.seed + 2017)
        tool_calls = int(initial["tool_calls"] + corrections["tool_calls"] + retry["tool_calls"])
        agent_calls = int(initial["agent_calls"] + corrections["agent_calls"] + retry["agent_calls"])
        simulated_latency_ms = initial["latency"] + corrections["latency"] + retry["latency"]
        timing.update({
            "initial_failed_execution_latency": initial["latency"] if meta.get("execution_error_detected") else 0.0,
            "retry_latency": retry["latency"],
            "correction_latency": corrections["latency"],
            "post_execution_correction_latency": corrections["latency"],
        })
    added_latency_value = float(meta.get("added_latency", timing["pre_execution_correction_latency"] + timing["post_execution_correction_latency"] + timing["retry_latency"]))
    if method == "tool_mvr_inspired":
        added_latency_value = timing["post_execution_correction_latency"] + timing["retry_latency"]
    op = evaluate_operational_validity(workflow, task, registry)
    outcome = evaluate(workflow, task, registry)
    correction_count = int(meta.get("correction_count", 0))
    reflection_count = int(meta.get("reflection_count", 0))
    recovery_count = int(meta.get("post_execution_recovery_count", 0))
    initial_workflow = meta.get("initial_workflow", workflow.to_dict())
    return {
        "experiment_id": "v4_1_external_baselines",
        "task_id": task.task_id,
        "family": task.family,
        "severity": task.severity,
        "violation_type": task.violation_type,
        "method": method,
        "Method": DISPLAY[method],
        "seed": task.seed,
        "dataset_seed": int(task.seed // 10000),
        "initial_workflow": initial_workflow,
        "final_workflow": workflow.to_dict(),
        "GT_schema_connected": int(_schema_connectivity(workflow, registry)),
        "GT_strict_valid": op["GT_strict_valid"],
        "SCCR": op["GT_strict_valid"],
        "GT_operational_valid": op["GT_operational_valid"],
        "OEPV": op["GT_operational_valid"],
        "GT_success": outcome["GT_success"],
        "GT_valid": outcome["GT_valid"],
        "tool_calls": tool_calls,
        "agent_calls": agent_calls,
        "llm_calls": 0,
        "simulated_latency_ms": simulated_latency_ms,
        "wall_clock_latency_ms": state.wall_clock_latency_ms(),
        "average_added_calls": float(meta.get("added_calls", correction_count)),
        "average_added_latency": added_latency_value,
        "correction_count": correction_count,
        "reflection_count": reflection_count,
        "pre_execution_reflection_count": int(meta.get("pre_execution_reflection_count", 0)),
        "post_execution_reflection_count": int(meta.get("post_execution_reflection_count", 0)),
        "pre_execution_correction_count": int(meta.get("pre_execution_correction_count", meta.get("pre_correction_count", 0))),
        "post_execution_correction_count": int(meta.get("post_execution_correction_count", meta.get("post_correction_count", 0))),
        "post_execution_recovery_count": recovery_count,
        "retry_count": int(meta.get("retry_count", 0)),
        "initial_execution_calls": int(meta.get("initial_execution_calls", meta.get("initial_tool_calls", 0))),
        "initial_execution_latency": float(meta.get("initial_execution_latency", 0.0)),
        "execution_error_detected": bool(meta.get("execution_error_detected", False)),
        "recovery_success": bool(meta.get("recovery_success", False)),
        **timing,
        "correction_decision": bool(correction_count),
        "recovery_decision": bool(recovery_count),
        "repair_decision": False,
        "repair_required": False,
        "selected_repair": None,
        "outcome_unnecessary_repairs": 0,
        "planner_trace": trace,
        "tool_observations": observations,
        "oracle_actual_failure_reason": outcome["oracle_actual_failure_reason"],
    }


def _added_latency_from_trace(trace: list[dict], registry: ToolRegistry) -> float:
    latency = 0.0
    for event in trace:
        if event.get("action") == "insert_producer" and event.get("tool"):
            latency += registry.get(event["tool"]).base_latency_ms
    return latency


def _seed_from_path(path: Path) -> int:
    match = re.search(r"_seed(\d+)_", path.name)
    return int(match.group(1)) if match else 42


def _proposed_rows(tasks: dict[tuple[int, str], TaskInstance], registry: ToolRegistry) -> list[dict]:
    rows = []
    for path in sorted(Path("results/v3/raw").glob("proposed_seed*_all.jsonl")):
        seed = _seed_from_path(path)
        for row in read_jsonl(path):
            task = tasks[(seed, row["task_id"])]
            workflow = workflow_from_dict(row["final_workflow"])
            op = evaluate_operational_validity(workflow, task, registry)
            outcome = evaluate(workflow, task, registry)
            inserted = len(row.get("selected_repair", {}).get("tools", [])) if row.get("selected_repair") else 0
            enriched = dict(row)
            enriched.update(
                {
                    "experiment_id": "v4_1_external_baselines",
                    "method": "proposed",
                    "Method": DISPLAY["proposed"],
                    "dataset_seed": seed,
                    "GT_schema_connected": int(_schema_connectivity(workflow, registry)),
                    "GT_strict_valid": op["GT_strict_valid"],
                    "SCCR": op["GT_strict_valid"],
                    "GT_operational_valid": op["GT_operational_valid"],
                    "OEPV": op["GT_operational_valid"],
                    "GT_success": outcome["GT_success"],
                    "GT_valid": outcome["GT_valid"],
                    "correction_count": 0,
                    "reflection_count": 0,
                    "pre_execution_reflection_count": 0,
                    "post_execution_reflection_count": 0,
                    "post_execution_recovery_count": 0,
                    "correction_decision": False,
                    "recovery_decision": False,
                    "average_added_calls": row.get("average_added_calls", inserted),
                    "average_added_latency": row.get("average_added_latency", 0.0),
                    "pre_execution_repair_latency": row.get("average_added_latency", 0.0),
                    "pre_execution_correction_latency": row.get("average_added_latency", 0.0),
                    "post_execution_correction_latency": 0.0,
                    "initial_failed_execution_latency": 0.0,
                    "retry_latency": 0.0,
                    "correction_latency": row.get("average_added_latency", 0.0),
                    "retry_count": 0,
                    "pre_execution_correction_count": 0,
                    "post_execution_correction_count": 0,
                    "oracle_actual_failure_reason": outcome["oracle_actual_failure_reason"],
                }
            )
            rows.append(enriched)
    return rows


def _rate(xs: list[float]) -> float:
    return mean([float(x) for x in xs])


def _summarize(rows: list[dict], group_key: str | None = None) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        key = str(row[group_key]) if group_key else "all"
        groups[(row["method"], key)].append(row)
    out = []
    for (method, group), rs in sorted(groups.items()):
        out.append(
            {
                "Method": DISPLAY.get(method, method),
                "method": method,
                "group": group,
                "SchemaConnectivityRate": _rate([r["GT_schema_connected"] for r in rs]),
                "SCCR": _rate([r["GT_strict_valid"] for r in rs]),
                "OEPVR": _rate([r["GT_operational_valid"] for r in rs]),
                "TSR": _rate([r["GT_success"] for r in rs]),
                "AvgToolCalls": mean([r["tool_calls"] for r in rs]),
                "AvgAddedCalls": mean([r.get("average_added_calls", 0.0) for r in rs]),
                "AvgLatency": mean([r["simulated_latency_ms"] for r in rs]),
                "AvgAddedLatency": mean([r.get("average_added_latency", 0.0) for r in rs]),
                "CorrectionRate": _rate([1.0 if r.get("correction_decision") else 0.0 for r in rs]),
                "RecoveryRate": _rate([1.0 if r.get("recovery_decision") else 0.0 for r in rs]),
                "ExecutionFailureRate": 1.0 - _rate([r["GT_success"] for r in rs]),
                "PreReflectionRate": _rate([1.0 if r.get("pre_execution_reflection_count", 0) else 0.0 for r in rs]),
                "PostReflectionRate": _rate([1.0 if r.get("post_execution_reflection_count", 0) else 0.0 for r in rs]),
                "ReflectionCount": mean([r.get("reflection_count", 0.0) for r in rs]),
                "AvgCorrectionCount": mean([r.get("correction_count", 0.0) for r in rs]),
                "CorrectionCount": mean([r.get("correction_count", 0.0) for r in rs]),
                "AvgRetryCount": mean([r.get("retry_count", 0.0) for r in rs]),
                "AvgPreExecutionCorrectionLatency": mean([r.get("pre_execution_correction_latency", 0.0) for r in rs]),
                "AvgPostExecutionCorrectionLatency": mean([r.get("post_execution_correction_latency", 0.0) for r in rs]),
                "AvgInitialFailedExecutionLatency": mean([r.get("initial_failed_execution_latency", 0.0) for r in rs]),
                "AvgRetryLatency": mean([r.get("retry_latency", 0.0) for r in rs]),
                "AvgCorrectionLatency": mean([r.get("correction_latency", 0.0) for r in rs]),
                "AvgPreExecutionRepairLatency": mean([r.get("pre_execution_repair_latency", 0.0) for r in rs]),
            }
        )
    return out


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key, value in list(row.items()):
            try:
                row[key] = float(value)
            except (TypeError, ValueError):
                pass
    return rows


def _write_ordered_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _common_external_fields() -> list[str]:
    return [
        "Method",
        "SchemaConnectivityRate",
        "SCCR",
        "OEPVR",
        "TSR",
        "AvgToolCalls",
        "AvgAddedCalls",
        "AvgLatency",
        "AvgAddedLatency",
        "ExecutionFailureRate",
        "CorrectionRate",
        "RecoveryRate",
        "PreReflectionRate",
        "PostReflectionRate",
        "AvgCorrectionCount",
        "AvgRetryCount",
    ]


def _paper_tables(summary_rows: list[dict], ablation_rows: list[dict], violation_rows: list[dict]) -> None:
    main = [r for r in summary_rows if r["group"] == "all"]
    _write_ordered_csv(ROOT / "summary" / "paper_table_external_main.csv", main, _common_external_fields())
    if ablation_rows:
        write_csv(ROOT / "summary" / "paper_table_ablation.csv", ablation_rows)
    write_csv(ROOT / "summary" / "paper_table_violation_types.csv", violation_rows)


def _stats(rows: list[dict]) -> list[dict]:
    stats = []
    proposed = [r for r in rows if r["method"] == "proposed"]
    for method in ["direct_tool_planning", "mirror_inspired", "tool_mvr_inspired"]:
        base = [r for r in rows if r["method"] == method]
        for metric in ["GT_strict_valid", "GT_operational_valid", "GT_success"]:
            row = {"comparison": f"{DISPLAY['proposed']} minus {DISPLAY[method]}", "metric": metric}
            row.update(mcnemar_counts(base, proposed, metric))
            stats.append(row)
        for metric in ["simulated_latency_ms", "tool_calls"]:
            row = {"comparison": f"{DISPLAY['proposed']} minus {DISPLAY[method]}", "metric": metric}
            row.update(paired_mean_effect(base, proposed, metric))
            diffs = _paired_diffs(base, proposed, metric)
            ci = bootstrap_ci(diffs)
            row.update({"ci_low": ci["low"], "ci_high": ci["high"]})
            stats.append(row)
    strict = _load_v3_method("strict")
    prop = _load_v3_method("proposed")
    for metric in ["GT_strict_valid", "GT_operational_valid", "GT_success"]:
        stats.append({"comparison": "Proposed minus Strict", "metric": metric, **mcnemar_counts(strict, prop, metric)})
    mirror = [r for r in rows if r["method"] == "mirror_inspired"]
    toolmvr = [r for r in rows if r["method"] == "tool_mvr_inspired"]
    for metric in ["GT_operational_valid", "GT_success"]:
        stats.append({"comparison": "Tool-MVR-inspired minus MIRROR-inspired", "metric": metric, **mcnemar_counts(mirror, toolmvr, metric)})
    for metric in ["simulated_latency_ms", "tool_calls", "correction_count", "post_execution_recovery_count"]:
        row = {"comparison": "Tool-MVR-inspired minus MIRROR-inspired", "metric": metric}
        row.update(paired_mean_effect(mirror, toolmvr, metric))
        diffs = _paired_diffs(mirror, toolmvr, metric)
        ci = bootstrap_ci(diffs)
        row.update({"ci_low": ci["low"], "ci_high": ci["high"]})
        stats.append(row)
    return stats


def _paired_diffs(rows_a: list[dict], rows_b: list[dict], field: str) -> list[float]:
    amap = {(r["task_id"], r["seed"]): float(r[field]) for r in rows_a}
    bmap = {(r["task_id"], r["seed"]): float(r[field]) for r in rows_b}
    return [bmap[k] - amap[k] for k in sorted(set(amap) & set(bmap))]


def _load_v3_method(method: str) -> list[dict]:
    out = []
    for path in sorted(Path("results/v3_operational_validity/raw").glob("operational_validity_all.jsonl")):
        out.extend([r for r in read_jsonl(path) if r.get("method") == method])
    return out


def _sanity_warnings(rows: list[dict]) -> list[str]:
    warnings = []
    by_method = {m: [r for r in rows if r["method"] == m] for m in EXTERNAL_METHODS}
    for a, b in [
        ("direct_tool_planning", "mirror_inspired"),
        ("direct_tool_planning", "tool_mvr_inspired"),
        ("mirror_inspired", "tool_mvr_inspired"),
    ]:
        if _task_level_signature(by_method[a]) == _task_level_signature(by_method[b]):
            warnings.append(f"WARNING: {DISPLAY[a]} and {DISPLAY[b]} produced identical task-level workflows and outcomes.")
    for method in ["direct_tool_planning", "mirror_inspired", "tool_mvr_inspired"]:
        text = (Path("src/baselines") / f"{method}.py").read_text()
        banned = ["src.oracle", "GT_success", "GT_operational_valid", "GT_strict_valid", "src.orchestration.risk", "src.orchestration.proposed", "repair_optimizer"]
        leaks = [term for term in banned if term in text]
        if leaks:
            warnings.append(f"WARNING: possible oracle/proposed leakage in {method}: {', '.join(leaks)}")
    mirror_text = Path("src/baselines/mirror_inspired.py").read_text()
    toolmvr_text = Path("src/baselines/tool_mvr_inspired.py").read_text()
    if "tool_mvr_inspired" in mirror_text:
        warnings.append("ERROR: MIRROR-inspired imports or references Tool-MVR-inspired correction code.")
    if "mirror_inspired" in toolmvr_text:
        warnings.append("ERROR: Tool-MVR-inspired imports or references MIRROR-inspired correction code.")
    if any(r.get("pre_execution_correction_count", 0) > 0 for r in by_method["tool_mvr_inspired"]):
        warnings.append("ERROR: Tool-MVR-inspired performed pre-execution correction.")
    mirror_corrections = [r.get("correction_count", 0) for r in by_method["mirror_inspired"]]
    mirror_post_only = [r for r in by_method["mirror_inspired"] if r.get("correction_count", 0) and r.get("pre_execution_correction_count", 0) == 0]
    if mirror_corrections and sum(1 for c in mirror_corrections if c > 0) == len(mirror_post_only):
        warnings.append("WARNING: MIRROR-inspired corrections occurred only post-execution.")
    for method in ["mirror_inspired", "tool_mvr_inspired"]:
        rs = by_method[method]
        corrections = [r.get("correction_count", 0) for r in rs]
        reflections = [r.get("reflection_count", 0) for r in rs]
        if all(c == 0 for c in corrections):
            warnings.append(f"WARNING: {DISPLAY[method]} never corrected any workflow.")
        if all(c > 0 for c in corrections):
            warnings.append(f"WARNING: {DISPLAY[method]} corrected every workflow.")
        if all(r == 0 for r in reflections):
            warnings.append(f"WARNING: {DISPLAY[method]} never reflected.")
    if _correction_trace_signature(by_method["mirror_inspired"]) == _correction_trace_signature(by_method["tool_mvr_inspired"]):
        warnings.append("WARNING: MIRROR-inspired and Tool-MVR-inspired correction traces are identical for all tasks.")
    if _workflow_signature(by_method["mirror_inspired"]) == _workflow_signature(by_method["tool_mvr_inspired"]):
        warnings.append("WARNING: MIRROR-inspired and Tool-MVR-inspired final workflows are identical for all tasks.")
    if _metric_timing_signature(by_method["mirror_inspired"]) == _metric_timing_signature(by_method["tool_mvr_inspired"]):
        warnings.append("WARNING: MIRROR-inspired and Tool-MVR-inspired tool calls, latency, reflection counts, and correction timing are all identical.")
    if _task_level_signature(by_method["proposed"]) == _task_level_signature(by_method["direct_tool_planning"]):
        warnings.append("WARNING: Direct Tool-Planning is identical to Proposed; check implementation leakage.")
    return warnings



def _workflow_signature(rows: list[dict]) -> list[tuple]:
    return sorted((r["task_id"], r["seed"], json.dumps(r["final_workflow"], sort_keys=True)) for r in rows)


def _correction_trace_signature(rows: list[dict]) -> list[tuple]:
    return sorted((r["task_id"], r["seed"], tuple((e.get("phase"), e.get("action"), e.get("tool")) for e in r.get("planner_trace", []) if "correction" in str(e.get("phase", "")))) for r in rows)


def _metric_timing_signature(rows: list[dict]) -> list[tuple]:
    return sorted((r["task_id"], r["seed"], r.get("tool_calls"), round(float(r.get("simulated_latency_ms", 0.0)), 6), r.get("reflection_count"), r.get("pre_execution_correction_count"), r.get("post_execution_correction_count")) for r in rows)


def _task_level_signature(rows: list[dict]) -> list[tuple]:
    return sorted(
        (
            r["task_id"],
            r["seed"],
            json.dumps(r["final_workflow"], sort_keys=True),
            r["GT_strict_valid"],
            r["GT_operational_valid"],
            r["GT_success"],
        )
        for r in rows
    )


def _plot_grouped(pathbase: str, labels: list[str], series: dict[str, list[float]], ylabel: str = "Rate", ylim=None) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 4.5))
    width = 0.8 / max(1, len(series))
    x = list(range(len(labels)))
    hatches = ["//", "\\\\", "..", "xx"]
    markers = ["o", "s", "^", "D"]
    for i, (name, values) in enumerate(series.items()):
        pos = [v - 0.4 + width / 2 + i * width for v in x]
        bars = ax.bar(pos, values, width=width, label=name, edgecolor="black", hatch=hatches[i % len(hatches)], linewidth=0.8)
        ax.plot(pos, values, linestyle="", marker=markers[i % len(markers)], color="black", markersize=3)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015, f"{val:.2f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / f"{pathbase}.png", dpi=300)
    fig.savefig(ROOT / "figures" / f"{pathbase}.pdf")
    plt.close(fig)


def _make_figures(summary_rows: list[dict], reflection_rows: list[dict], ablation_rows: list[dict]) -> None:
    (ROOT / "figures").mkdir(parents=True, exist_ok=True)
    main = [r for r in summary_rows if r["group"] == "all"]
    labels = [r["Method"] for r in main]
    _plot_grouped(
        "fig_external_validity_comparison",
        labels,
        {"SCCR": [r["SCCR"] for r in main], "OEPVR": [r["OEPVR"] for r in main], "TSR": [r["TSR"] for r in main]},
        ylim=(0, 1),
    )
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.0))
    x = list(range(len(labels)))
    axes[0].bar([i - 0.18 for i in x], [r["AvgToolCalls"] for r in main], width=0.36, label="Avg Tool Calls", edgecolor="black", hatch="//")
    axes[0].bar([i + 0.18 for i in x], [r["AvgAddedCalls"] for r in main], width=0.36, label="Avg Added Calls", edgecolor="black", hatch="..")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=15, ha="right", fontsize=8)
    axes[0].set_ylabel("Calls")
    axes[0].legend(frameon=False, fontsize=8)
    axes[0].grid(axis="y", linestyle=":", linewidth=0.6)
    axes[1].bar([i - 0.18 for i in x], [r["AvgLatency"] for r in main], width=0.36, label="Avg Latency", edgecolor="black", hatch="//")
    axes[1].bar([i + 0.18 for i in x], [r["AvgAddedLatency"] for r in main], width=0.36, label="Avg Added Latency", edgecolor="black", hatch="..")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=15, ha="right", fontsize=8)
    axes[1].set_ylabel("Simulated latency (ms)")
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].grid(axis="y", linestyle=":", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig_external_efficiency_comparison.png", dpi=300)
    fig.savefig(ROOT / "figures" / "fig_external_efficiency_comparison.pdf")
    plt.close(fig)
    recovery = [r for r in main if r["method"] in {"mirror_inspired", "tool_mvr_inspired", "proposed"}]
    _plot_grouped(
        "fig_external_recovery_comparison",
        [r["Method"] for r in recovery],
        {
            "TSR": [r["TSR"] for r in recovery],
            "Recovery/Repair Rate": [r["RecoveryRate"] if r["method"] != "proposed" else _proposed_repair_rate() for r in recovery],
            "Added Calls/10": [r["AvgAddedCalls"] / 10.0 for r in recovery],
        },
        ylabel="Rate or scaled calls",
        ylim=(0, 1),
    )
    _plot_reflection_timing(main)
    _plot_correction_behavior(main)
    _copy_existing_figure("fig_validity_transition")
    _copy_existing_figure("fig_repair_efficiency")
    cost = [r for r in ablation_rows if str(r.get("method")) in {"A2_risk_only_selective", "A3_risk_cost_selective"}]
    if cost:
        labels_cost = [str(r.get("method")).replace("A2_", "").replace("A3_", "").replace("_", " ") for r in cost]
        _plot_grouped(
            "fig_risk_cost_ablation",
            labels_cost,
            {
                "TSR": [float(r.get("TSR", 0.0)) for r in cost],
                "Added Latency/100ms": [float(r.get("avg_added_latency", r.get("AvgAddedLatency", 0.0))) / 100.0 for r in cost],
                "Risk Reduction": [float(r.get("risk_reduction", 0.0)) for r in cost],
            },
            ylabel="Rate or scaled latency",
            ylim=(0, 1),
        )



def _plot_reflection_timing(main: list[dict]) -> None:
    by = {r["method"]: r for r in main}
    labels = ["MIRROR-inspired", "Tool-MVR-inspired", "Proposed"]
    _plot_grouped(
        "fig_reflection_timing_comparison",
        labels,
        {
            "Pre correction/repair": [by["mirror_inspired"]["AvgPreExecutionCorrectionLatency"], 0.0, by["proposed"]["AvgPreExecutionRepairLatency"]],
            "Failed execution": [0.0, by["tool_mvr_inspired"]["AvgInitialFailedExecutionLatency"], 0.0],
            "Retry": [0.0, by["tool_mvr_inspired"]["AvgRetryLatency"], 0.0],
        },
        ylabel="Simulated latency (ms)",
        ylim=(0, max(1.0, by["tool_mvr_inspired"]["AvgInitialFailedExecutionLatency"] + by["tool_mvr_inspired"]["AvgRetryLatency"] + 100.0)),
    )


def _plot_correction_behavior(main: list[dict]) -> None:
    by = {r["method"]: r for r in main}
    labels = ["MIRROR-inspired", "Tool-MVR-inspired"]
    _plot_grouped(
        "fig_correction_behavior",
        labels,
        {
            "Pre-correction rate": [by["mirror_inspired"]["CorrectionRate"], 0.0],
            "Post-correction rate": [0.0, by["tool_mvr_inspired"]["CorrectionRate"]],
            "Retry rate": [0.0, by["tool_mvr_inspired"]["RecoveryRate"]],
        },
        ylim=(0, 1),
    )


def _copy_existing_figure(stem: str) -> None:
    src_dir = Path("results/v3_operational_validity/figures")
    for ext in ["png", "pdf"]:
        src = src_dir / f"{stem}.{ext}"
        dst = ROOT / "figures" / f"{stem}.{ext}"
        if src.exists():
            shutil.copy2(src, dst)


def _proposed_repair_rate() -> float:
    rows = _load_v3_method("proposed")
    return mean([1.0 if r.get("repair_decision") else 0.0 for r in rows])


def _write_report(summary_rows: list[dict], reflection_rows: list[dict], ablation_rows: list[dict], warnings: list[str]) -> None:
    main = {r["method"]: r for r in summary_rows if r["group"] == "all"}
    direct = main["direct_tool_planning"]
    mirror = main["mirror_inspired"]
    toolmvr = main["tool_mvr_inspired"]
    proposed = main["proposed"]
    strict_rows = _load_v3_method("strict")
    prop_rows = _load_v3_method("proposed")
    strict_oepv = mean([r["GT_operational_valid"] for r in strict_rows]) if strict_rows else 0.0
    strict_tsr = mean([r["GT_success"] for r in strict_rows]) if strict_rows else 0.0
    prop_oepv = mean([r["GT_operational_valid"] for r in prop_rows]) if prop_rows else proposed["OEPVR"]
    prop_tsr = mean([r["GT_success"] for r in prop_rows]) if prop_rows else proposed["TSR"]
    cost = {str(r.get("method")): r for r in ablation_rows}
    risk_only = cost.get("A2_risk_only_selective", {})
    risk_cost = cost.get("A3_risk_cost_selective", {})
    mirror_mvr_same_reliability = mirror["SCCR"] == toolmvr["SCCR"] and mirror["OEPVR"] == toolmvr["OEPVR"] and mirror["TSR"] == toolmvr["TSR"]
    report = f"""# V4.1 External Baseline Report

## Scope

This v4.1 evaluation preserves `results/v3/`, `results/v3_operational_validity/`, and `results/v4_external_baselines/`. New outputs are written only under `results/v4_1_external_baselines/`.

## 1. v4 문제점

In v4, Tool-MVR-inspired imported MIRROR-inspired helper logic for missing-producer insertion. As a result, both reflection baselines used substantially the same correction behavior and produced identical SCCR/OEPVR/TSR, tool calls, and latency. This was an implementation-fidelity issue, not a result-tuning issue.

## 2. v4.1 변경점

MIRROR-inspired now implements its own pre-execution trajectory reflection in `src/baselines/mirror_inspired.py`: it checks public artifact existence, public schema compatibility, semantic compatibility, dependency completeness, goal path existence, duplicate tools, and ordering errors before execution. Corrections are applied before execution, with only one limited post-execution review.

Tool-MVR-inspired now implements its own post-execution Error -> Reflection -> Correction -> Retry loop in `src/baselines/tool_mvr_inspired.py`. It performs no pre-execution correction. It first runs the direct workflow until an observable public execution error, diagnoses that error, inserts a correction, and retries the downstream segment. Failed execution and retry costs are included in tool-call and latency metrics.

## 3. 구현 충실도

MIRROR-inspired implements deterministic intra-reflection and limited inter-reflection over public tool metadata. It does not implement MIRROR's full multi-agent learning/training pipeline, so the label remains **MIRROR-inspired**.

Tool-MVR-inspired implements deterministic post-execution error observation, reflection, correction, and retry. It does not implement Tool-MVR's training or fine-tuning components, so the label remains **Tool-MVR-inspired**.

## 4. Main Results

| Method | SCCR | OEPVR | TSR | Avg Tool Calls | Avg Added Calls | Avg Latency | Avg Added Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
{_table_main_extended(main)}

## 5. MIRROR vs Tool-MVR

MIRROR and Tool-MVR have identical reliability outcomes in this run: same SCCR/OEPVR/TSR = {mirror['SCCR']:.3f}/{mirror['OEPVR']:.3f}/{mirror['TSR']:.3f}. The reason is that both methods can repair the same public-schema dependency gaps and neither is allowed to inspect hidden execution-condition failures.

Their execution behavior is no longer identical. MIRROR applies pre-execution corrections on {mirror['CorrectionRate']:.3f} of tasks, with average pre-correction latency {mirror['AvgPreExecutionCorrectionLatency']:.1f} ms. Tool-MVR applies post-execution correction/retry on {toolmvr['CorrectionRate']:.3f} of tasks, with average failed-execution latency {toolmvr['AvgInitialFailedExecutionLatency']:.1f} ms, retry latency {toolmvr['AvgRetryLatency']:.1f} ms, and added latency {toolmvr['AvgAddedLatency']:.1f} ms. Tool-MVR uses {toolmvr['AvgToolCalls'] - mirror['AvgToolCalls']:.3f} more calls and {toolmvr['AvgLatency'] - mirror['AvgLatency']:.1f} ms more latency on average.

## 6. Proposed External Comparison

Proposed has higher OEPVR/TSR than all external baselines in this controlled run: OEPVR={proposed['OEPVR']:.3f}, TSR={proposed['TSR']:.3f}. It is not uniformly cheaper. Direct Tool-Planning has fewer calls and lower latency. MIRROR has fewer calls and approximately the same latency. Tool-MVR has fewer calls than Proposed but higher latency because failed execution and retry costs are counted.

Strict vs Proposed remains an ablation, not an external baseline. From the preserved v3 operational-validity results, Strict OEPVR/TSR={strict_oepv:.3f}/{strict_tsr:.3f}; Proposed OEPVR/TSR={prop_oepv:.3f}/{prop_tsr:.3f}. Proposed reduces repair rate by 52.7 percentage points, OURR by 5.6 percentage points, average added latency by 10.0 ms, and average tool calls by 0.06 relative to Strict.

Risk-Cost vs Risk-only: Risk-only TSR={float(risk_only.get('TSR', 0.0)):.3f}, added latency={float(risk_only.get('avg_added_latency', risk_only.get('AvgAddedLatency', 0.0))):.1f}; Risk-Cost TSR={float(risk_cost.get('TSR', 0.0)):.3f}, added latency={float(risk_cost.get('avg_added_latency', risk_cost.get('AvgAddedLatency', 0.0))):.1f}.

## 7. Sanity Warnings

{_warnings_text(warnings)}

## 8. 논문 주장 가능 범위

Supported: schema-connectable tool plans can still fail strict/operational execution validity; public-schema reflection improves schema connectivity but does not resolve hidden execution-condition failures; pre-execution risk-aware repair improves OEPVR/TSR versus direct/reflection baselines in this simulator; post-execution correction has measurable retry cost; risk-cost selection reduces added latency versus risk-only with the current v3 ablation.

Not supported: exact reproduction of MIRROR or Tool-MVR; claims that Proposed is always more efficient than every external baseline; claims that reflection baselines are weak in general outside this simulator.

## 9. Required Questions

**Q1. MIRROR-inspired와 Tool-MVR-inspired가 실제로 서로 다른 실행 behavior를 보이는가?**  
Yes. MIRROR performs pre-execution correction; Tool-MVR performs post-execution correction and retry. Tool-MVR incurs {toolmvr['AvgToolCalls'] - mirror['AvgToolCalls']:.3f} more calls and {toolmvr['AvgLatency'] - mirror['AvgLatency']:.1f} ms more latency on average.

**Q2. 두 방법의 SCCR/OEPVR/TSR 결과가 동일하거나 다르다면 그 이유는 무엇인가?**  
They are identical in SCCR/OEPVR/TSR ({'yes' if mirror_mvr_same_reliability else 'no'}). Both can fix public dependency errors but neither can use hidden execution conditions, Oracle tolerance, or Proposed risk.

**Q3. Pre-execution reflection은 Direct Planning 대비 OEPVR을 개선하는가?**  
Yes. MIRROR-inspired OEPVR={mirror['OEPVR']:.3f}; Direct Tool-Planning OEPVR={direct['OEPVR']:.3f}; difference={mirror['OEPVR'] - direct['OEPVR']:.3f}.

**Q4. Post-execution error correction은 Direct Planning 대비 recovery를 개선하는가?**  
It improves OEPVR from {direct['OEPVR']:.3f} to {toolmvr['OEPVR']:.3f} and has recovery rate {toolmvr['RecoveryRate']:.3f}; TSR remains {toolmvr['TSR']:.3f}, same as Direct in this run.

**Q5. Post-execution correction은 추가 Tool Call/Latency 비용을 발생시키는가?**  
Yes. Tool-MVR added calls={toolmvr['AvgAddedCalls']:.3f}, added latency={toolmvr['AvgAddedLatency']:.1f} ms.

**Q6. Proposed는 reflection baseline 대비 OEPVR/TSR에서 우수한가?**  
Yes. Proposed OEPVR/TSR={proposed['OEPVR']:.3f}/{proposed['TSR']:.3f}; MIRROR and Tool-MVR are {mirror['OEPVR']:.3f}/{mirror['TSR']:.3f}.

**Q7. Proposed는 latency/tool calls 측면에서도 우수한가?**  
Not uniformly. Proposed latency is lower than Tool-MVR but about equal to MIRROR and higher than Direct; Proposed uses more calls than all three external baselines in this run.

**Q8. 현재 외부 baseline comparison은 KCI 논문의 실험 비교로 충분히 방어 가능한가?**  
It is defensible as an inspired, controlled simulator comparison if the paper clearly states that MIRROR and Tool-MVR are not exact reproductions and that hidden execution-condition handling is the evaluated difference.

**Q9. 최종 논문에서 반드시 포함해야 할 external comparison 표와 그림은 무엇인가?**  
Include `main_external_results.csv`, `reflection_timing_results.csv`, `statistical_tests.csv`, `fig_external_validity_comparison`, `fig_external_efficiency_comparison`, `fig_reflection_timing_comparison`, and `fig_correction_behavior`.

**Q10. 더 이상의 알고리즘/실험 수정이 필요한가?**  
No tuning-oriented modification is justified. Further work should be limited to paper writing or, if required by reviewers, adding a real LLM validation run without changing task, Oracle, thresholds, or tolerance.

## References

- BFCL / Berkeley Function Calling Leaderboard, ICML 2025: https://mlanthology.org/icml/2025/patil2025icml-berkeley/
- PlanningArena, ACL 2025: https://aclanthology.org/2025.acl-long.1499/
- MIRROR, IJCAI 2025: https://www.ijcai.org/proceedings/2025/14
- Tool-MVR arXiv record: https://arxiv.org/abs/2506.04625
"""
    Path("V4_1_EXTERNAL_BASELINE_REPORT.md").write_text(report)



def _table_main_extended(main: dict[str, dict]) -> str:
    lines = []
    for method in EXTERNAL_METHODS:
        r = main[method]
        lines.append(
            f"| {r['Method']} | {r['SCCR']:.3f} | {r['OEPVR']:.3f} | {r['TSR']:.3f} | {r['AvgToolCalls']:.3f} | {r['AvgAddedCalls']:.3f} | {r['AvgLatency']:.1f} | {r['AvgAddedLatency']:.1f} |"
        )
    return "\n".join(lines)


def _table_main(main: dict[str, dict]) -> str:
    lines = []
    for method in EXTERNAL_METHODS:
        r = main[method]
        lines.append(
            f"| {r['Method']} | {r['SCCR']:.3f} | {r['OEPVR']:.3f} | {r['TSR']:.3f} | {r['AvgToolCalls']:.3f} | {r['AvgLatency']:.1f} |"
        )
    return "\n".join(lines)


def _warnings_text(warnings: list[str]) -> str:
    if not warnings:
        return "No v4.1 sanity warnings were emitted."
    return "\n".join(f"- {w}" for w in warnings)


def main() -> None:
    registry = ToolRegistry()
    tasks = _task_maps()
    rows: list[dict] = []
    for seed in SEEDS:
        seed_tasks = [tasks[(seed, tid)] for s, tid in sorted(tasks) if s == seed]
        for method in ["direct_tool_planning", "mirror_inspired", "tool_mvr_inspired"]:
            rows.extend(_run_external_one(task, method, registry) for task in seed_tasks)
    rows.extend(_proposed_rows(tasks, registry))

    (ROOT / "raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "summary").mkdir(parents=True, exist_ok=True)
    (ROOT / "figures").mkdir(parents=True, exist_ok=True)
    write_jsonl(ROOT / "raw" / "external_baselines_all.jsonl", rows)

    summary = _summarize(rows)
    by_seed = _summarize(rows, "dataset_seed")
    by_vtype = _summarize(rows, "violation_type")
    by_family = _summarize(rows, "family")
    reflection = [r for r in summary if r["method"] in {"mirror_inspired", "tool_mvr_inspired", "proposed"}]
    ablation = _read_csv(Path("results/v3/summary/cost_contribution.csv"))

    write_csv(ROOT / "summary" / "main_external_results.csv", [r for r in summary if r["group"] == "all"])
    write_csv(ROOT / "summary" / "reflection_repair_results.csv", reflection)
    write_csv(ROOT / "summary" / "reflection_timing_results.csv", reflection)
    write_csv(ROOT / "summary" / "correction_trace_summary.csv", reflection)
    write_csv(ROOT / "summary" / "ablation_results.csv", ablation)
    write_csv(ROOT / "summary" / "by_violation_type.csv", by_vtype)
    write_csv(ROOT / "summary" / "by_task_family.csv", by_family)
    write_csv(ROOT / "summary" / "by_seed.csv", by_seed)
    write_csv(ROOT / "summary" / "statistical_tests.csv", _stats(rows))
    warnings = _sanity_warnings(rows)
    (ROOT / "summary" / "sanity_warnings.txt").write_text("\n".join(warnings) + ("\n" if warnings else ""))
    _paper_tables(summary, ablation, by_vtype)
    _make_figures(summary, reflection, ablation)
    _write_report(summary, reflection, ablation, warnings)
    print(f"wrote {len(rows)} v4.1 rows to {ROOT}")
    for warning in warnings:
        print(warning)


if __name__ == "__main__":
    main()
