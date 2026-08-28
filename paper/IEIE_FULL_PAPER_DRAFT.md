# 실행계획 유효성과 위험도 기반 선택적 보완을 고려한 MCP AI 에이전트 오케스트레이션 기법

## An MCP-Based AI Agent Orchestration Method with Execution-Plan Validity and Risk-Aware Selective Repair

> 대한전자공학회 정규논문 투고용 원고 초안. 본문 내 `[삽입]` 표시는 저장소의 실제 그림 또는 결과 파일을 가리킨다. MIRROR-inspired와 Tool-MVR-inspired는 원 논문의 완전 재현이 아니라 비교 목적의 결정론적 구현이다.

---

## 요 약

최근 Model Context Protocol(MCP)을 활용한 AI 에이전트의 도구 연계가 확대되고 있으나, 도구 간 스키마가 연결되더라도 데이터의 단위, 좌표계, 최신성, 신뢰도 등의 실행조건이 충족되지 않으면 실행계획의 운용 유효성이 저하된다. 본 논문은 실행조건의 결손 정도를 기반으로 워크플로의 실행 위험도를 산정하고, 위험도가 임계값을 초과한 경우에만 보완 도구를 삽입하는 MCP 기반 AI 에이전트 오케스트레이션 기법을 제안한다. 복수의 보완 후보가 존재하는 경우 잔여 위험도와 추가 지연시간 및 도구 호출 비용을 함께 고려하여 보완 방법을 선택한다. 실험 결과 제안방법은 OEPVR 83.2%와 TSR 91.4%를 기록하여 Direct Tool-Planning 및 reflection 기반 비교방법보다 높은 실행 유효성과 작업 성공률을 나타냈다. 또한 모든 위반을 보완하는 방식과 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률을 52.7%p 감소시켰다. 실험 결과는 MCP 기반 에이전트 오케스트레이션에서 구조적 도구 연결성뿐 아니라 실행조건의 유효성과 보완 비용을 함께 평가해야 함을 보여준다.

**주요어:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Although Model Context Protocol (MCP) enables AI agents to integrate heterogeneous external tools, schema-level connectivity alone does not guarantee the operational validity of an execution plan when conditions such as units, reference frames, freshness, and confidence are not satisfied. This paper proposes a risk-aware MCP-based AI agent orchestration method that quantifies execution risk from condition deficits and selectively inserts repair tools only when the risk exceeds a predefined threshold. When multiple repair candidates are available, the proposed method jointly considers residual risk, additional latency, and tool-call cost. Experimental results show that the proposed method achieves an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%, outperforming Direct Tool-Planning and reflection-based baselines. It also preserves the same OEPVR and TSR as an all-repair strategy while reducing the repair rate by 52.7 percentage points. The results demonstrate that MCP-based AI agent orchestration requires joint consideration of execution-condition validity and repair cost in addition to structural tool connectivity.

**Keywords:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

# I. 서 론

대규모 언어모델(Large Language Model, LLM)은 자연어 생성과 질의응답을 넘어 외부 도구, API 및 데이터베이스를 호출하여 복합 작업을 수행하는 AI 에이전트의 핵심 구성요소로 활용되고 있다. AI 에이전트의 도구 활용 범위가 확대되면서 단일 도구의 정확한 호출뿐 아니라 사용자 요구에 적합한 복수 도구를 선택하고 실행 순서와 의존관계를 구성하는 tool planning의 중요성이 증가하였다. LLM의 함수 선택 및 인자 생성 능력을 평가하는 Berkeley Function Calling Leaderboard(BFCL)는 단일 함수 호출에서 병렬·순차 호출과 다단계 도구 사용으로 평가 범위를 확장하였다[1]. 실제 응용 서비스의 여러 API를 조합하여 목표를 수행하는 계획 능력을 평가하는 PlanningArena는 도구 선택, 호출 순서 및 복합 실행계획 생성 능력을 평가한다[2]. 두 벤치마크는 LLM 기반 도구 사용 연구의 평가 범위가 단일 호출 정확도에서 복수 도구를 연계한 실행계획으로 확대되었음을 보여준다.

복수 도구를 하나의 에이전트에서 활용하기 위한 인터페이스 표준화도 진행되고 있다. Model Context Protocol(MCP)은 AI 응용과 외부 데이터 및 도구 간 상호작용 방식을 표준화하는 개방형 프로토콜이며, MCP server가 제공하는 tool, resource 및 prompt의 탐색과 호출을 지원한다[3]. MCP 기반 에이전트는 서로 다른 서버에서 제공되는 도구의 입·출력을 연결하여 다단계 실행계획을 구성한다. 그러나 도구 간 입·출력 스키마의 호환성은 실행계획의 운용 유효성을 보장하지 않는다. 동일한 데이터 형식이 연결되더라도 단위, 기준좌표계, 데이터 최신성, 신뢰도 및 출처 조건이 후속 도구의 요구조건과 불일치할 수 있다. 따라서 MCP 기반 다중 도구 실행계획에서는 구조적 연결성과 실행조건 유효성을 구분하여 평가해야 한다.

기존 tool planning 연구는 도구 선택, 호출 순서, 함수 인자 생성 및 schema-level compatibility를 주요 평가 대상으로 설정한다[1], [2]. Reflection 기반 연구는 계획 또는 실행 과정에서 발생한 오류를 추론 단계에서 검토하고 수정한다. MIRROR는 실행 전후의 reflection을 결합하여 tool-use trajectory를 개선하고[4], Tool-MVR은 meta-verification과 Error–Reflection–Correction 구조를 이용하여 도구 사용 오류의 수정 능력을 학습한다[5]. 그러나 구조적으로 연결된 artifact의 운용 조건을 정형화하고, 조건 위반의 크기를 수치화하여 실행 전 보완 여부를 결정하는 방법은 기존 연구의 주요 범위에 포함되지 않는다. 특히 모든 조건 위반을 동일하게 처리하면 운용상 허용 가능한 작은 편차에도 보완 도구가 삽입되어 추가 호출과 지연시간이 증가한다. 실행 유효성을 유지하면서 불필요한 보완을 제한하려면 조건 위반의 크기와 보완 비용을 동시에 고려하는 의사결정 기준이 필요하다.

국내에서도 LLM 기반 작업계획, AI 기능의 단계적 연계 및 멀티에이전트 협업에 관한 연구가 수행되고 있다. 조준형과 정소이는 강화학습 기반 순차 작업계획에 LLM이 생성한 단계별 행동 마스크를 적용하여 탐색 공간을 제한하고 계획 효율을 향상시키는 방법을 제안하였다[6]. 우성영 등은 RAG 프롬프트 기반 레이아웃 생성과 DQN 기반 검증·수정·최적화를 결합하여 생성-검증-최적화 과정을 자동화한 통합 프레임워크를 제안하였다[7]. 이창은 등은 복수 에이전트가 멀티모달 지식 정보를 처리·융합하여 전장 상황인식과 의사결정을 지원하는 유·무인 협업 시스템을 구성하였다[8]. 국내 선행연구는 작업계획, 단계적 AI 기능 연계 및 멀티에이전트 협업 구조를 제시하지만, 복수 도구 사이에서 전달되는 artifact의 실행조건을 정량적으로 평가하고 위험도에 따라 보완 여부를 결정하는 문제는 다루지 않는다.

