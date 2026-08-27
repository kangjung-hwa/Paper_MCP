#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path("results/paper_figures")
DPI = 300
FONT = "DejaVu Sans"

COLORS = {
    "box": "#f7f7f7",
    "line": "#222222",
    "accent": "#d9e8f5",
    "repair": "#f3e3c3",
    "valid": "#d9ead3",
    "warn": "#f4cccc",
    "soft": "#eeeeee",
}


def setup(figsize=(10, 6)):
    plt.rcParams.update({
        "font.family": FONT,
        "font.size": 10,
        "axes.edgecolor": COLORS["line"],
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    })
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def box(ax, xy, w, h, text, fc=None, fontsize=9, lw=1.0, style="round,pad=0.012,rounding_size=0.012"):
    patch = FancyBboxPatch(xy, w, h, boxstyle=style, linewidth=lw, edgecolor=COLORS["line"], facecolor=fc or COLORS["box"])
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)
    return patch


def rect(ax, xy, w, h, text, fc=None, fontsize=9, lw=1.0):
    patch = Rectangle(xy, w, h, linewidth=lw, edgecolor=COLORS["line"], facecolor=fc or COLORS["box"])
    ax.add_patch(patch)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)
    return patch


def arrow(ax, start, end, text=None, rad=0.0, style="->"):
    arr = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=12, linewidth=1.0, color=COLORS["line"], connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(arr)
    if text:
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.015, text, ha="center", va="center", fontsize=8)
    return arr


def save(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / f"{stem}.png", dpi=DPI)
    fig.savefig(OUT / f"{stem}.pdf")
    plt.close(fig)


