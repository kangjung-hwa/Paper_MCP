# V4 External Baseline Report

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
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | 6.167 | 1380.5 |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Proposed | 0.772 | 0.832 | 0.914 | 7.366 | 1541.7 |

## Sanity Warnings

No v4 sanity warnings were emitted.

## Required Questions

**Q1. Proposed가 외부 baseline 대비 OEPVR에서 우수한가?**  
Proposed OEPVR=0.832; best external baseline is MIRROR-inspired with OEPVR=0.666.

**Q2. Proposed가 외부 baseline 대비 TSR에서 우수한가?**  
Proposed TSR=0.914; best external baseline is Direct Tool-Planning with TSR=0.700.

**Q3. Proposed가 external reflection baseline보다 Tool Calls 또는 latency를 줄이는가?**  
Compared with reflection baselines, Proposed average calls/latency are 7.366/1541.7 ms; MIRROR-inspired is 6.500/1542.0 ms and Tool-MVR-inspired is 6.500/1542.0 ms. Proposed has higher tool calls than both reflection baselines in this run, while simulated latency is essentially tied. Direct Tool-Planning remains the cheapest method but has lower OEPVR/TSR.

**Q4. Schema Connectivity가 높아도 SCCR/OEPVR이 낮은 사례가 외부 baseline에서도 확인되는가?**  
Direct Tool-Planning schema connectivity=0.833, SCCR=0.533, OEPVR=0.580; this directly tests schema-level connection versus operational validity.

**Q5. 실행 전 validity/risk evaluation이 실행 후 reflection/correction 대비 어떤 장단점을 보이는가?**  
Pre-execution Proposed avoids some post-hoc correction loops but may keep low-risk non-conformances. Reflection baselines can repair public schema errors after inspection but do not inspect hidden execution conditions before execution.

**Q6. Strict 대비 Proposed는 동일 OEPVR/TSR 수준에서 repair를 줄이는가?**  
Strict OEPVR/TSR=0.832/0.914; Proposed OEPVR/TSR=0.832/0.914. In the v3 operational-validity deltas copied into this evaluation, Proposed changes SCCR by -6.0 percentage points, OEPVR by +0.0 percentage points, TSR by +0.0 percentage points, repair rate by -52.7 percentage points, OURR by -5.6 percentage points, average added latency by -10.0 ms, and average tool calls by -0.06.

**Q7. Risk-Cost는 Risk-only 대비 동일한 reliability에서 latency를 줄이는가?**  
Risk-only TSR=0.914, added latency=53.9; Risk-Cost TSR=0.914, added latency=43.7.

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
