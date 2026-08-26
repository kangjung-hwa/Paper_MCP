# V3 Report: Validity-Focused MCP Orchestration Experiment

## 1. V2 대비 변경사항

- v2 결과는 `results/v2/`에 그대로 보존했다.
- v3 dataset은 `data/v3/`, v3 결과는 `results/v3/`에 저장한다.
- 기본 risk 식에서 downstream multiplier를 제거했다. 기본 risk는 edge deficit score이고 workflow risk는 사전 고정된 `max edge risk`다.
- Downstream dependency는 `risk_structural_dependency`라는 보조 ablation으로만 유지한다.
- repair cost는 실제 측정 가능한 추가 simulated latency와 추가 call 수만 사용한다.
- Cost contribution 검증을 위해 Strict, Risk-only Selective, Risk-Cost Selective를 별도 비교한다.
- v3 main controlled experiment는 seed `42`, `123`, `2026`의 3회 반복 결과를 합산한다.

## 2. V3 연구 질문

- RQ1: schema 연결이 가능해도 execution condition 불일치로 task failure가 발생하는가?
- RQ2: Strict Repair 대비 risk-based selective repair가 성공률을 크게 낮추지 않으면서 불필요 repair를 줄이는가?
- RQ3: 복수 repair 후보가 있을 때 cost-aware selection이 더 효율적인 repair를 고르는가?

## 3. 실행조건 정의

사용 조건은 schema/semantic type, reference frame, unit, freshness, confidence, provenance로 제한했다. 각 Tool이 현실적으로 요구하지 않는 조건은 추가하지 않는다.

## 4. Risk 식

Edge risk:

```text
R_ij = sum_k w_k d_ij,k
```

기본 가중치는 edge의 사용 조건 수에 대한 균등가중치다. Workflow risk는:

```text
R(W) = max_ij R_ij
```

mean, sum-normalized, structural dependency는 main contribution이 아니라 ablation 대상으로만 둔다.

## 5. Theta/Lambda 선정

현재 구현은 config의 사전 고정값 `theta=0.05`, `lambda=0.25`를 사용한다. Test 결과를 보고 재조정하지 않았다. Sensitivity CSV는 `results/v3/summary/theta_sensitivity.csv`, `lambda_sensitivity.csv`에 저장된다.

## 6. Repair Candidate 정의

Repair 후보는 violation type과 artifact semantic에 따라 제한된다.

- Coordinate: `CoordinateTransform`, `PreciseCoordinateTransform`
- Unit: `UnitConversion`
- Freshness: Position은 `RefreshPosition`, ThreatInfo는 `RefreshThreatInfo`, `FastThreatRefresh`, `SensorBasedThreatRefresh`
- Confidence: `ConfidenceEnhancement`, `SensorFusion`, semantic이 ObjectPosition인 경우 `TrackObject`
- Provenance: `ValidateSource`, ThreatInfo trusted refresh 계열

각 후보는 latency, call 수, output freshness/confidence/provenance 효과가 다르게 정의된다.

## 7. Oracle 평가방법

Oracle은 `src/oracle/simulator.py`, `environment.py`, `task_outcomes.py`를 사용한다. `src/orchestration/validator.py`를 import하거나 호출하지 않는다. `GT_valid`는 mandatory execution precondition 만족 여부, `GT_success`는 hidden world state 기반 task outcome으로 판정한다.

## 8. Main Experiment 결과

3 seeds x 300 tasks 결과다.

| Method | TSR | EPVR | Repair Precision | Repair Recall | Repair F1 | OURR | Avg Tool Calls | Avg Added Calls | Avg Latency | Avg Added Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ReAct | 0.467 | 0.467 | 0.000 | 0.000 | 0.000 | 0.000 | 5.333 | 0.000 | 1208.86 | 0.00 |
| Schema-aware | 0.583 | 0.400 | 0.000 | 0.000 | 0.000 | 0.000 | 5.833 | 0.000 | 1205.11 | 0.00 |
| Strict | 0.914 | 0.832 | 0.214 | 1.000 | 0.353 | 0.558 | 7.426 | 0.533 | 1553.19 | 53.66 |
| Proposed | 0.914 | 0.772 | 0.453 | 1.000 | 0.624 | 0.502 | 7.366 | 0.473 | 1541.74 | 43.66 |

## 9. Strict vs Proposed

- TSR difference: `0.000` percentage points.
- EPVR difference: Proposed is `-0.060` lower.
- OURR difference: Proposed is `-0.056` lower.
- Tool calls: Proposed is `-0.060` calls lower on average.
- Latency: Proposed is `-11.45 ms` lower on average.
- Repair F1 improves from `0.353` to `0.624`.

## 10. Risk-only vs Risk-Cost

| Method | TSR | Risk Reduction | Added Latency | Added Calls | RSCR | RRL |
|---|---:|---:|---:|---:|---:|---:|
| Risk-only Selective | 0.914 | 0.146 | 53.93 | 0.473 | 0.148 | 0.00268 |
| Risk-Cost Selective | 0.914 | 0.146 | 43.66 | 0.473 | 0.148 | 0.00268 |