본 논문은 MCP 기반 다중 도구 실행계획의 실행조건을 명시적으로 모델링하고, 조건 위반의 크기를 기반으로 실행 위험도를 산정한 후 위험도가 임계값을 초과한 경우에만 보완을 수행하는 오케스트레이션 기법을 제안한다. 본 연구의 주요 기여는 다음과 같다.

1. MCP workflow의 tool dependency에 대해 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance의 7개 실행조건을 정의하고 각 조건의 위반 크기를 deficit으로 정량화하였다.
2. 각 tool dependency의 condition deficit을 기반으로 edge risk와 workflow risk를 계산하고, 임계값을 초과한 workflow에 대해서만 보완을 수행하는 risk-aware selective repair를 설계하였다.
3. 복수의 repair candidate가 존재하는 경우 residual risk, 추가 latency 및 tool-call count를 함께 고려하는 risk-cost objective를 정의하였다.
4. 실행계획 평가를 Schema Connectivity, Strict Condition Conformance Rate(SCCR), Operational Execution Plan Validity Rate(OEPVR) 및 Task Success Rate(TSR)로 구분하고, 구조적 연결성·엄격 조건 충족·운용 유효성·최종 작업 성공 간 차이를 실험적으로 분석하였다.

II장에서는 LLM tool planning, reflection 기반 오류 수정 및 MCP 기반 tool ecosystem 관련 연구를 정리한다. III장에서는 실행조건 모델, 위험도 계산 및 선택적 보완 기법을 기술한다. IV장에서는 실험환경, 비교방법 및 평가 지표를 정의한다. V장에서는 외부 비교방법, Strict 방식 및 cost ablation 결과를 분석한다. VI장에서는 실험 결과의 적용 범위와 타당성 위협을 논의하고 VII장에서 결론을 제시한다.

---

# II. 관련 연구

## 1. LLM 기반 Tool Use 및 Tool Planning

LLM 기반 tool use는 사용자 질의를 기반으로 외부 함수 또는 API를 선택하고, 실행에 필요한 인자를 생성하며, 실행 결과를 후속 추론에 반영하는 문제를 다룬다. 초기 연구는 단일 함수 선택과 인자 정확도에 집중하였으나 최근 평가는 복수 도구 간 의존관계와 다단계 실행계획으로 확대되었다.

BFCL은 LLM의 function calling 성능을 정량적으로 평가하는 벤치마크로서 serial, parallel 및 stateful multi-step function calling을 포함한다[1]. BFCL의 평가 대상은 함수 선택과 호출 형식의 정확성을 중심으로 구성된다. PlanningArena는 다양한 응용 서비스의 API를 포함하는 planning benchmark이며, 사용자 요구를 달성하기 위한 도구 선택, 논리적 추론 및 사용자 정보 해석을 평가한다[2]. PlanGenLLMs는 LLM planner를 completeness, executability, optimality, representation, generalization 및 efficiency의 여섯 평가기준으로 정리하였다[9]. 해당 연구들은 복수 도구를 연결하는 계획 능력의 평가 기반을 제공하지만, tool 간 전달 artifact의 단위, 기준좌표계, 최신성, 신뢰도 및 출처를 독립적인 실행조건으로 모델링하지 않는다.

본 연구는 tool selection accuracy 또는 plan generation accuracy를 대체 지표로 사용하지 않는다. 연구 범위는 planner가 생성한 workflow의 각 dependency에서 artifact가 후속 tool의 실행조건을 충족하는지 평가하고, 필요한 보완을 결정하는 orchestration 단계에 한정된다.

## 2. Reflection 기반 오류 수정

LLM agent의 실행 오류를 줄이기 위한 연구는 reflection을 이용하여 계획 또는 실행 결과를 재검토한다. MIRROR는 intended action을 실행하기 전의 intra-reflection과 실행 후 observation을 반영하는 inter-reflection을 결합하여 tool learning 과정의 reasoning trajectory를 개선한다[4]. Tool-MVR은 Multi-Agent Meta-Verification과 Exploration-based Reflection Learning을 결합하고 Error–Reflection–Correction 구조를 통해 tool-use 오류 수정 능력을 학습한다[5].

Reflection 기반 접근은 오류 발생 전후의 reasoning을 수정한다는 점에서 본 연구와 문제 범위가 인접한다. 그러나 reflection의 판단 근거는 주로 tool description, schema, trajectory 및 execution feedback으로 구성된다. 본 연구는 unit, reference frame, freshness, confidence 및 provenance와 같이 정형화 가능한 실행조건을 수치화하고, 보완 판단을 deterministic validation 단계에서 수행한다. 따라서 본 연구의 execution-condition validation은 reflection의 대체가 아니라 구조화된 실행조건에 대한 별도의 검증 계층으로 정의된다.

## 3. MCP 기반 Tool Ecosystem

MCP는 AI application과 외부 데이터 또는 도구 간 상호작용을 표준화하는 protocol이다[3]. Protocol Revision 2025-11-25에서 MCP는 JSON-RPC 2.0 기반의 client-server 통신과 capability negotiation을 정의하며, server primitive로 prompts, resources 및 tools를 제공한다[3]. Tool은 모델이 실행할 수 있는 기능으로 노출된다.

MCP 환경을 대상으로 한 정식 benchmark 연구로 MCP-AgentBench가 제안되었다[10]. MCP-AgentBench는 33개의 operational MCP server와 188개의 tool로 구성된 testbed에서 600개의 query를 평가하고, MCP-mediated tool interaction의 task success를 측정한다. 해당 연구는 MCP 기반 에이전트의 실제 tool-use 평가 범위를 확장하지만 execution-condition deficit과 risk-based selective repair를 평가 대상으로 사용하지 않는다.

MCP의 표준화 대상은 client-server 간 상호작용과 tool interface이다. 표준화된 interface는 서로 다른 provider가 구현한 tool을 하나의 AI application에 연결하는 기반을 제공한다. 반면 domain-specific execution condition은 tool schema만으로 완전하게 표현되지 않는다. 동일 field가 사용하는 물리 단위, 좌표 기준, 허용 데이터 age, confidence threshold 및 provenance requirement는 application-level metadata와 validation을 요구한다. 본 연구는 MCP tool workflow에 execution-condition metadata를 부가하고, tool dependency 단위로 조건 적합성을 평가하는 orchestration layer를 구성한다.

