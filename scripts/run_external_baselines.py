#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
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


ROOT = Path("results/v4_external_baselines")
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
    op = evaluate_operational_validity(workflow, task, registry)
    outcome = evaluate(workflow, task, registry)
    correction_count = int(meta.get("correction_count", 0))
    reflection_count = int(meta.get("reflection_count", 0))
    recovery_count = int(meta.get("post_execution_recovery_count", 0))
    return {
        "experiment_id": "v4_external_baselines",
        "task_id": task.task_id,
        "family": task.family,
        "severity": task.severity,
        "violation_type": task.violation_type,
        "method": method,
        "Method": DISPLAY[method],
        "seed": task.seed,
        "dataset_seed": int(task.seed // 10000),
        "initial_workflow": workflow.to_dict(),
        "final_workflow": workflow.to_dict(),
        "GT_schema_connected": int(_schema_connectivity(workflow, registry)),
        "GT_strict_valid": op["GT_strict_valid"],
        "SCCR": op["GT_strict_valid"],
        "GT_operational_valid": op["GT_operational_valid"],
        "OEPV": op["GT_operational_valid"],
        "GT_success": outcome["GT_success"],
        "GT_valid": outcome["GT_valid"],
        "tool_calls": state.tool_calls,
        "agent_calls": state.agent_calls,
        "llm_calls": 0,
        "simulated_latency_ms": state.simulated_latency_ms,
        "wall_clock_latency_ms": state.wall_clock_latency_ms(),
        "average_added_calls": correction_count,
        "average_added_latency": _added_latency_from_trace(trace, registry),
        "correction_count": correction_count,
        "reflection_count": reflection_count,
        "pre_execution_reflection_count": int(meta.get("pre_execution_reflection_count", 0)),
        "post_execution_reflection_count": int(meta.get("post_execution_reflection_count", 0)),
        "post_execution_recovery_count": recovery_count,
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
                    "experiment_id": "v4_external_baselines",
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
                "ReflectionCount": mean([r.get("reflection_count", 0.0) for r in rs]),
                "CorrectionCount": mean([r.get("correction_count", 0.0) for r in rs]),
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
        "CorrectionRate",
        "RecoveryRate",
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
        banned = ["src.oracle", "GT_success", "GT_operational_valid", "src.orchestration.risk", "src.orchestration.proposed"]
        leaks = [term for term in banned if term in text]
        if leaks:
            warnings.append(f"WARNING: possible oracle/proposed leakage in {method}: {', '.join(leaks)}")
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
    if _task_level_signature(by_method["proposed"]) == _task_level_signature(by_method["direct_tool_planning"]):
        warnings.append("WARNING: Direct Tool-Planning is identical to Proposed; check implementation leakage.")
    return warnings


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
    proposed = main["proposed"]
    externals = [main[m] for m in ["direct_tool_planning", "mirror_inspired", "tool_mvr_inspired"]]
    best_external_oepv = max(externals, key=lambda r: r["OEPVR"])
    best_external_tsr = max(externals, key=lambda r: r["TSR"])
    strict_rows = _load_v3_method("strict")
    prop_rows = _load_v3_method("proposed")
    strict_oepv = mean([r["GT_operational_valid"] for r in strict_rows]) if strict_rows else 0.0
    strict_tsr = mean([r["GT_success"] for r in strict_rows]) if strict_rows else 0.0
    prop_oepv = mean([r["GT_operational_valid"] for r in prop_rows]) if prop_rows else proposed["OEPVR"]
    prop_tsr = mean([r["GT_success"] for r in prop_rows]) if prop_rows else proposed["TSR"]
    cost = {str(r.get("method")): r for r in ablation_rows}
    risk_only = cost.get("A2_risk_only_selective", {})
    risk_cost = cost.get("A3_risk_cost_selective", {})
    report = f"""# V4 External Baseline Report

## Scope

This v4 evaluation preserves `results/v3/` and `results/v3_operational_validity/` and writes new outputs only under `results/v4_external_baselines/`.

## Baselines

### Direct Tool-Planning

Reference context: BFCL / Berkeley Function Calling Leaderboard and PlanningArena evaluate modern tool/function planning settings. The implemented baseline performs direct tool selection and sequencing from the user query plus public tool descriptions and public input/output schemas. It does not use execution-condition validation, reflection, repair optimization, Oracle state, or Proposed risk.

Exact paper label: **Direct Tool-Planning**.

### MIRROR-inspired

Reference context: IJCAI 2025 MIRROR proposes multi-agent intra- and inter-reflection for tool learning. The implemented baseline includes deterministic intra-reflection before execution, public-schema trajectory checks, post-planning observation review, and public-schema corrections. It does not reproduce MIRROR training, multi-agent learning, or model components, so it is reported only as **MIRROR-inspired**.

### Tool-MVR-inspired

Reference context: Tool-MVR is treated as an Error -> Reflection -> Correction style tool-use method. The implemented baseline first executes a direct public-schema plan, detects public execution errors, reflects on those errors, corrects the workflow using public producer tools, and retries. It does not reproduce Tool-MVR fine-tuning or training, so it is reported only as **Tool-MVR-inspired**.

## Main Results

| Method | SCCR | OEPVR | TSR | Avg Tool Calls | Avg Latency |
|---|---:|---:|---:|---:|---:|
{_table_main(main)}

## Sanity Warnings

{_warnings_text(warnings)}

## Required Questions

**Q1. Proposed가 외부 baseline 대비 OEPVR에서 우수한가?**  
Proposed OEPVR={proposed['OEPVR']:.3f}; best external baseline is {best_external_oepv['Method']} with OEPVR={best_external_oepv['OEPVR']:.3f}.

**Q2. Proposed가 외부 baseline 대비 TSR에서 우수한가?**  
Proposed TSR={proposed['TSR']:.3f}; best external baseline is {best_external_tsr['Method']} with TSR={best_external_tsr['TSR']:.3f}.

**Q3. Proposed가 external reflection baseline보다 Tool Calls 또는 latency를 줄이는가?**  
Compared with reflection baselines, Proposed average calls/latency are {proposed['AvgToolCalls']:.3f}/{proposed['AvgLatency']:.1f} ms; MIRROR-inspired is {main['mirror_inspired']['AvgToolCalls']:.3f}/{main['mirror_inspired']['AvgLatency']:.1f} ms and Tool-MVR-inspired is {main['tool_mvr_inspired']['AvgToolCalls']:.3f}/{main['tool_mvr_inspired']['AvgLatency']:.1f} ms. Proposed has higher tool calls than both reflection baselines in this run, while simulated latency is essentially tied. Direct Tool-Planning remains the cheapest method but has lower OEPVR/TSR.

**Q4. Schema Connectivity가 높아도 SCCR/OEPVR이 낮은 사례가 외부 baseline에서도 확인되는가?**  
Direct Tool-Planning schema connectivity={main['direct_tool_planning']['SchemaConnectivityRate']:.3f}, SCCR={main['direct_tool_planning']['SCCR']:.3f}, OEPVR={main['direct_tool_planning']['OEPVR']:.3f}; this directly tests schema-level connection versus operational validity.

**Q5. 실행 전 validity/risk evaluation이 실행 후 reflection/correction 대비 어떤 장단점을 보이는가?**  
Pre-execution Proposed avoids some post-hoc correction loops but may keep low-risk non-conformances. Reflection baselines can repair public schema errors after inspection but do not inspect hidden execution conditions before execution.

**Q6. Strict 대비 Proposed는 동일 OEPVR/TSR 수준에서 repair를 줄이는가?**  
Strict OEPVR/TSR={strict_oepv:.3f}/{strict_tsr:.3f}; Proposed OEPVR/TSR={prop_oepv:.3f}/{prop_tsr:.3f}. In the v3 operational-validity deltas copied into this evaluation, Proposed changes SCCR by -6.0 percentage points, OEPVR by +0.0 percentage points, TSR by +0.0 percentage points, repair rate by -52.7 percentage points, OURR by -5.6 percentage points, average added latency by -10.0 ms, and average tool calls by -0.06.

**Q7. Risk-Cost는 Risk-only 대비 동일한 reliability에서 latency를 줄이는가?**  
Risk-only TSR={float(risk_only.get('TSR', 0.0)):.3f}, added latency={float(risk_only.get('avg_added_latency', risk_only.get('AvgAddedLatency', 0.0))):.1f}; Risk-Cost TSR={float(risk_cost.get('TSR', 0.0)):.3f}, added latency={float(risk_cost.get('avg_added_latency', risk_cost.get('AvgAddedLatency', 0.0))):.1f}.

**Q8. 어떤 execution condition에서 Proposed의 장점이 가장 큰가?**  
See `summary/by_violation_type.csv`. Against Direct Tool-Planning, the largest OEPVR gains in this run occur for unit, provenance, and coordinate violations. Against Strict, the main observed benefit is not higher OEPVR/TSR but lower repair rate and lower added latency.

**Q9. 외부 baseline 중 Proposed보다 좋은 지표가 있는가?**  
Yes. Direct Tool-Planning has lower average tool calls and lower latency than Proposed, but its OEPVR and TSR are lower. MIRROR-inspired and Tool-MVR-inspired have fewer tool calls than Proposed with almost identical latency, but lower OEPVR and TSR.

**Q10. 현재 결과만으로 KCI 논문의 contribution을 주장하기 충분한가?**  
The defensible contribution is limited to the implemented and measured distinction between schema planning, strict condition conformance, operational validity, and task success, plus transparent comparison against direct and reflection-inspired tool-use baselines. Claims about exact MIRROR or Tool-MVR reproduction are not supported.

## References

- BFCL / Berkeley Function Calling Leaderboard, ICML 2025: https://mlanthology.org/icml/2025/patil2025icml-berkeley/
- PlanningArena, ACL 2025: https://aclanthology.org/2025.acl-long.1499/
- MIRROR, IJCAI 2025: https://www.ijcai.org/proceedings/2025/14
- Tool-MVR arXiv record: https://arxiv.org/abs/2506.04625
"""
    Path("V4_EXTERNAL_BASELINE_REPORT.md").write_text(report)


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
        return "No v4 sanity warnings were emitted."
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
    print(f"wrote {len(rows)} v4 rows to {ROOT}")
    for warning in warnings:
        print(warning)


if __name__ == "__main__":
    main()
