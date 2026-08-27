# Figure Guide

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

- `fig_correction_timing_concept.png`
- `fig_experimental_pipeline.png`
- `fig_proposed_architecture.png`
- `fig_selective_repair_example.png`
- `fig_validity_hierarchy_concept.png`
- `fig_correction_timing_concept.pdf`
- `fig_experimental_pipeline.pdf`
- `fig_proposed_architecture.pdf`
- `fig_selective_repair_example.pdf`
- `fig_validity_hierarchy_concept.pdf`
- FIGURE_GUIDE.md