## 4. 기존 연구와 제안방법의 차이

**표 1. 기존 연구와 제안방법의 기능 비교**  
**Table 1. Functional comparison of related approaches and the proposed method**

| Method | Tool selection / planning | Pre-execution review | Post-execution correction | Explicit execution-condition model | Risk-based selective repair | Cost-aware repair |
|---|---:|---:|---:|---:|---:|---:|
| Direct Tool-Planning | O | X | X | X | X | X |
| MIRROR | O | O | O | X | X | X |
| Tool-MVR | O | △ | O | X | X | X |
| **Proposed** | O | **O** | - | **O** | **O** | **O** |

표 1은 관련 연구와 제안방법의 기능 범위를 비교한다. MIRROR와 Tool-MVR은 reflection 또는 error correction을 통해 tool-use trajectory를 개선한다[4], [5]. 제안방법은 execution condition의 deviation을 명시적으로 계산하고, 계산된 risk와 repair cost를 보완 여부 및 후보 선택에 사용한다. 따라서 제안방법의 차별점은 reflection 여부가 아니라 **정형 실행조건의 수치화, 선택적 보완, 비용 기반 후보 선택**에 있다.

---

# III. 제안하는 MCP 기반 오케스트레이션

## 1. 전체 구조

제안방법의 전체 구조는 그림 1과 같다.

**[그림 1 삽입]**  
`results/paper_figures/fig_proposed_architecture.pdf`

**그림 1. 제안하는 위험도 기반 MCP AI 에이전트 오케스트레이션 구조**  
**Fig. 1. Overall architecture of the proposed risk-aware MCP AI agent orchestration**

Planner는 사용자 task와 tool registry를 입력으로 받아 tool sequence와 artifact dependency로 구성된 초기 workflow \(W\)를 생성한다. Execution-condition validator는 workflow의 각 dependency edge에서 upstream artifact의 상태와 downstream tool의 요구조건을 비교한다. Validator 출력은 condition deficit으로 변환되며, 각 edge의 risk와 전체 workflow risk 계산에 사용된다.

Workflow risk가 임계값 이하이면 초기 workflow를 유지한다. Workflow risk가 임계값을 초과하면 위반 condition에 대응하는 repair candidate set을 생성한다. 각 candidate를 적용한 workflow의 residual risk와 repair cost를 계산하고, risk-cost objective가 최소인 candidate를 선택한다. 선택된 repair tool을 workflow에 삽입한 후 수정된 workflow를 실행 단계로 전달한다.

## 2. Execution Condition 모델

Tool \(T_i\)의 출력 artifact가 tool \(T_j\)의 입력으로 전달되는 dependency edge \((i,j)\)를 정의한다. Edge \((i,j)\)에서 후속 tool이 요구하는 실행조건은 식 (1)과 같다.

\[
C_{ij}=(\tau_{ij},s_{ij},u_{ij},r_{ij},t_{ij},q_{ij},p_{ij})
\tag{1}
\]

**표 2. Execution condition 구성요소**  
**Table 2. Execution conditions considered in the proposed method**

| Condition | Symbol | Definition |
|---|---|---|
| Schema type | \(\tau\) | 데이터 구조 및 형식의 호환 조건 |
| Semantic type | \(s\) | artifact가 표현하는 의미 유형 |
| Unit | \(u\) | 물리량 또는 데이터 값의 단위 |
| Reference frame | \(r\) | 좌표계 또는 기준계 |
| Freshness | \(t\) | 허용 가능한 최대 데이터 age |
| Confidence | \(q\) | 요구되는 최소 신뢰도 |
| Provenance | \(p\) | 요구되는 데이터 출처 또는 검증 속성 |

Schema type과 semantic type은 artifact의 구조적·의미적 연결 조건을 정의한다. Unit과 reference frame은 downstream computation에 직접 입력하기 위한 표현 조건을 정의한다. Freshness는 시간 경과에 따른 정보 유효기간을, confidence는 최소 신뢰수준을, provenance는 입력 데이터의 출처 및 검증 요구조건을 정의한다. 제안방법은 총 7개 condition을 독립적으로 평가한다.

## 3. Condition Deficit

실제 artifact condition과 downstream requirement의 차이를 condition deficit으로 정의한다. Edge \((i,j)\)의 deficit vector는 식 (2)와 같다.

\[
D_{ij}=[d_{ij,1},d_{ij,2},\dots,d_{ij,m}]
\tag{2}
\]

Schema type, semantic type, unit, reference frame 및 provenance와 같은 categorical condition의 deficit은 식 (3)으로 계산한다.

\[
d_{ij,k}=\begin{cases}
0,&c^{act}_{ij,k}=c^{req}_{ij,k}\\
1,&c^{act}_{ij,k}\neq c^{req}_{ij,k}
\end{cases}
\tag{3}
\]

최소 요구값을 갖는 continuous condition은 위반 크기를 요구값에 대해 정규화한다. Confidence deficit은 식 (4)로 계산한다.

\[
d_{ij,k}=\min\left(1,\max\left(0,\frac{c^{req}_{ij,k}-c^{act}_{ij,k}}{c^{req}_{ij,k}}\right)\right)
\tag{4}
\]

Freshness condition은 artifact age \(a\)와 허용 최대 age \(a_{\max}\)의 차이를 사용하며 식 (5)로 정의한다.

\[
d^{fresh}_{ij}=\min\left(1,\max\left(0,\frac{a-a_{\max}}{a_{\max}}\right)\right)
\tag{5}
\]

연속형 deficit은 작은 기준 초과와 큰 기준 초과를 구분한다. Binary violation만 사용할 경우 두 편차의 위험도가 동일하게 처리되지만 식 (4)와 식 (5)는 위반 크기를 risk calculation에 반영한다.

## 4. Edge Risk 및 Workflow Risk

각 dependency edge의 execution risk는 condition deficit의 가중합으로 정의한다.

\[
R_{ij}=\sum_{k=1}^{m}w_kd_{ij,k}
\tag{6}
\]

Main experiment에서는 condition 간 사전 중요도 가정을 배제하기 위해 동일한 weight를 적용하였다. Equal weighting은 최적 weight에 대한 주장이 아니라 controlled comparison을 위한 중립적 설정이다.

Workflow risk는 전체 dependency edge 중 최대 edge risk로 정의한다.

\[
R(W)=\max_{(i,j)\in E}R_{ij}
\tag{7}
\]

Max aggregation은 높은 risk를 갖는 단일 dependency가 다수의 정상 dependency에 의해 평균화되는 현상을 방지한다. Main experiment에서는 `risk_mode=max`, `structural_dependency=false`를 사용하였다. Downstream structural dependency를 risk에 추가하는 방식은 별도 ablation에서 평가하였으며 main method에는 포함하지 않았다.

## 5. 실행계획 유효성의 구분

