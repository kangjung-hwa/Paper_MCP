# V3 Operational Validity Report

## 1. 기존 EPVR의 의미

v3의 기존 `GT_valid`/`EPVR`은 모든 mandatory execution condition을 완전히 만족했는지를 의미한다. 이번 추가 평가에서는 이 값을 더 명확하게 `SCCR`로 병기한다.

```text
SCCR = Strict Condition Conformance Rate
```

즉 SCCR은 schema/semantic type, reference frame, unit, freshness, confidence, provenance requirement가 모두 strict하게 만족되는 비율이다.

## 2. SCCR로 재정의한 이유

기존 EPVR은 실행계획 유효성이라는 넓은 개념과 strict conformance를 혼동할 수 있었다. 논문에서는 다음 네 개념을 분리해서 사용한다.

1. Schema Connectivity: public schema/semantic type 수준 연결성
2. SCCR: 모든 strict execution condition 완전 만족
3. OEPVR: operational tolerance 내 실행 가능성
4. TSR: 최종 task outcome 성공

## 3. OEPVR 정의

`GT_operational_valid`는 Tool chain이 실제 운용 허용범위에서 실행 가능한지를 평가한다. `GT_success`와 동일하게 정의하지 않는다. OEPVR은 `GT_operational_valid=1`의 비율이다.

## 4. Hard/Tolerable Condition 기준

Hard condition은 operational tolerance 없이 strict requirement를 그대로 적용한다.

- schema mismatch
- semantic type mismatch
- unsupported reference frame
- unit mismatch
- missing mandatory input
- provenance mismatch, when a Tool requires verified input

Tolerable condition은 Tool output 해석이 가능한 범위에서 operational boundary를 둔다. 이 값은 theta/lambda/test result를 보고 조정하지 않았다.

- strict confidence `c`: operational minimum `max(0, c - 0.05)`
- strict max age `a`: operational max age `1.4 * a`

근거: simulator에서 confidence threshold는 desired quality bound이며 0.05 이내 저하는 sensor output 해석 자체를 막지 않는 margin으로 둔다. Freshness는 nominal strict max age 이후에도 hidden world가 변하지 않는 경우 운용상 해석 가능한 구간이 존재한다는 가정으로 40% margin을 둔다.

구현 위치: `src/oracle/operational_validity.py`. Oracle은 `src/orchestration/validator.py`를 호출하지 않는다.

## 5. SCCR vs OEPVR 차이

3 seeds x 300 tasks, 총 900 task per method 기준이다.

| Method | Schema Connectivity | SCCR | OEPVR | TSR |
|---|---:|---:|---:|---:|
| ReAct | 0.667 | 0.467 | 0.498 | 0.467 |
| Schema-Aware | 1.000 | 0.400 | 0.496 | 0.583 |
| Strict | 0.470 | 0.832 | 0.832 | 0.914 |
| Proposed | 0.488 | 0.772 | 0.832 | 0.914 |

Strict and Proposed have identical OEPVR (`0.832`) and TSR (`0.914`), while Proposed has lower SCCR (`0.772` vs `0.832`).

## 6. Strict vs Proposed 결과

| Metric | Strict | Proposed | Delta Proposed-Strict |
|---|---:|---:|---:|
| SCCR | 0.832 | 0.772 | -0.060 |
| OEPVR | 0.832 | 0.832 | 0.000 |
| TSR | 0.914 | 0.914 | 0.000 |
| OURR | 0.558 | 0.502 | -0.056 |
| Repair Rate | 1.000 | 0.473 | -0.527 |
| Repair F1 | 0.353 | 0.624 | +0.270 |
| Avg Latency | 1553.19 | 1541.74 | -11.45 ms |
| Avg Added Latency | 53.66 | 43.66 | -10.00 ms |
| Avg Tool Calls | 7.426 | 7.366 | -0.060 |

## 7. TSR과의 관계

Validity transition counts show OEPV and TSR are not identical. For Proposed:

- OEPV=1 & TSR=1: 674
- OEPV=1 & TSR=0: 75
- OEPV=0 & TSR=1: 149
- OEPV=0 & TSR=0: 2

Thus operational execution validity and task success remain distinct concepts in the evaluator.

## 8. Invalid-plan Detection 성능

Ground truth positive class is `GT_operational_valid=False`. Prediction score is workflow risk. Threshold classification uses the existing fixed theta.

| Method | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|
| ReAct | 1.000 | 0.666 | 0.799 | 0.899 | 0.981 |
| Schema-Aware | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Strict | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Proposed | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

This result should be interpreted carefully: the current simulator makes operational invalidity highly aligned with residual strict deficits after repair. The metric is useful, but the perfect scores for repair methods should not be overclaimed as real-world generalization.

## 9. Repair 품질

