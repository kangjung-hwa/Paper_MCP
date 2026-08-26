# Risk-Aware MCP Orchestration Testbed

Python implementation for the paper experiment: **execution-plan validity and execution-risk-aware MCP based AI agent orchestration**.

## Structure

The implementation is under `src/` with separated responsibilities:

| Area | Path |
|---|---|
| MCP registry/client/server | `src/mcp/` |
| 24 tool specifications and execution model | `src/tools/`, `src/mcp/registry.py` |
| Workflow/task/contracts | `src/models/` |
| Planner prompt and deterministic planner | `src/planner/` |
| Validator, deficit, dependency, risk, repair | `src/orchestration/` |
| ReAct, schema-aware, strict baselines | `src/baselines/` |
| Oracle-only validity/success/counterfactual | `src/oracle/` |
| Task generator and violations | `src/tasks/` |
| Runner, metrics, statistics | `src/evaluation/` |

## Reproduce

```bash
pip install -r requirements.txt
python scripts/generate_tasks.py --seed 42
python scripts/run_experiment.py --config configs/experiment.yaml --method react
python scripts/run_experiment.py --config configs/experiment.yaml --method schema_aware
python scripts/run_experiment.py --config configs/experiment.yaml --method strict
python scripts/run_experiment.py --config configs/experiment.yaml --method proposed
python scripts/run_ablation.py
python scripts/aggregate_results.py
```

One-command reproduction:

```bash
python scripts/run_all.py
```

## Tool Specification Table

| ID | Tool | Category | Output |
|---|---|---|---|
| T01 | GetOwnPosition | information | Position |
| T02 | DetectObject | information | ObjectPosition |
| T03 | TrackObject | information | Updated Position |
| T04 | GetDestination | information | Position |
| T05 | GetWeather | information | Weather |
| T06 | GetTerrain | information | TerrainMap |
| T07 | GetThreatInfo | information | ThreatInfo |
| T08 | GetCommunicationStatus | information | CommStatus |
| T09 | CoordinateTransform | conversion | transformed data |
| T10 | UnitConversion | conversion | converted data |
| T11 | RefreshPosition | refresh | fresh Position |
| T12 | RefreshThreatInfo | refresh | fresh ThreatInfo |
| T13 | SensorFusion | enhancement | higher-confidence fused data |
| T14 | ConfidenceEnhancement | enhancement | higher-confidence data |
| T15 | ValidateSource | enhancement | verified-provenance data |
| T16 | ThreatAnalysisAgent | agent | ThreatMap |
| T17 | SituationAnalysisAgent | agent | Situation |
| T18 | CommunicationAnalysisAgent | agent | CommAssessment |
| T19 | RoutePlanning | planning | Route |
| T20 | ThreatAwareRoutePlanning | planning | Route |
| T21 | WeatherAwareRoutePlanning | planning | Route |
| T22 | CommunicationAwareRoutePlanning | planning | Route |
| T23 | RouteValidation | validation | ValidationResult |
| T24 | ResultVisualization | visualization | Visualization |

Detailed public and oracle execution conditions are encoded in `src/mcp/registry.py`. Public metadata can be exported in full or partial mode through `ToolSpec.public_spec()`.

## Task Family Specification Table

| Family | Goal | Required Functions |
|---|---|---|
| F1 | Basic route planning | Own position, destination, terrain, route planning, validation |
| F2 | Threat-aware route | Own position, destination, threat info, threat analysis, threat-aware route, validation |
| F3 | Weather-aware route | Own position, destination, weather, weather-aware route, validation |
| F4 | Communication-aware route | Own position, destination, comm status, comm analysis, comm-aware route, validation |
| F5 | Multi-constraint route | Position, destination, threat, weather, situation/threat analysis, route, validation |
| F6 | Situation analysis and recommendation | Position, threat, weather, situation, route, validation, visualization |

The generator creates 300 tasks: 50 per family with 20 normal, 15 minor, and 15 critical instances.

## Violation Specification Table

| Type | Injection |
|---|---|
| Coordinate | ENU-required data starts as WGS84 |
| Unit | meter-required data starts as kilometer |
| Freshness | artifact timestamp age exceeds `max_age` |
| Confidence | confidence falls below `min_confidence` |
| Provenance | verified-required data starts as unverified |
| Compound | 2-4 simultaneous condition violations |

Minor/critical labels are defined by Oracle task outcome, not by the proposed risk formula.

## Baseline Comparison Table

| Method | Implementation |
|---|---|
| ReAct | ReAct-style deterministic reasoning/action workflow without prior validity/risk evaluator |
| Schema-Aware | HyperAgent-inspired schema-aware baseline using schema/semantic connectivity only |
| Strict | Uses the same condition checker as Proposed, but repairs every violation |
| Proposed | Deficit magnitude, downstream impact, risk threshold, and risk-cost repair optimization |

This project does not claim to reproduce the original ReAct or HyperAgent implementations or their reported paper numbers.

## Hyperparameter Table