실행계획의 구조적 연결성, 엄격 조건 충족, 운용 유효성 및 최종 task outcome을 동일한 지표로 처리하면 선택적 보완의 효과를 구분할 수 없다. 본 연구는 그림 2와 같이 네 수준의 평가 개념을 정의한다.

**[그림 2 삽입]**  
`results/paper_figures/fig_validity_hierarchy_concept.pdf`

**그림 2. 실행계획 유효성의 개념적 계층**  
**Fig. 2. Conceptual hierarchy of execution-plan validity**

Schema Connectivity는 upstream output과 downstream input의 구조적 연결 여부를 평가한다. Strict Condition Conformance Rate(SCCR)은 모든 mandatory execution condition을 strict requirement에 따라 충족한 workflow의 비율이다. Operational Execution Plan Validity Rate(OEPVR)은 사전에 정의한 operational acceptance envelope를 충족한 workflow의 비율이다. Task Success Rate(TSR)은 independent Oracle이 계산한 최종 task outcome의 성공 비율이다.

Operational validity의 hard categorical condition인 schema, semantic type, unit, reference frame 및 provenance는 strict requirement와 동일하게 설정하였다. Confidence는 strict minimum보다 0.05 낮은 값을 operational minimum으로 설정하였고, freshness의 operational maximum age는 strict maximum age의 1.4배로 설정하였다. 0.05와 1.4는 실험 전에 고정한 simulator parameter이며 외부 표준 또는 실환경 허용치를 의미하지 않는다. 실제 시스템 적용 시 operational envelope는 sensor, tool 및 service specification에서 도출해야 한다.

## 6. Risk-Aware Selective Repair

제안방법은 workflow risk가 식 (8)의 조건을 만족할 때 repair를 수행한다.

\[
R(W)>\theta
\tag{8}
\]

Main experiment의 threshold는 \(\theta=0.05\)로 고정하였다. Strict 방식은 strict condition violation이 존재하면 repair를 수행하지만, Proposed는 normalized risk가 threshold를 초과한 경우에만 repair를 수행한다.

**[그림 3 삽입]**  
`results/paper_figures/fig_selective_repair_example.pdf`

**그림 3. Strict all-repair와 제안하는 selective repair의 개념 비교**  
**Fig. 3. Conceptual comparison between strict all-repair and risk-aware selective repair**

Selective repair의 목적함수는 strict conformance의 최대화가 아니다. Main objective는 OEPVR과 TSR을 보존하면서 운용상 허용 가능한 low-risk deviation에 대한 불필요한 repair를 감소시키는 데 있다.

## 7. Repair Candidate 생성

Repair candidate는 violation type과 candidate tool의 입·출력 condition을 기반으로 생성한다. Coordinate condition에는 `CoordinateTransform`과 `PreciseCoordinateTransform`, unit condition에는 `UnitConversion`, freshness condition에는 `RefreshPosition`, `RefreshThreatInfo`, `FastThreatRefresh` 및 `SensorBasedThreatRefresh`를 사용한다. Confidence condition에는 `ConfidenceEnhancement`, `SensorFusion` 및 대상 artifact에 따라 `TrackObject`를 사용한다. Provenance condition에는 `ValidateSource` 또는 trusted-source 속성을 제공하는 refresh 계열 tool을 사용한다.

동일 condition에 복수 candidate를 허용한 이유는 repair 결과와 실행비용이 candidate별로 다르기 때문이다. Candidate evaluation 단계는 각 candidate 적용 후의 residual risk와 추가 latency 및 tool call 수를 계산한다.

## 8. Risk-Cost Repair Optimization

Candidate \(r\)의 execution cost는 식 (9)로 정의한다.

\[
C(r)=\beta_L\hat L(r)+\beta_N\hat N(r)
\tag{9}
\]

\(\hat L(r)\)은 normalized added latency이며 \(\hat N(r)\)은 normalized added tool-call count이다. Main experiment에서는 \(\beta_L=0.5\), \(\beta_N=0.5\)를 사용하였다. Added latency는 1000 ms로 나눈 후 1로 clipping하였고, added call 수는 3으로 나눈 후 1로 clipping하였다.

Candidate \(r\)을 workflow에 적용한 결과를 \(W\oplus r\)로 정의하면 최종 candidate selection은 식 (10)과 같다.

\[
r^{*}=\arg\min_{r\in\mathcal{R}}\left[R(W\oplus r)+\lambda C(r)\right]
\tag{10}
\]

Main experiment의 cost coefficient는 \(\lambda=0.25\)로 설정하였다. Risk reduction이 없는 candidate는 선택 대상에서 제외한다. Cost term의 역할은 reliability를 직접 증가시키는 것이 아니라 동일한 risk reduction을 제공하는 후보 중 추가 실행비용이 작은 후보를 선택하는 데 있다.

## 9. 전체 알고리즘

**Algorithm 1. Risk-Aware MCP Workflow Repair**

```text
Input:
    Initial workflow W
    Tool registry G
    Risk threshold θ
    Cost coefficient λ

1: Validate dependency edges in W
2: for each edge (i, j) do
3:     Compute condition deficit D_ij
4:     Compute edge risk R_ij
5: end for
6: Compute R(W) = max R_ij
7: if R(W) <= θ then
8:     return W
9: end if
10: Identify conditions contributing to the risk
11: Generate compatible repair candidates
12: for each repair candidate r do
13:     Apply r to obtain candidate workflow W_r
14:     Compute residual risk R(W_r)
15:     Compute repair cost C(r)
16:     Compute J(r) = R(W_r) + λC(r)
17: end for
18: Select r* = argmin J(r) among risk-reducing candidates
19: Insert r* into W
20: Revalidate the repaired workflow
21: return repaired workflow
```

Algorithm 1의 validation과 repair selection은 execution-condition metadata를 사용하여 deterministic하게 수행한다. Planner의 내부 reasoning 과정은 risk calculation에 포함되지 않으며, 동일한 workflow와 condition metadata가 입력되면 동일한 repair decision을 산출한다.

---

# IV. 실험 설계

## 1. 실험 환경 및 Tool Registry

평가환경은 Python 기반 deterministic simulator로 구성하였다. Main experiment에서는 24개의 base tool과 별도의 repair alternative를 등록하였다. Base tool은 information acquisition, conversion, refresh, enhancement, analysis agent, planning, validation 및 visualization 기능으로 구성된다.

**표 3. Testbed의 주요 MCP Tool**  
**Table 3. Major MCP tools used in the testbed**

| Category | Tools |
|---|---|
| Information | GetOwnPosition, DetectObject, GetDestination, GetWeather, GetTerrain, GetThreatInfo |
| Conversion | CoordinateTransform, UnitConversion |
| Refresh | RefreshPosition, RefreshThreatInfo |
| Enhancement | SensorFusion, ConfidenceEnhancement, ValidateSource |
| Agent | ThreatAnalysisAgent, SituationAnalysisAgent, CommunicationAnalysisAgent |
| Planning | RoutePlanning, ThreatAwareRoutePlanning, WeatherAwareRoutePlanning, CommunicationAwareRoutePlanning |
| Validation | RouteValidation |
| Visualization | ResultVisualization |