Proposed reduces repair rate from `1.000` to `0.473`, improves repair F1 from `0.353` to `0.624`, and reduces OURR from `0.558` to `0.502`, with no TSR or OEPVR loss in this dataset.

## 10. Cost-aware 결과

Existing v3 cost contribution remains unchanged and is reused for figures/tables. Risk-cost selective repair preserves TSR relative to risk-only selective repair and lowers average added latency.

## 11. Figure 설명

Generated under `results/v3_operational_validity/figures/` in PNG and PDF.

- `fig_validity_hierarchy`: SCCR, OEPVR, TSR hierarchy across methods.
- `fig_conformance_operational_gap`: Strict vs Proposed SCCR/OEPVR gap.
- `fig_repair_quality`: Precision/Recall/F1 for Strict and Proposed.
- `fig_repair_efficiency` and `fig_repair_efficiency_cost`: Repair rate, OURR, added latency/calls.
- `fig_violation_type_effect`: Proposed-Strict differences by violation type.
- `fig_risk_cost`: Risk-only vs Risk-cost contribution.
- `fig_invalid_plan_roc`, `fig_invalid_plan_pr`: risk score vs operational invalidity.
- `fig_validity_transition`: strict conformant, operational-only, operationally invalid stacked states.

## 12. 논문에서 실제 주장 가능한 contribution

Supported:

1. Strict condition conformance and operational execution validity are different concepts.
2. Schema-level connectivity alone is insufficient: Schema-Aware has schema connectivity 1.000 but SCCR 0.400 and OEPVR 0.496.
3. Proposed can reduce repair rate, OURR, added latency, and tool calls while preserving OEPVR and TSR relative to Strict in this simulator.
4. Cost-aware repair selection remains supported as a latency-efficiency contribution, not a success-rate contribution.

Not strongly supported:

1. Strong generalization of perfect invalid-plan detection to real systems. The simulator is still simplified.
2. Structural downstream dependency as a main contribution, per existing v3 downstream ablation.

## 13. Required Q&A

### Q1. Strict Condition Conformance와 Operational Execution Validity는 실제로 다른 값을 보이는가?

Yes. Proposed SCCR is `0.772`, while OEPVR is `0.832`. ReAct and Schema-Aware also show SCCR/OEPVR gaps.

### Q2. `SCCR=0 & OEPV=1`인 workflow가 얼마나 존재하는가?

Across 900 tasks per method: ReAct 28, Schema-Aware 86, Strict 0, Proposed 54. Total across methods: 168.

### Q3. Strict와 Proposed의 SCCR 차이는 몇 %p인가?

Proposed is lower by `6.0 percentage points` (`0.772 - 0.832 = -0.060`).

### Q4. Strict와 Proposed의 OEPVR 차이는 몇 %p인가?

`0.0 percentage points`; both are `0.832`.

### Q5. SCCR 차이보다 OEPVR 차이가 감소하는가?

Yes. SCCR gap is `6.0 pp`, OEPVR gap is `0.0 pp`.

### Q6. Strict와 Proposed의 TSR 차이는 얼마인가?

`0.0 percentage points`; both are `0.914`.

### Q7. Proposed는 동일/유사 OEPVR 및 TSR 수준에서 Repair Rate, OURR, latency를 감소시키는가?

Yes in this run. Repair rate decreases by `52.7 pp`, OURR by `5.6 pp`, average latency by `11.45 ms`, and added latency by `10.00 ms`, with unchanged OEPVR and TSR.

### Q8. Risk Score는 Operationally Invalid Plan을 얼마나 잘 탐지하는가?

For Proposed: Precision `1.000`, Recall `1.000`, F1 `1.000`, ROC-AUC `1.000`, PR-AUC `1.000`. This should be reported with the limitation that operational invalidity is simple in the current simulator.

### Q9. OEPV와 TSR이 서로 다른 사례가 실제 존재하는가?

Yes. Proposed has 75 cases with `OEPV=1 & TSR=0` and 149 cases with `OEPV=0 & TSR=1`.

### Q10. 현재 결과 기준으로 실행계획 유효성을 논문의 핵심 contribution으로 주장할 수 있는가?

Yes, with bounded wording. The results support distinguishing schema connectivity, strict condition conformance, operational execution validity, and task success. They do not support claiming that the current simulator fully captures real-world operational validity.

### Q11. Figure 중 논문 본문에 반드시 넣어야 할 핵심 그림 3~5개를 추천하라.

Recommended main figures:

1. `fig_validity_hierarchy`
2. `fig_validity_transition`
3. `fig_conformance_operational_gap`
4. `fig_repair_efficiency` / `fig_repair_efficiency_cost`
5. `fig_invalid_plan_roc` and `fig_invalid_plan_pr` if space allows