| Parameter | Default | Grid |
|---|---:|---|
| `theta` | 0.05 | 0.05 default; sensitivity 0.1 to 0.9 |
| `lambda` | 0.25 | 0, 0.1, 0.25, 0.5, 1, 2 |
| `eta` | 0.1 | config |
| `xi` | 0.1 | config |
| repair cost betas | 0.25 each | config |
| model | deterministic-planner | config |
| temperature | 0.0 | config |

## Outputs

Raw task-level JSONL files are saved under `results/raw/`. Summary CSV files:

| File | Content |
|---|---|
| `results/summary/main_results.csv` | method-level reliability and efficiency |
| `results/summary/by_task_family.csv` | grouped by F1-F6 |
| `results/summary/by_violation_type.csv` | grouped by violation |
| `results/summary/by_severity.csv` | grouped by normal/minor/critical |
| `results/summary/ablation.csv` | A1-A5 ablations |
| `results/figures/figure_source_main.csv` | figure-ready main table |

## Oracle Rules

Oracle code in `src/oracle/` independently evaluates mandatory execution conditions and task success. It does not consume proposed risk scores. Success accepts workflows by final goal conditions, not exact tool order matching.

## Known Limits

The current planner is deterministic for reproducible paper experiments. Tool outputs are simulated rather than connected to live services. Geometry checks are represented by deterministic condition rules; real polygon intersection can be added behind the same Oracle interface.


## V2 Validity Improvements

V2 preserves the original project layout and 24 base tools, while adding four alternative repair tools (T25-T28) so repair optimization has real cost/quality alternatives. Existing v1 outputs were preserved under `results/archive/v1_initial/`; new outputs are written to `results/v2/`.

### ReAct Baseline

`src/baselines/react.py` now implements a deterministic ReAct-style loop:

1. infer required tool sequence from the user query,
2. choose an executable action using public tool descriptions and public schema,
3. append the tool result as an observation,
4. continue until a goal artifact is produced or `max_tool_calls` is reached.

It does not import or call `gold_workflows.py`. Every thought/action/observation is stored in raw result field `planner_trace` and `tool_observations`.

### Schema-Aware Baseline

`src/baselines/schema_aware.py` is a HyperAgent-inspired schema-aware baseline; not an exact reproduction of the original HyperAgent implementation. It performs backward graph search from the goal semantic artifact and recursively resolves missing requirements using only public input/output schema and semantic type. It ignores coordinate frame, unit, freshness, confidence, provenance, downstream impact, and risk. Tie-breaks are minimum tool count proxy, lower simulated latency, then lexical tool id.

### Oracle Separation

Oracle evaluation no longer imports `src.orchestration.validator`. The independent path is:

| Module | Role |
|---|---|
| `src/oracle/environment.py` | hidden world state and geometric/environment helpers |
| `src/oracle/artifact_semantics.py` | Oracle-only condition comparison |
| `src/oracle/simulator.py` | Oracle execution simulation using registry oracle requirements |
| `src/oracle/task_outcomes.py` | task-family outcome rules |
| `src/oracle/validity.py` | GT_valid |
| `src/oracle/success.py` | GT_success and failure reason |

This allows `GT_valid=False, GT_success=True` for minor outcome-safe violations, and `GT_valid=True, GT_success=False` for valid plans that still fail in the hidden environment.

### Outcome-Based Minor/Critical Tasks

Task instances now include `oracle_world`, hidden from planners. Minor tasks may violate execution preconditions but set `outcome_impacted=False`, so the final route can still succeed. Critical tasks set hidden obstacles, threat polygons, weather hazards, or communication coverage failures so uncorrected workflows fail by outcome, not merely by deficit magnitude.

### Repair Metrics

| Metric | Definition |
|---|---|
| OURR | Outcome-unnecessary repair rate: removing an inserted repair still leaves `GT_success=True` |
| VURR | Validity-unnecessary repair rate: removing an inserted repair still leaves `GT_valid=True` |

`OURR` is the main paper metric. The previous strict URR column is retained as an alias for VURR for backward compatibility.

### V2 Outputs

| File | Content |
|---|---|
| `results/v2/raw/*.jsonl` | task-level raw logs with planner trace, observations, risk edges, failure reason |
| `results/v2/summary/main_results.csv` | method comparison with OURR/VURR/AUC columns |
| `results/v2/summary/ablation.csv` | A1-A5 ablation |
| `results/v2/summary/by_downstream_depth.csv` | depth bucket comparison for Proposed and no-downstream |
| `results/v2/summary/by_branching_factor.csv` | branch bucket comparison |
| `results/v2/summary/sanity_warnings.txt` | automatic validity warnings |

### LLM Validation

Controlled experiments remain deterministic by default. OpenAI-compatible validation hooks are available via `src/planner/llm_backend.py`; if no API key is configured, deterministic mode remains usable.

```bash
OPENAI_API_KEY=... python scripts/run_llm_validation.py
```

The LLM prompt path must use public tool metadata only. Oracle world state, GT labels, severity, hidden conditions, and failure reasons are not exposed.

### Current V2 Sanity Notes

The current v2 run emits a repair-metric warning because VURR is 0 across methods, while OURR is non-zero. This is not hidden or tuned away; it indicates that validity-unnecessary repair remains rare under the current Oracle precondition rules, but outcome-unnecessary repair is measurable.