Tool execution latency는 simulator에 정의된 base latency와 correction/retry latency를 사용한다. 따라서 본 논문의 latency 결과는 실제 LLM 또는 네트워크의 wall-clock latency가 아니라 controlled simulator에서 계산한 execution cost이다.

## 2. Task 구성

Task는 총 6개 family로 구성하였다. F1은 basic route planning, F2는 threat-aware route planning, F3는 weather-aware route planning, F4는 communication-aware route planning, F5는 multi-constraint route planning, F6는 situation analysis and recommendation이다.

Seed당 각 family에서 50개 task를 생성하여 총 300개 task를 구성하였다. 각 family는 normal 20개, minor 15개, critical 15개로 구성된다. Main experiment에서는 seed 42, 123, 2026을 사용하였으며 방법별 총 900개 task execution을 평가하였다.

Minor와 critical label은 Proposed risk function과 독립적으로 생성하였다. Minor case는 strict condition deviation이 존재하더라도 hidden-world task outcome에 직접적인 실패를 유발하지 않는 조건을 포함한다. Critical case는 condition violation과 hidden environment state의 결합이 task failure에 영향을 주도록 구성하였다. Oracle은 비교방법이 접근하지 않는 hidden-world state를 사용하여 strict validity, operational validity 및 task success를 계산한다.

## 3. Violation 구성

Execution-condition violation은 coordinate, unit, freshness, confidence, provenance 및 compound의 6개 group으로 구분하였다.

**표 4. 실행조건 위반 유형**  
**Table 4. Injected execution-condition violations**

| Violation | Definition |
|---|---|
| Coordinate | artifact의 reference frame과 downstream requirement의 불일치 |
| Unit | artifact unit과 downstream requirement의 불일치 |
| Freshness | artifact age가 required maximum age를 초과 |
| Confidence | artifact confidence가 required minimum보다 낮음 |
| Provenance | artifact source/verification property가 requirement를 충족하지 않음 |
| Compound | 2~4개의 condition violation이 동시에 발생 |

Violation injection은 실행조건별 효과와 compound condition에 대한 robustness를 분리하여 분석하기 위해 사용하였다.

## 4. 비교 방법

External comparison에는 Direct Tool-Planning, MIRROR-inspired, Tool-MVR-inspired 및 Proposed를 사용하였다.

**Direct Tool-Planning**은 task와 공개 tool metadata를 이용하여 workflow를 구성하며 별도의 reflection, execution-condition validation 또는 repair를 수행하지 않는다.

**MIRROR-inspired**는 MIRROR[4]의 pre-execution reflection 개념을 비교 목적으로 단순화한 deterministic baseline이다. 실행 전에 public artifact, schema, semantic dependency, goal path, duplicate 및 tool order를 검토하고 public-schema dependency gap에 대한 correction을 수행한다. MIRROR의 full multi-agent learning framework를 재현하지 않았으므로 결과는 원 MIRROR의 성능을 의미하지 않는다.

**Tool-MVR-inspired**는 Tool-MVR[5]의 Error–Reflection–Correction 구조를 비교 목적으로 구현한 deterministic baseline이다. Initial workflow를 먼저 실행한 후 observable public error가 발생한 task에서 reflection, correction 및 retry를 수행한다. Tool-MVR의 training 및 fine-tuning 절차는 포함하지 않았다.

**Proposed**는 execution-condition deficit, workflow risk, threshold 기반 selective repair 및 risk-cost candidate selection을 사용한다.

**[그림 4 삽입]**  
`results/paper_figures/fig_correction_timing_concept.pdf`

**그림 4. 비교 방법별 correction timing**  
**Fig. 4. Correction timing of the compared methods**

Strict 방식은 external baseline이 아니라 Proposed의 selective repair 효과를 평가하기 위한 internal ablation으로 사용하였다. Strict는 strict condition violation이 탐지된 모든 task에 repair를 적용한다.

## 5. Oracle 분리 및 평가 절차

모든 비교방법은 동일한 task set과 tool registry를 입력으로 사용한다. Main planner는 결과 재현성을 위해 deterministic mode로 설정하였으며 temperature는 0.0으로 고정하였다. Proposed의 main parameter는 \(\theta=0.05\), \(\lambda=0.25\), `risk_mode=max`, `structural_dependency=false`이다.

Oracle은 orchestration method가 접근하지 않는 사후 평가 module로 분리하였다. Oracle implementation은 `src/orchestration/validator.py`를 호출하거나 import하지 않으며 독립적인 simulator state와 task outcome logic으로 ground truth를 계산한다. 해당 분리는 Proposed의 validation rule과 evaluation label 사이의 직접적인 함수 재사용을 방지한다.

**[그림 5 삽입]**  
`results/paper_figures/fig_experimental_pipeline.pdf`

**그림 5. 실험 평가 파이프라인**  
**Fig. 5. Experimental evaluation pipeline**

## 6. 평가 지표 및 연구 질문

SCCR은 strict execution condition을 모두 만족한 workflow의 비율이다. OEPVR은 operational acceptance envelope를 만족한 workflow의 비율이다. TSR은 task goal을 성공한 workflow의 비율이다. Repair Rate는 repair가 수행된 task 비율이며, repair precision·recall·F1은 Oracle 기준으로 필요한 repair를 얼마나 정확하게 수행했는지 평가한다. OURR은 unnecessary repair와 관련된 비율을 평가하며, Avg. Added Latency와 Avg. Added Calls는 repair로 증가한 실행비용을 측정한다.

통계 검증은 동일 task에 대한 paired comparison으로 수행하였다. Binary outcome에는 McNemar test를 사용하고 latency와 call count 차이에는 bootstrap confidence interval을 사용하였다.

본 실험은 다음 네 연구질문을 검증한다.

- **RQ1.** Execution-condition validation은 Direct Tool-Planning과 reflection-inspired baseline 대비 OEPVR 및 TSR을 향상시키는가?
- **RQ2.** Pre-execution selective repair와 post-execution correction은 reliability와 execution cost에서 어떤 차이를 나타내는가?
- **RQ3.** Selective repair는 Strict 방식과 동일한 OEPVR 및 TSR을 유지하면서 repair overhead를 감소시키는가?
- **RQ4.** Risk-cost candidate selection은 risk-only selection과 동일한 reliability 조건에서 added latency를 감소시키는가?

---

# V. 실험 결과 및 분석

## 1. RQ1: Execution Validity 비교

표 5는 external comparison의 주요 결과를 제시한다.

**표 5. External baseline과 Proposed의 비교**  
**Table 5. Comparison with external baselines**

