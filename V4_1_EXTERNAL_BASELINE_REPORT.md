# V4.1 External Baseline Report

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
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | 6.167 | 0.000 | 1380.5 | 0.0 |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 0.333 | 1542.0 | 140.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1.500 | 1818.8 | 495.1 |
| Proposed | 0.772 | 0.832 | 0.914 | 7.366 | 0.473 | 1541.7 | 43.7 |

## 5. MIRROR vs Tool-MVR

MIRROR and Tool-MVR have identical reliability outcomes in this run: same SCCR/OEPVR/TSR = 0.600/0.666/0.700. The reason is that both methods can repair the same public-schema dependency gaps and neither is allowed to inspect hidden execution-condition failures.

Their execution behavior is no longer identical. MIRROR applies pre-execution corrections on 0.333 of tasks, with average pre-correction latency 140.0 ms. Tool-MVR applies post-execution correction/retry on 0.333 of tasks, with average failed-execution latency 567.8 ms, retry latency 332.6 ms, and added latency 495.1 ms. Tool-MVR uses 0.667 more calls and 276.8 ms more latency on average.

## 6. Proposed External Comparison

Proposed has higher OEPVR/TSR than all external baselines in this controlled run: OEPVR=0.832, TSR=0.914. It is not uniformly cheaper. Direct Tool-Planning has fewer calls and lower latency. MIRROR has fewer calls and approximately the same latency. Tool-MVR has fewer calls than Proposed but higher latency because failed execution and retry costs are counted.

Strict vs Proposed remains an ablation, not an external baseline. From the preserved v3 operational-validity results, Strict OEPVR/TSR=0.832/0.914; Proposed OEPVR/TSR=0.832/0.914. Proposed reduces repair rate by 52.7 percentage points, OURR by 5.6 percentage points, average added latency by 10.0 ms, and average tool calls by 0.06 relative to Strict.

Risk-Cost vs Risk-only: Risk-only TSR=0.914, added latency=53.9; Risk-Cost TSR=0.914, added latency=43.7.

## 7. Sanity Warnings

No v4.1 sanity warnings were emitted.

## 8. 논문 주장 가능 범위

Supported: schema-connectable tool plans can still fail strict/operational execution validity; public-schema reflection improves schema connectivity but does not resolve hidden execution-condition failures; pre-execution risk-aware repair improves OEPVR/TSR versus direct/reflection baselines in this simulator; post-execution correction has measurable retry cost; risk-cost selection reduces added latency versus risk-only with the current v3 ablation.

Not supported: exact reproduction of MIRROR or Tool-MVR; claims that Proposed is always more efficient than every external baseline; claims that reflection baselines are weak in general outside this simulator.

## 9. Required Questions

**Q1. MIRROR-inspired와 Tool-MVR-inspired가 실제로 서로 다른 실행 behavior를 보이는가?**  
Yes. MIRROR performs pre-execution correction; Tool-MVR performs post-execution correction and retry. Tool-MVR incurs 0.667 more calls and 276.8 ms more latency on average.

**Q2. 두 방법의 SCCR/OEPVR/TSR 결과가 동일하거나 다르다면 그 이유는 무엇인가?**  
They are identical in SCCR/OEPVR/TSR (yes). Both can fix public dependency errors but neither can use hidden execution conditions, Oracle tolerance, or Proposed risk.

**Q3. Pre-execution reflection은 Direct Planning 대비 OEPVR을 개선하는가?**  
Yes. MIRROR-inspired OEPVR=0.666; Direct Tool-Planning OEPVR=0.580; difference=0.086.

**Q4. Post-execution error correction은 Direct Planning 대비 recovery를 개선하는가?**  
It improves OEPVR from 0.580 to 0.666 and has recovery rate 0.333; TSR remains 0.700, same as Direct in this run.

**Q5. Post-execution correction은 추가 Tool Call/Latency 비용을 발생시키는가?**  
Yes. Tool-MVR added calls=1.500, added latency=495.1 ms.

**Q6. Proposed는 reflection baseline 대비 OEPVR/TSR에서 우수한가?**  
Yes. Proposed OEPVR/TSR=0.832/0.914; MIRROR and Tool-MVR are 0.666/0.700.

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