Cost-aware selection changed the selected repair on `14.8%` of multi-candidate tasks. TSR and call count were unchanged, while added latency decreased by about `10.27 ms`. This supports a limited cost-efficiency claim, not a reliability improvement claim.

## 11. Condition별 결과

Proposed vs Strict showed the largest OURR and latency reductions for freshness and confidence violations.

- freshness: TSR delta `0.000`, OURR delta `-0.319`, latency delta `-46.79 ms`, calls delta `-0.318`
- confidence: TSR delta `0.000`, OURR delta `-0.266`, latency delta `-59.68 ms`, calls delta `-0.237`
- compound: TSR delta `0.000`, OURR delta `-0.029`, latency delta `-6.91 ms`, calls delta `-0.043`
- coordinate/unit/provenance: no measured difference under the current task distribution and candidate set.

Detailed CSV: `results/v3/summary/by_violation_type.csv`.

## 12. Severity별 결과

Detailed CSV: `results/v3/summary/by_severity.csv`. Minor tasks are the main subset where Strict can over-repair because original outcome can still succeed despite invalid execution conditions.

## 13. Downstream Variant

| Method | TSR | EPVR | OURR | Added Latency | Added Calls |
|---|---:|---:|---:|---:|---:|
| Risk-only | 0.914 | 0.772 | 0.502 | 43.66 | 0.473 |
| Risk + structural dependency | 0.880 | 0.728 | 0.545 | 34.78 | 0.437 |

Structural dependency reduced cost but also reduced TSR and EPVR. It is not supported as a main contribution in v3. It should be discussed only as an ablation or limitation.

## 14. 통계 검정

`results/v3/summary/statistical_tests.csv` stores paired statistics. Strict vs Proposed:

- McNemar TSR: b01=0, b10=0, difference 0.
- McNemar GT_valid: b01=0, b10=54, continuity-corrected chi-square 52.02, Proposed lower by 0.06.
- Paired latency difference: Proposed lower by 11.45 ms.
- Paired tool-call difference: Proposed lower by 0.06 calls.

## 15. Sanity Checks

No v3 sanity warnings were emitted. `results/v3/summary/sanity_warnings.txt` is empty.

## 16. Supported Contributions

Supported by current v3 results:

1. Execution-condition checks expose failures missed by schema-only planning.
2. Risk-based selective repair preserves TSR relative to Strict in the current testbed while reducing OURR, latency, and calls.
3. Cost-aware selection changes repair choice in a non-zero subset and reduces added latency without TSR loss versus risk-only selection.

Not supported as a main contribution:

1. Structural downstream dependency as a reliability improvement. It reduces cost but lowers TSR/EPVR in this run.
2. Strong claims about real commercial LLM behavior. LLM validation hooks exist, but the controlled result is deterministic unless API credentials are supplied.

## 17. Required Q&A

### Q1. Schema-aware workflow가 높은 schema 연결성을 가지더라도 실제 execution-condition 문제로 실패하는 사례가 존재하는가?

Yes. In seed 42 alone, Schema-aware has 180 invalid tasks and 105 tasks with both `GT_valid=0` and `GT_success=0`.

### Q2. Proposed는 Strict 대비 TSR을 얼마나 잃거나 얻었는가?

No TSR change in the 3-seed main result: Strict `0.914`, Proposed `0.914`, delta `0.000`.

### Q3. Proposed는 Strict 대비 OURR을 얼마나 줄였는가?

Strict `0.558`, Proposed `0.502`, delta `-0.056`.

### Q4. Proposed는 Strict 대비 Tool Call과 Latency를 얼마나 줄였는가?

Average tool calls decreased by `0.060`; average simulated latency decreased by `11.45 ms`.

### Q5. Risk Score의 Repair Necessity 예측력은 어느 정도인가?

ROC-AUC is `0.789`; PR-AUC is `0.562`. This is meaningful but not strong enough for overclaiming.

### Q6. Risk-Cost가 Risk-only와 실제로 다른 repair를 선택하는가?

Yes. Repair Selection Change Rate is `0.148` among multi-candidate tasks.

### Q7. 다른 repair를 선택했다면 TSR 유지 하에 latency 또는 call 수가 줄었는가?

Yes for latency, not for calls. Risk-only and Risk-Cost both have TSR `0.914` and added calls `0.473`, but added latency decreases from `53.93 ms` to `43.66 ms`.

### Q8. Structural Downstream Dependency를 추가한 것이 유의미한 성능향상을 보이는가?

No. Structural dependency lowered TSR from `0.914` to `0.880` and EPVR from `0.772` to `0.728`, though it reduced cost. It should not be claimed as a main contribution.

### Q9. 어떤 execution condition에서 제안방법의 효과가 가장 크게 나타나는가?

Freshness and confidence. They show the largest OURR and latency reductions with no TSR loss relative to Strict.

### Q10. 현재 v3 결과가 실제로 지원하는 contribution만 목록으로 작성하라.

- Execution-condition-aware validation is necessary beyond schema-only connectivity.
- Selective risk-based repair can reduce unnecessary outcome-level repairs while preserving TSR in this testbed.
- Cost-aware repair selection can reduce added latency without reducing TSR when multiple valid repair candidates exist.