**Source:** `results/v4_1_external_baselines/summary/paper_table_external_main.csv`

| Method | SCCR | OEPVR | TSR | Avg. Calls | Avg. Latency (ms) |
|---|---:|---:|---:|---:|---:|
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | **6.167** | **1380.5** |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1818.8 |
| **Proposed** | **0.772** | **0.832** | **0.914** | 7.366 | 1541.7 |

Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였다. MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

Paired comparison에서 Proposed와 Direct의 operational validity difference는 +0.2522였으며 discordant pair는 \(b_{01}=253\), \(b_{10}=26\)이었다. Proposed와 각 reflection-inspired baseline의 operational validity difference는 +0.1667이었으며 discordant pair는 \(b_{01}=228\), \(b_{10}=78\)이었다. TSR comparison에서는 Proposed만 성공한 task가 193개였고 external baseline만 성공한 task는 0개였다.

**[그림 6 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf`

**그림 6. External baseline 대비 SCCR, OEPVR 및 TSR**  
**Fig. 6. SCCR, OEPVR, and TSR compared with external baselines**

Direct Tool-Planning의 Schema Connectivity Rate는 83.3%였으나 SCCR은 53.3%, OEPVR은 58.0%였다. 구조적으로 연결된 workflow 중 일부가 strict 또는 operational execution condition을 충족하지 않았음을 의미한다. Schema connectivity와 operational validity의 차이는 실행계획 평가에서 schema-level compatibility만으로 충분하지 않음을 정량적으로 보여준다.

## 2. RQ2: Correction Timing과 Execution Cost

MIRROR-inspired와 Tool-MVR-inspired는 각각 SCCR 60.0%, OEPVR 66.6%, TSR 70.0%로 동일한 reliability 결과를 기록하였다. 두 baseline 모두 public schema 및 dependency gap에 대한 correction을 수행하지만 execution-condition metadata를 직접 평가하지 않으므로 동일한 task set에서 reliability 차이가 발생하지 않았다.

Correction timing은 실행비용에 차이를 발생시켰다. MIRROR-inspired는 pre-execution correction을 task당 평균 0.333회 수행하였고 평균 added latency는 140.0 ms였다. Tool-MVR-inspired는 initial execution 이후 Error–Reflection–Correction–Retry 절차를 수행하여 평균 added calls 1.500, added latency 495.1 ms를 기록하였다. Tool-MVR-inspired의 비용에는 initial failed execution, correction 및 retry가 포함된다.

Tool-MVR-inspired와 MIRROR-inspired의 평균 total latency difference는 +276.8 ms였으며 95% bootstrap CI는 250.2~306.1 ms였다. 평균 call count difference는 +0.667이며 95% CI는 0.611~0.729였다. Reliability가 동일한 조건에서 post-execution recovery가 pre-execution correction보다 높은 retry cost를 발생시켰다.

Proposed의 total latency는 1541.7 ms로 MIRROR-inspired의 1542.0 ms와 거의 동일하였다. Proposed와 MIRROR-inspired의 latency difference는 -0.27 ms였으며 confidence interval에 0이 포함되었다. Proposed의 평균 call count는 7.366으로 MIRROR-inspired의 6.500보다 높았다. Tool-MVR-inspired와 비교하면 Proposed의 total latency는 277.1 ms 낮았고 평균 call count는 약 0.199 높았다.

**[그림 7 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf`

**그림 7. External baseline과 Proposed의 실행비용 비교**  
**Fig. 7. Execution-cost comparison with external baselines**

External comparison 결과는 Proposed가 모든 cost metric에서 최소값을 갖는다는 주장을 지원하지 않는다. Direct Tool-Planning은 가장 낮은 latency와 call count를 기록하였고 MIRROR-inspired는 Proposed보다 적은 call 수를 사용하였다. Proposed의 external comparison상 이점은 추가 tool call을 사용하는 대신 OEPVR과 TSR을 증가시키고, total latency를 MIRROR-inspired와 유사한 수준으로 유지하며 Tool-MVR-inspired보다 낮게 유지한 점에 있다.

## 3. Violation Type별 분석

Violation type별 결과는 execution-condition validation의 효과가 특정 condition에 집중되는지 확인하기 위해 분석하였다.

Coordinate group에서 Direct Tool-Planning의 OEPVR과 TSR은 각각 29.9%, 43.7%였고 Proposed는 80.5%, 81.6%를 기록하였다. Unit group의 OEPVR은 Direct 30.0%, Proposed 87.8%였다. Provenance group에서는 Direct의 OEPVR과 TSR이 각각 37.8%, 57.8%였고 Proposed는 91.1%, 88.9%였다.

Freshness group의 OEPVR은 Direct 58.0%, Proposed 79.5%였으며 confidence group은 Direct 54.8%, Proposed 82.8%였다. Compound group의 OEPVR은 Direct 35.9%, Proposed 79.3%였고 TSR은 53.3%에서 89.1%로 증가하였다.

**Source:** `results/v4_1_external_baselines/summary/by_violation_type.csv`

Coordinate, unit, provenance 및 compound group에서 OEPVR 차이가 크게 나타났으며 freshness와 confidence에서도 OEPVR 증가가 관찰되었다. Violation type별 결과는 Proposed의 main result가 단일 condition에 의해 형성되지 않았음을 보여준다.

## 4. RQ3: Strict All-Repair와 Selective Repair

Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. SCCR은 Strict 83.2%, Proposed 77.2%로 Proposed가 6.0%p 낮았다. Proposed는 strict condition을 완전히 충족하지 않은 일부 workflow를 유지했지만 operational validity와 task success는 감소하지 않았다.

Validity transition 분석에서 Proposed의 900개 task 중 54개는 `SCCR=0`이면서 `OEPV=1`이었다. 해당 54개 task가 Proposed와 Strict의 SCCR 6.0%p 차이를 구성하였다. Operational-validity pair와 task-success pair에서는 Strict와 Proposed 간 차이가 없었다.

Repair behavior에서는 Strict의 repair rate가 100%였고 Proposed는 47.3%였다. Proposed는 repair rate를 52.7%p 감소시켰다. Repair precision은 Strict 21.4%, Proposed 45.3%, repair F1은 Strict 35.3%, Proposed 62.4%였다. OURR은 55.8%에서 50.2%로 5.6%p 감소하였다. Average added latency는 53.7 ms에서 43.7 ms로 10.0 ms 감소하였고 average added calls는 0.533에서 0.473으로 감소하였다.

**[그림 8 삽입]**  
`results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf`

**그림 8. Strict all-repair 대비 Proposed의 repair 효율성**  
**Fig. 8. Repair efficiency of the proposed method compared with strict all-repair**

Strict comparison은 Proposed의 selective repair가 strict conformance 자체를 최대화하지 않음을 보여준다. 반면 operational validity와 task success를 유지하면서 repair frequency와 added latency를 감소시켰다. 따라서 selective repair의 기여는 모든 strict deviation을 제거하는 데 있지 않고, operational outcome에 영향을 주지 않는 low-risk deviation에 대한 repair를 제한하는 데 있다.

## 5. Severity별 Repair Behavior

Severity 분석은 selective repair가 normal, minor 및 critical case에서 서로 다른 repair behavior를 나타내는지 평가하였다.

Critical case에서 Strict와 Proposed의 TSR은 모두 71.5%였다. Proposed의 repair precision은 약 91.0%, repair F1은 95.3%, repair rate는 78.5%였다. Strict는 모든 critical case에 repair를 적용하므로 repair rate는 100%였다.

Minor case에서 두 방법의 TSR은 모두 100%였다. Proposed의 repair rate는 56.3%로 Strict의 100%보다 낮았다. Normal case에서도 두 방법의 TSR은 모두 100%였으며 Proposed의 repair rate는 17.2%였다. Severity별 결과는 Proposed가 critical case의 repair를 상대적으로 유지하고 minor 및 normal case에서 repair를 더 많이 생략했음을 보여준다.

## 6. RQ4: Risk-Cost Ablation

Cost term의 효과는 Strict, Risk-only Selective 및 Risk-Cost Selective를 비교하여 평가하였다.

**표 6. Risk-cost ablation 결과**  
**Table 6. Ablation study of risk-cost repair selection**

**Source:** `results/v4_1_external_baselines/summary/paper_table_ablation.csv`

| Method | TSR | Added Latency (ms) | Added Calls | Repair F1 |
|---|---:|---:|---:|---:|
| Strict | 0.914 | 53.7 | 0.533 | 0.353 |
| Risk-only Selective | 0.914 | 53.9 | 0.473 | 0.624 |
| **Risk-Cost Selective** | **0.914** | **43.7** | **0.473** | **0.624** |

Risk-only와 Risk-Cost는 TSR 91.4%, repair rate, added calls 및 repair F1에서 동일한 결과를 기록하였다. Added latency는 Risk-only 53.9 ms, Risk-Cost 43.7 ms로 10.2 ms 감소하였다. Multi-candidate task 중 약 14.8%에서 cost term에 의해 선택 candidate가 변경되었다.

Cost ablation은 식 (10)의 cost term이 reliability를 증가시키지 않음을 명확히 한다. Cost term은 동일한 repair decision과 reliability를 유지하면서 더 낮은 latency를 갖는 candidate를 선택하는 역할을 수행하였다.

## 7. 결과 요약

RQ1 결과에서 Proposed는 Direct 및 reflection-inspired baseline보다 높은 OEPVR과 TSR을 기록하였다. RQ2에서는 MIRROR-inspired와 유사한 total latency, Tool-MVR-inspired보다 낮은 total latency를 기록하였으나 external baseline보다 많은 tool call을 사용하였다. RQ3에서는 Strict와 동일한 OEPVR 및 TSR을 유지하면서 repair rate와 added latency를 감소시켰다. RQ4에서는 cost-aware selection이 risk-only selection과 동일한 reliability를 유지하면서 added latency를 감소시켰다.

실험 결과는 제안방법의 기여를 두 단계로 구분한다. 첫 번째 단계는 execution-condition-aware risk calculation을 이용한 operational validity와 task success의 향상이다. 두 번째 단계는 selective repair와 cost-aware candidate selection을 이용한 repair overhead의 제한이다.

---

# VI. 논의 및 타당성 위협

## 1. Simulator 기반 평가의 한계

Main experiment는 결과 재현성과 비교방법 간 조건 통제를 위해 deterministic simulator에서 수행하였다. Tool output, latency, condition violation 및 hidden-world task outcome은 simulator에 의해 생성된다. 따라서 보고된 latency는 실제 MCP server, network 또는 LLM inference의 wall-clock latency를 의미하지 않는다. 실제 MCP deployment에서는 server response time, network delay, model inference latency 및 API failure가 추가된다.

## 2. Planner의 결정론적 설정

Main experiment는 deterministic planner를 사용하였다. 실제 LLM planner에서 발생하는 stochastic plan variation, hallucinated argument 및 reasoning instability는 main result에 포함되지 않았다. 현재 결과는 동일 workflow 생성 조건에서 orchestration layer의 차이를 분리하여 평가한 결과로 해석해야 한다. 실제 LLM planner와의 결합 평가는 외적 타당성 검증을 위한 후속 실험 항목이다.

## 3. Inspired Baseline의 구현 범위

MIRROR-inspired와 Tool-MVR-inspired는 각 원 논문의 완전 재현이 아니다. MIRROR의 multi-agent intra/inter-reflection learning과 Tool-MVR의 meta-verification 및 reflection learning을 재학습하지 않았다. 두 baseline은 correction timing과 public tool-feedback 기반 correction 구조를 controlled simulator에 맞추어 구현하였다. 따라서 본 논문의 수치로 실제 MIRROR 또는 Tool-MVR의 절대 성능 우열을 판단하지 않는다. External comparison의 목적은 pre-execution reflection, post-execution recovery 및 execution-condition-aware pre-validation의 동작 차이를 동일 환경에서 비교하는 데 있다.

## 4. Operational Validity Parameter

OEPVR에 사용한 confidence tolerance 0.05와 freshness multiplier 1.4는 simulator assumption이다. 두 parameter는 실험 결과에 맞추어 조정하지 않고 main experiment 이전에 고정하였다. 그러나 해당 값은 산업 또는 군용 시스템의 표준 허용치를 의미하지 않는다. 실제 적용에서는 sensor accuracy, update period, service-level requirement 및 system safety requirement를 기준으로 operational envelope를 정의해야 한다.

## 5. Risk Weight 및 Hyperparameter

Main experiment는 7개 condition에 동일한 weight를 적용하였다. Equal weighting은 condition 중요도의 최적성을 주장하기 위한 설정이 아니라 domain-specific manual weighting을 배제하기 위한 controlled setting이다. Threshold \(\theta=0.05\)와 cost coefficient \(\lambda=0.25\)도 main experiment에서 고정하였다. Lambda sensitivity 분석에서는 일정 구간에서 TSR이 유지되었으나 본 실험만으로 universal optimum을 주장하지 않는다. 실제 적용에서는 safety requirement와 cost profile에 따라 weight, threshold 및 cost coefficient를 별도로 설정해야 한다.

## 6. 평가 범위

Testbed는 route planning과 situation analysis 중심의 6개 task family 및 24개 base tool로 구성되었다. 결과는 해당 simulator distribution과 tool registry에 대한 비교 결과이다. Software engineering, enterprise workflow, web automation 등 다른 MCP ecosystem에 대한 일반화는 추가 검증이 필요하다. 특히 tool 수, dependency depth, error distribution 및 metadata quality가 달라질 경우 risk distribution과 repair behavior도 변한다.

## 7. Reflection과 Execution-Condition Validation의 관계

본 연구는 reflection 기반 reasoning의 대체를 목표로 하지 않는다. Structured metadata로 검증 가능한 unit, reference frame, freshness, confidence 및 provenance는 deterministic validator가 처리하며, semantic ambiguity와 unstructured execution failure는 LLM reasoning 또는 reflection이 처리하는 구조가 기능적으로 구분된다. 따라서 실제 시스템에서는 execution-condition validation과 reflection을 결합한 hybrid orchestration 구조를 고려할 수 있다. 본 논문의 main experiment는 두 기능의 결합 효과를 평가하지 않았으므로 hybrid architecture의 성능은 후속 연구 범위로 남는다.

---

# VII. 결 론

본 논문은 MCP 기반 AI 에이전트가 생성한 multi-tool execution plan의 실행조건을 정량적으로 평가하고, execution risk와 repair cost를 기반으로 보완 도구를 선택하는 orchestration 기법을 제안하였다. 제안방법은 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance의 7개 execution condition을 정의하고 condition deficit으로부터 edge risk와 workflow risk를 계산한다. Workflow risk가 threshold를 초과한 경우에만 repair를 수행하며, 복수 candidate에 대해서는 residual risk와 normalized latency 및 tool-call cost를 결합한 objective를 사용한다.

24개 base tool과 6개 task family로 구성된 deterministic MCP simulator에서 방법별 900개 task를 평가하였다. Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고 MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

Internal ablation에서 Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. Proposed는 repair rate를 100%에서 47.3%로 감소시켰고 added latency를 53.7 ms에서 43.7 ms로 감소시켰다. Risk-only와 Risk-Cost comparison에서는 동일한 TSR과 repair F1을 유지하면서 added latency가 53.9 ms에서 43.7 ms로 감소하였다.

실험 결과는 MCP 기반 다중 도구 실행계획에서 schema connectivity, strict condition conformance, operational validity 및 task success를 구분하여 평가해야 함을 확인하였다. 또한 execution-condition-aware risk calculation과 selective repair를 결합하면 operational outcome을 유지하면서 불필요한 repair를 제한할 수 있음을 확인하였다.

향후 연구에서는 실제 LLM planner와 실제 MCP server를 결합한 evaluation을 수행하고, tool specification에서 operational tolerance를 직접 추출하는 방법을 검토한다. 추가 연구 항목으로 monetary cost, network overhead 및 server reliability를 포함한 multi-objective repair optimization과 시간에 따라 변하는 artifact condition을 반영한 dynamic risk model을 설정한다.

---

# References

[1] S. G. Patil, H. Mao, F. Yan, C. C.-J. Ji, V. Suresh, I. Stoica, and J. E. Gonzalez, “The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models,” *Proceedings of the 42nd International Conference on Machine Learning*, PMLR, vol. 267, pp. 48371–48392, 2025.

[2] Z. Zheng, T. Cui, C. Xie, J. Pan, Q. Chen, and L. He, “PlanningArena: A Modular Benchmark for Multidimensional Evaluation of Planning and Tool Learning,” *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 31047–31086, 2025. doi: 10.18653/v1/2025.acl-long.1499.

[3] Model Context Protocol, “Model Context Protocol Specification, Protocol Revision 2025-11-25,” 2025.

[4] Z. Guo, B. Xu, X. Wang, and Z. Mao, “MIRROR: Multi-agent Intra- and Inter-Reflection for Optimized Reasoning in Tool Learning,” *Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence*, pp. 117–125, 2025. doi: 10.24963/ijcai.2025/14.

[5] Z. Ma, J. Liu, X. Luo, Z. Huang, Q. Zhu, and W. Che, “Advancing Tool-Augmented Large Language Models via Meta-Verification and Reflection Learning,” *Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2*, pp. 2078–2089, 2025. doi: 10.1145/3711896.3736835.

[6] 조준형, 정소이, “LLM 기반 행동 마스킹을 통한 강화학습 에이전트의 작업 계획 효율성 향상,” *전자공학회논문지*, vol. 63, no. 5, pp. 120–130, 2026. doi: 10.5573/ieie.2026.63.5.120.

[7] 우성영, 연혜은, 김영식, “RAG 프롬프트 및 DQN 강화학습 기반 2단 Op-Amp 레이아웃 자동 생성과 LPE 성능 최적화 통합 시스템,” *전자공학회논문지*, vol. 63, no. 2, pp. 19–31, 2026.

[8] 이창은, 백재욱, 손진희, 이소연, 하영국, “전투병의 인지증강을 위한 멀티에이전트 기반 유무인 협업 시스템,” *전자공학회논문지*, vol. 59, no. 2, pp. 126–134, 2022.

[9] H. Wei, Z. Zhang, S. He, T. Xia, S. Pan, and F. Liu, “PlanGenLLMs: A Modern Survey of LLM Planning Capabilities,” *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 19497–19521, 2025. doi: 10.18653/v1/2025.acl-long.958.

[10] Z. Guo, B. Xu, C. Zhu, W. Hong, X. Wang, and Z. Mao, “MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools,” *Proceedings of the AAAI Conference on Artificial Intelligence*, vol. 40, no. 37, pp. 30888–30896, 2026. doi: 10.1609/aaai.v40i37.40347.

---

# 편집용 Figure/Table 매핑

| 번호 | 권장 위치 | 파일 |
|---|---|---|
| Fig. 1 | III-1 전체 구조 | `results/paper_figures/fig_proposed_architecture.pdf` |
| Fig. 2 | III-5 실행계획 유효성 | `results/paper_figures/fig_validity_hierarchy_concept.pdf` |
| Fig. 3 | III-6 선택적 보완 | `results/paper_figures/fig_selective_repair_example.pdf` |
| Fig. 4 | IV-4 비교방법 | `results/paper_figures/fig_correction_timing_concept.pdf` |
| Fig. 5 | IV-5 실험평가 | `results/paper_figures/fig_experimental_pipeline.pdf` |
| Fig. 6 | V-1 External validity | `results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf` |
| Fig. 7 | V-2 Execution cost | `results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf` |
| Fig. 8 | V-4 Repair efficiency | `results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf` |
| Table 5 | 메인 비교 | `results/v4_1_external_baselines/summary/paper_table_external_main.csv` |
| Table 6 | Cost ablation | `results/v4_1_external_baselines/summary/paper_table_ablation.csv` |
| Violation analysis | V-3 | `results/v4_1_external_baselines/summary/by_violation_type.csv` |

## 편집 메모

2단 편집에서 지면이 부족하면 Fig. 4 correction timing concept를 우선 제거하고, Fig. 5 experimental pipeline을 축소한다. 지면이 남으면 validity transition 54/900과 severity analysis를 별도 표로 추가한다.