def fig_proposed_architecture():
    fig, ax = setup((12, 7))
    x = 0.07
    w = 0.24
    h = 0.062
    ys = [0.89, 0.79, 0.69, 0.59, 0.49]
    labels = [
        "User Query / Task",
        "Initial MCP\nWorkflow Planning",
        "Execution-Condition\nValidation",
        "Condition Deficit\nCalculation",
        "Workflow Risk\nCalculation R(W)",
    ]
    for y, label in zip(ys, labels):
        box(ax, (x, y), w, h, label, fc=COLORS["accent"] if "Validation" in label else COLORS["box"])
    for y1, y2 in zip(ys, ys[1:]):
        arrow(ax, (x + w / 2, y1), (x + w / 2, y2 + h))

    conds = ["Schema Type", "Semantic Type", "Unit", "Reference Frame", "Freshness", "Confidence", "Provenance"]
    cx0, cy0 = 0.37, 0.675
    for i, c in enumerate(conds):
        rect(ax, (cx0 + (i % 2) * 0.13, cy0 - (i // 2) * 0.047), 0.118, 0.034, c, fc="white", fontsize=7.3)
    arrow(ax, (x + w, 0.72), (cx0, 0.72), style="-")

    box(ax, (0.39, 0.47), 0.25, 0.10, "Edge Risk:\n$R_{ij}=\\sum_k w_k d_{ij,k}$\nWorkflow Risk:\n$R(W)=\\max R_{ij}$", fc="white", fontsize=9)
    arrow(ax, (x + w, 0.52), (0.39, 0.52), style="-")

    box(ax, (0.39, 0.34), 0.25, 0.075, "Decision:\n$R(W)>\\theta$ ?", fc=COLORS["soft"], fontsize=10)
    arrow(ax, (x + w / 2, 0.49), (0.515, 0.415))

    box(ax, (0.70, 0.42), 0.22, 0.06, "Use Original\nWorkflow", fc=COLORS["valid"])
    box(ax, (0.70, 0.30), 0.22, 0.06, "Final Execution", fc=COLORS["valid"])
    arrow(ax, (0.64, 0.377), (0.70, 0.45), "No")
    arrow(ax, (0.81, 0.42), (0.81, 0.36))

    repair_labels = [
        "Generate\nCandidates",
        "Risk-Cost\nEvaluation",
        "Select\n$r^*$",
        "Insert Repair\nTool / Agent",
        "Final Workflow\nExecution",
    ]
    rx = [0.07, 0.26, 0.45, 0.64, 0.83]
    ry = 0.13
    for xpos, label in zip(rx, repair_labels):
        box(ax, (xpos, ry), 0.14, 0.075, label, fc=COLORS["repair"] if "Repair" in label or "Insert" in label or "Candidates" in label else COLORS["box"], fontsize=8)
    arrow(ax, (0.515, 0.34), (0.14, ry + 0.075), "Yes")
    for x1, x2 in zip(rx, rx[1:]):
        arrow(ax, (x1 + 0.14, ry + 0.037), (x2, ry + 0.037))
    box(ax, (0.34, 0.01), 0.32, 0.08, "$r^*=\\arg\\min [R(W\\oplus r)+\\lambda C(r)]$\nCost terms: Latency, Tool Calls", fc="white", fontsize=9)
    arrow(ax, (0.52, ry), (0.50, 0.09), style="-")
    save(fig, "fig_proposed_architecture")

def fig_validity_hierarchy_concept():
    fig, ax = setup((9, 7))
    levels = [
        ("Level 1\nSchema Connectivity", "Can tool outputs and inputs\nbe structurally connected?"),
        ("Level 2\nStrict Condition Conformance\n(SCCR)", "Are all specified execution\nconditions fully satisfied?"),
        ("Level 3\nOperational Execution Validity\n(OEPVR)", "Is the workflow executable\nwithin operational tolerance?"),
        ("Level 4\nTask Success\n(TSR)", "Was the final task objective\nachieved?"),
    ]
    x, w, h = 0.10, 0.36, 0.11
    ys = [0.80, 0.62, 0.44, 0.26]
    for i, ((title, desc), y) in enumerate(zip(levels, ys)):
        box(ax, (x, y), w, h, f"{title}\n{desc}", fc=COLORS["accent"] if i < 3 else COLORS["valid"], fontsize=9)
    for y1, y2 in zip(ys, ys[1:]):
        arrow(ax, (x + w / 2, y1), (x + w / 2, y2 + h))
    ax.text(0.28, 0.12, "Structural Compatibility\n!= Strict Conformance\n!= Operational Validity\n!= Task Success", ha="center", va="center", fontsize=11, fontweight="bold")

    box(ax, (0.57, 0.58), 0.32, 0.22, "Illustrative tolerance example\n\nRequired confidence: 0.80\nOperational minimum: 0.75\nActual confidence: 0.77\n\nSCCR = 0\nOEPV = 1", fc="white", fontsize=9)
    box(ax, (0.57, 0.28), 0.32, 0.20, "Illustrative outcome example\n\nWorkflow executable\nRoute quality or environment\noutcome fails\n\nOEPV = 1\nTSR = 0", fc="white", fontsize=9)
    save(fig, "fig_validity_hierarchy_concept")


def fig_selective_repair_example():
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), facecolor="white")
    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
    for ax, title in zip(axes, ["Strict All-Repair", "Proposed Selective Repair"]):
        ax.text(0.5, 0.95, title, ha="center", va="center", fontsize=12, fontweight="bold")
        for y, label in [(0.78, "Tool A"), (0.52, "Tool B"), (0.26, "Tool C\nGoal")]:
            box(ax, (0.12, y), 0.22, 0.08, label, fc=COLORS["box"])
        arrow(ax, (0.23, 0.78), (0.23, 0.60))
        arrow(ax, (0.23, 0.52), (0.23, 0.34))
        rect(ax, (0.40, 0.66), 0.25, 0.07, "Artifact 1\nFreshness deficit: low", fc=COLORS["warn"], fontsize=8)
        rect(ax, (0.40, 0.40), 0.25, 0.07, "Artifact 2\nConfidence deficit: high", fc=COLORS["warn"], fontsize=8)
    ax = axes[0]
    box(ax, (0.70, 0.65), 0.22, 0.07, "Refresh Tool", fc=COLORS["repair"])
    box(ax, (0.70, 0.39), 0.22, 0.08, "Sensor Fusion /\nConfidence Enhancement", fc=COLORS["repair"], fontsize=8)
    arrow(ax, (0.65, 0.695), (0.70, 0.685))
    arrow(ax, (0.65, 0.435), (0.70, 0.43))
    ax.text(0.55, 0.13, "Repair every detected violation\nResult: all violations repaired", ha="center", va="center", fontsize=10)

    ax = axes[1]
    box(ax, (0.70, 0.64), 0.22, 0.09, "Illustrative:\nR = 0.03 <= theta 0.05\nNo Repair", fc=COLORS["valid"], fontsize=8)
    box(ax, (0.70, 0.37), 0.22, 0.12, "Illustrative:\nR = 0.12 > theta 0.05\nGenerate candidates\nRisk-cost selection", fc=COLORS["repair"], fontsize=8)
    arrow(ax, (0.65, 0.695), (0.70, 0.685))
    arrow(ax, (0.65, 0.435), (0.70, 0.43))
    ax.text(0.55, 0.12, "Repair only violations whose\nexecution risk exceeds threshold\nCandidates evaluated by risk reduction,\nlatency, and tool calls", ha="center", va="center", fontsize=9)
    fig.tight_layout(pad=0.8)
    fig.savefig(OUT / "fig_selective_repair_example.png", dpi=DPI)
    fig.savefig(OUT / "fig_selective_repair_example.pdf")
    plt.close(fig)


def fig_experimental_pipeline():
    fig, ax = setup((12, 6.8))
    left_x = 0.07
    steps = [
        ("Task Generator", 0.82),
        ("3 Seeds\n42 / 123 / 2026", 0.68),
        ("300 Tasks per Seed", 0.54),
        ("900 Tasks per Method", 0.40),
    ]
    for label, y in steps:
        box(ax, (left_x, y), 0.22, 0.08, label, fc=COLORS["box"])
    for (_, y1), (_, y2) in zip(steps, steps[1:]):
        arrow(ax, (left_x + 0.11, y1), (left_x + 0.11, y2 + 0.08))

    methods = ["Direct Tool-Planning", "MIRROR-inspired", "Tool-MVR-inspired", "Proposed"]
    mx = 0.39
    for i, m in enumerate(methods):
        box(ax, (mx, 0.72 - i * 0.13), 0.25, 0.075, m, fc=COLORS["accent"] if m == "Proposed" else COLORS["box"])
        arrow(ax, (left_x + 0.22, 0.44), (mx, 0.757 - i * 0.13), style="-")

    box(ax, (0.39, 0.16), 0.25, 0.12, "Shared Conditions\nSame Tasks\nSame Seeds\nSame Tool Registry\nSame Environment\nSame Evaluator", fc="white", fontsize=8.5)

    box(ax, (0.72, 0.42), 0.23, 0.18, "Independent\nEvaluation / Oracle\n\nSchema Connectivity\nSCCR / OEPVR / TSR\nTool Calls / Latency", fc=COLORS["valid"], fontsize=8.5)
    for i in range(4):
        arrow(ax, (mx + 0.25, 0.757 - i * 0.13), (0.72, 0.51), style="->")
    ax.text(0.82, 0.34, "Oracle used only for\npost-execution evaluation", ha="center", va="center", fontsize=9, style="italic")
    arr = FancyArrowPatch((0.82, 0.38), (0.82, 0.42), arrowstyle="->", mutation_scale=10, linewidth=1.0, linestyle="--", color=COLORS["line"])
    ax.add_patch(arr)
    save(fig, "fig_experimental_pipeline")


def fig_correction_timing_concept():
    fig, ax = setup((12, 5.5))
    rows = [
        ("MIRROR-inspired", ["Planning", "Pre-Reflection", "Pre-Correction", "Execution", "Post Review"], "Public schema / trajectory"),
        ("Tool-MVR-inspired", ["Planning", "Execution", "Error Observation", "Reflection", "Correction", "Retry"], "Observable execution error"),
        ("Proposed", ["Planning", "Execution-Condition\nValidation", "Risk Evaluation", "Selective Repair", "Execution"], "Execution-condition metadata"),
    ]
    y_values = [0.78, 0.50, 0.22]
    for (name, steps, source), y in zip(rows, y_values):
        ax.text(0.04, y + 0.035, name, ha="left", va="center", fontsize=11, fontweight="bold")
        xs = [0.24 + i * (0.68 / (len(steps) - 1)) for i in range(len(steps))]
        for x, step in zip(xs, steps):
            box(ax, (x - 0.055, y), 0.11, 0.07, step, fc=COLORS["repair"] if "Correction" in step or "Repair" in step else COLORS["box"], fontsize=7.5)
        for x1, x2 in zip(xs, xs[1:]):
            arrow(ax, (x1 + 0.055, y + 0.035), (x2 - 0.055, y + 0.035))
        ax.text(0.24, y - 0.065, f"Information source: {source}", ha="left", va="center", fontsize=9, style="italic")
    save(fig, "fig_correction_timing_concept")


def write_guide():
    files = sorted(p.name for p in OUT.glob("fig_*.png")) + sorted(p.name for p in OUT.glob("fig_*.pdf"))
    guide = """# Figure Guide

## Fig. 1 Proposed Architecture

Files: `fig_proposed_architecture.png`, `fig_proposed_architecture.pdf`

Recommended position: beginning of the proposed method section.

Caption draft: Overall architecture of the proposed risk-aware MCP orchestration method. The method validates execution conditions, quantifies condition deficits, computes workflow risk, and selectively inserts repair tools or agents using risk-cost evaluation.

Contribution explained: execution-condition validation, risk-based selective repair, and cost-aware repair selection.

Formula/parameter status: formulas match the implementation; no experimental performance numbers are included.

## Fig. 2 Validity Hierarchy

Files: `fig_validity_hierarchy_concept.png`, `fig_validity_hierarchy_concept.pdf`

Recommended position: execution-plan validity definition section.

Caption draft: Conceptual hierarchy separating schema connectivity, strict condition conformance, operational execution validity, and task success.

Contribution explained: execution-plan validity is broader than schema connectivity but distinct from task success.

Formula/parameter status: confidence values are illustrative examples, not measured experiment results.

## Fig. 3 Selective Repair Example

Files: `fig_selective_repair_example.png`, `fig_selective_repair_example.pdf`

Recommended position: risk-based selective repair section.

Caption draft: Conceptual comparison between strict all-repair and proposed selective repair for a workflow with low-risk and high-risk condition deficits.

Contribution explained: selective repair can avoid repairing low-risk condition deviations while repairing high-risk ones through risk-cost candidate selection.

Formula/parameter status: R and theta values are illustrative examples, not actual task results.

## Fig. 4 Experimental Pipeline

Files: `fig_experimental_pipeline.png`, `fig_experimental_pipeline.pdf`

Recommended position: experimental setup section.

Caption draft: Reproducible evaluation pipeline using three seeds, 900 task instances per method, shared tool registry, shared task set, and independent post-execution Oracle evaluation.

Contribution explained: fairness and reproducibility of the external baseline comparison.

Formula/parameter status: seed and task-count values reflect the current experimental design.

## Fig. 5 Correction Timing Concept

Files: `fig_correction_timing_concept.png`, `fig_correction_timing_concept.pdf`

Recommended position: baseline comparison or result interpretation section.

Caption draft: Conceptual timing difference among MIRROR-inspired pre-execution reflection, Tool-MVR-inspired post-execution correction, and proposed pre-execution execution-condition validation and selective repair.

Contribution explained: separates pre-execution trajectory reflection, post-execution recovery, and execution-condition-aware repair.

Formula/parameter status: conceptual figure only; no measured latency or success numbers are included.

## Generated Files

"""
    guide += "\n".join(f"- `{name}`" for name in files)
    guide += "\n"
    (OUT / "FIGURE_GUIDE.md").write_text(guide)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig_proposed_architecture()
    fig_validity_hierarchy_concept()
    fig_selective_repair_example()
    fig_experimental_pipeline()
    fig_correction_timing_concept()
    write_guide()
    print(f"wrote paper figures to {OUT}")


if __name__ == "__main__":
    main()
