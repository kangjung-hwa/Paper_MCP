# 실행계획 유효성과 위험도 기반 선택적 보완을 고려한 MCP AI 에이전트 오케스트레이션 기법

## An MCP-Based AI Agent Orchestration Method with Execution-Plan Validity and Risk-Aware Selective Repair

---

## 요 약

Model Context Protocol(MCP)은 AI 에이전트가 외부 도구를 표준화된 방식으로 탐색하고 호출할 수 있도록 지원한다. 그러나 도구 간 입·출력 schema가 연결되더라도 전달 데이터의 단위, 기준좌표계, 최신성, 신뢰도 및 출처 조건이 후속 도구의 요구조건과 일치하지 않으면 실행계획의 운용 유효성이 저하될 수 있다. 본 논문은 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터의 실행조건을 명시적으로 정의하고, 조건 위반 정도로부터 실행 위험도를 계산하여 위험도가 임계값을 초과한 경우에만 보완을 수행하는 오케스트레이션 기법을 제안한다. 복수의 보완 후보가 존재할 때는 보완 후의 잔여 위험도와 추가 latency 및 도구 호출 수를 함께 고려하여 보완 방법을 선택한다. 실험 결과 제안방법은 OEPVR 83.2%와 TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고, MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다. 또한 모든 조건 위반을 보완하는 Strict 방식과 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률을 100%에서 47.3%로 감소시켰다. 결과는 MCP 기반 실행계획을 평가할 때 schema 연결성뿐 아니라 전달 데이터의 실행조건과 보완 비용을 함께 고려해야 함을 보여준다.

**주요어:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Although Model Context Protocol (MCP) enables AI agents to integrate heterogeneous external tools, schema-level connectivity alone does not guarantee the operational validity of an execution plan when conditions such as units, reference frames, freshness, confidence, and provenance are not satisfied. This paper proposes a risk-aware MCP-based AI agent orchestration method that explicitly models execution conditions of data exchanged between tools, quantifies execution risk from condition deficits, and selectively inserts repair tools only when the risk exceeds a predefined threshold. When multiple repair candidates are available, the proposed method jointly considers residual risk, additional latency, and tool-call cost. Experimental results show that the proposed method achieves an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%. Compared with Direct Tool-Planning, OEPVR and TSR increase by 25.2 and 21.4 percentage points, respectively. Compared with MIRROR-inspired and Tool-MVR-inspired baselines, OEPVR and TSR increase by 16.7 and 21.4 percentage points, respectively. The proposed method also preserves the same OEPVR and TSR as an all-repair strategy while reducing the repair rate from 100% to 47.3%.

**Keywords:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

# Ⅰ. 서 론

대규모 언어모델(Large Language Model, LLM)은 자연어 생성과 질의응답을 넘어 외부 도구, API 및 데이터베이스를 호출하여 복합 작업을 수행하는 AI 에이전트의 핵심 구성요소로 활용되고 있다. 에이전트가 사용하는 도구의 수와 종류가 증가하면서 단일 함수 호출의 정확도뿐 아니라 사용자 요구에 적합한 여러 도구를 선택하고 실행 순서와 의존관계를 구성하는 tool planning의 중요성이 증가하였다. Berkeley Function Calling Leaderboard(BFCL)는 LLM의 함수 선택과 인자 생성 능력을 단일 호출뿐 아니라 병렬·순차 호출 및 다단계 도구 사용까지 확장하여 평가한다[1]. PlanningArena는 여러 응용 서비스의 API를 조합하여 사용자 목표를 달성하는 과정에서 도구 선택, 논리적 추론 및 다단계 계획 능력을 평가한다[2].

복수 도구를 하나의 에이전트에서 사용할 수 있도록 인터페이스를 표준화하려는 시도도 진행되고 있다. Model Context Protocol(MCP)은 AI 응용과 외부 데이터 및 도구 간 상호작용 방식을 표준화한 개방형 프로토콜이다. MCP server는 tool, resource 및 prompt를 제공하며, client는 server가 제공하는 기능을 탐색하고 호출할 수 있다[3]. MCP를 이용하면 서로 다른 server가 제공하는 도구를 하나의 실행계획에서 연계할 수 있다.

그러나 도구 간 입·출력 schema가 연결된다는 사실만으로 실행계획의 유효성이 보장되지는 않는다. 선행 도구가 생성한 데이터 형식이 후속 도구의 입력 schema와 일치하더라도 데이터의 물리 단위, 기준좌표계, 생성 시점, 신뢰도 또는 출처가 후속 도구의 요구조건과 다를 수 있다. 따라서 MCP 기반 다중 도구 실행계획에서는 구조적 연결성과 실제 실행에 필요한 데이터 조건을 구분하여 평가할 필요가 있다.

기존 tool planning 연구는 도구 선택, 호출 순서, 함수 인자 생성 및 schema 수준의 연결성을 주요 평가 대상으로 설정한다[1], [2]. Reflection 기반 연구는 계획 또는 실행 과정에서 발생한 오류를 추론 단계에서 검토하고 수정한다. MIRROR는 실행 전후의 reflection을 결합하여 tool-use trajectory를 개선하고[4], Tool-MVR은 meta-verification과 Error–Reflection–Correction 구조를 이용하여 도구 사용 오류의 수정 능력을 학습한다[5]. 그러나 도구 간 전달 데이터가 만족해야 하는 실행조건을 정형화하고, 조건 위반 정도를 수치화하여 실행 전에 보완 필요성을 판단하는 문제는 기존 연구의 주된 범위에 포함되지 않는다.

국내에서도 LLM 기반 작업계획, AI 기능의 단계적 연계 및 멀티에이전트 협업에 관한 연구가 수행되고 있다. 조준형과 정소이는 강화학습 기반 순차 작업계획에 LLM이 생성한 단계별 행동 마스크를 적용하여 탐색 공간을 제한하고 계획 효율을 향상시키는 방법을 제안하였다[6]. 우성영 등은 RAG 프롬프트 기반 레이아웃 생성과 DQN 기반 검증·수정·최적화를 결합한 자동화 프레임워크를 제안하였다[7]. 이창은 등은 복수 에이전트가 정보를 처리·융합하여 전장 상황인식과 의사결정을 지원하는 유·무인 협업 시스템을 구성하였다[8]. 해당 연구들은 작업계획과 AI 기능 연계를 다루지만, 여러 도구 사이에서 전달되는 데이터의 실행조건을 정량적으로 평가하고 위험도에 따라 보완 여부를 결정하지는 않는다.

본 논문은 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터의 실행조건을 명시적으로 모델링하고, 조건 위반 정도를 기반으로 실행 위험도를 계산한 후 위험도가 임계값을 초과한 경우에만 보완을 수행하는 오케스트레이션 기법을 제안한다. 또한 복수의 보완 후보 중 잔여 위험도와 실행비용을 함께 고려하여 최종 보완 방법을 선택한다.

---

# Ⅱ. 관련 연구

## 1. LLM 기반 도구 사용 및 작업계획

LLM 기반 tool use는 사용자 질의를 기반으로 외부 함수 또는 API를 선택하고, 실행에 필요한 인자를 생성하며, 실행 결과를 후속 추론에 반영하는 문제를 다룬다. BFCL은 serial, parallel 및 stateful multi-step function calling을 포함하여 LLM의 function calling 성능을 평가한다[1]. PlanningArena는 여러 응용 서비스의 API를 이용하여 사용자 요구를 달성하기 위한 도구 선택, 논리적 추론 및 사용자 정보 해석 능력을 평가한다[2]. PlanGenLLMs는 LLM planning 연구를 정리하고 planning 능력을 completeness, executability, optimality, representation, generalization 및 efficiency의 여섯 기준으로 구분하였다[9].

기존 연구는 LLM이 적절한 도구와 호출 순서를 선택하는 능력을 평가하는 기반을 제공한다. 반면 본 연구는 planner 자체의 도구 선택 정확도를 개선하는 것이 아니라, planner가 생성한 실행계획에서 도구 간 전달 데이터가 후속 도구의 실행조건을 만족하는지 검증하고 필요한 보완을 결정하는 오케스트레이션 단계에 초점을 둔다.

## 2. Reflection 및 MCP 기반 도구 연계

MIRROR는 intended action 실행 전의 intra-reflection과 실행 후 observation을 반영하는 inter-reflection을 결합하여 tool learning 과정의 reasoning trajectory를 개선한다[4]. Tool-MVR은 Multi-Agent Meta-Verification과 Exploration-based Reflection Learning을 결합하고 Error–Reflection–Correction 구조를 통해 도구 사용 오류의 수정 능력을 학습한다[5]. 두 연구는 계획 또는 실행 오류를 검토하고 수정한다는 점에서 본 연구와 문제 범위가 인접하지만, unit, reference frame, freshness, confidence 및 provenance와 같은 정형 실행조건을 별도의 수치로 평가하지 않는다.

MCP는 AI application과 외부 데이터 및 도구 간 상호작용을 표준화하는 protocol이다[3]. Protocol Revision 2025-11-25는 JSON-RPC 2.0 기반 client-server 통신과 capability negotiation을 정의하고, server primitive로 prompts, resources 및 tools를 제공한다. MCP 환경을 대상으로 한 MCP-AgentBench는 33개의 operational MCP server와 188개의 tool로 구성된 testbed에서 600개의 query를 평가하여 MCP-mediated tool interaction의 task success를 측정한다[10].

MCP가 표준화하는 주요 대상은 client-server 상호작용과 tool interface이다. 따라서 표준화된 schema는 서로 다른 provider의 도구를 연결하기 위한 기반을 제공하지만, 특정 응용에서 요구되는 물리 단위, 기준좌표계, 최대 데이터 age, 최소 confidence 및 provenance 요구조건까지 자동으로 보장하지는 않는다. 본 연구는 해당 조건을 실행계획 검증 단계에 명시적으로 포함한다.

---

# Ⅲ. 제안하는 위험도 기반 MCP 오케스트레이션 기법

## 1. 실행조건 및 위험도 산정

Planner는 사용자 task와 tool registry를 입력으로 받아 도구 실행 순서와 데이터 의존관계로 구성된 초기 실행계획 \(W\)를 생성한다. 도구 \(T_i\)의 출력 데이터가 도구 \(T_j\)의 입력으로 전달되는 의존관계 \((i,j)\)에서 후속 도구가 요구하는 실행조건을 식 (1)과 같이 정의한다.

\[
C_{ij}=(\tau_{ij},s_{ij},u_{ij},r_{ij},t_{ij},q_{ij},p_{ij})
\tag{1}
\]

여기서 \(\tau\)는 schema type, \(s\)는 semantic type, \(u\)는 unit, \(r\)은 reference frame, \(t\)는 freshness, \(q\)는 confidence, \(p\)는 provenance를 의미한다.

**표 1. 실행조건 구성요소**  
**Table 1. Execution conditions considered in the proposed method**

| Condition | Symbol | Definition |
|---|---|---|
| Schema type | \(\tau\) | 데이터 구조 및 형식의 호환 조건 |
| Semantic type | \(s\) | 전달 데이터가 의미하는 정보 유형 |
| Unit | \(u\) | 물리량 또는 데이터 값의 단위 |
| Reference frame | \(r\) | 좌표계 또는 기준계 |
| Freshness | \(t\) | 허용 가능한 최대 데이터 age |
| Confidence | \(q\) | 요구되는 최소 신뢰도 |
| Provenance | \(p\) | 요구되는 데이터 출처 또는 검증 속성 |

선행 도구가 생성한 데이터의 실제 조건과 후속 도구의 요구조건 차이를 실행조건 결손도(condition deficit)로 정의한다. 의존관계 \((i,j)\)의 결손도 벡터는 식 (2)와 같다.

\[
D_{ij}=[d_{ij,1},d_{ij,2},\dots,d_{ij,m}]
\tag{2}
\]

Schema type, semantic type, unit, reference frame 및 provenance와 같이 일치 여부로 판단하는 조건은 식 (3)과 같이 계산한다.

\[
d_{ij,k}=\begin{cases}
0,&c^{act}_{ij,k}=c^{req}_{ij,k}\\
1,&c^{act}_{ij,k}\neq c^{req}_{ij,k}
\end{cases}
\tag{3}
\]

최소 요구값을 갖는 confidence는 식 (4), 데이터 age에 대한 freshness는 식 (5)로 계산한다.

\[
d_{ij,k}=\min\left(1,\max\left(0,\frac{c^{req}_{ij,k}-c^{act}_{ij,k}}{c^{req}_{ij,k}}\right)\right)
\tag{4}
\]

\[
d^{fresh}_{ij}=\min\left(1,\max\left(0,\frac{a-a_{\max}}{a_{\max}}\right)\right)
\tag{5}
\]

식 (4)와 식 (5)는 단순한 위반 여부뿐 아니라 위반 정도를 위험도 계산에 반영하기 위한 것이다. 각 도구 간 의존관계의 위험도는 식 (6)의 가중합으로 계산한다.

\[
R_{ij}=\sum_{k=1}^{m}w_kd_{ij,k}
\tag{6}
\]

본 실험에서는 특정 조건의 중요도를 사전에 높게 설정하는 영향을 배제하기 위해 동일한 가중치를 적용하였다. 전체 실행계획의 위험도는 식 (7)과 같이 의존관계 위험도의 최댓값으로 정의한다.

\[
R(W)=\max_{(i,j)\in E}R_{ij}
\tag{7}
\]

최댓값을 사용하는 이유는 위험도가 큰 단일 의존관계가 여러 정상 의존관계에 의해 평균화되는 것을 방지하기 위함이다.

## 2. 위험도 기반 선택적 보완 및 보완 후보 선택

제안방법은 실행계획 위험도가 식 (8)의 조건을 만족할 때 보완을 수행한다.

\[
R(W)>\theta
\tag{8}
\]

본 실험에서 임계값은 \(\theta=0.05\)로 고정하였다. Strict 방식은 strict condition violation이 하나라도 존재하면 보완을 수행하지만, 제안방법은 정규화된 실행계획 위험도가 임계값을 초과한 경우에만 보완을 수행한다.

위험도가 임계값을 초과하면 위반된 실행조건을 보완할 수 있는 후보 도구를 생성한다. Coordinate 조건에는 `CoordinateTransform`과 `PreciseCoordinateTransform`, unit 조건에는 `UnitConversion`, freshness 조건에는 `RefreshPosition`, `RefreshThreatInfo`, `FastThreatRefresh` 및 `SensorBasedThreatRefresh`를 사용한다. Confidence 조건에는 `ConfidenceEnhancement`, `SensorFusion` 및 대상 데이터에 따라 `TrackObject`를 사용하고, provenance 조건에는 `ValidateSource` 또는 trusted-source 속성을 제공하는 refresh 계열 도구를 사용한다.

보완 후보 \(r\)의 실행비용은 식 (9)와 같이 정의한다.

\[
C(r)=\beta_L\hat L(r)+\beta_N\hat N(r)
\tag{9}
\]

\(\hat L(r)\)은 정규화된 추가 latency이고 \(\hat N(r)\)은 정규화된 추가 도구 호출 수이다. 본 실험에서는 \(\beta_L=0.5\), \(\beta_N=0.5\)를 사용하였다. 추가 latency는 1000 ms로 나눈 뒤 1을 상한으로 제한하였고, 추가 도구 호출 수는 3으로 나눈 뒤 1을 상한으로 제한하였다.

보완 후보 \(r\)을 적용한 실행계획을 \(W\oplus r\)로 정의하면 최종 보완 후보는 식 (10)으로 선택한다.

\[
r^{*}=\arg\min_{r\in\mathcal{R}}\left[R(W\oplus r)+\lambda C(r)\right]
\tag{10}
\]

본 실험에서는 비용 계수 \(\lambda=0.25\)를 사용하였다. 적용 후 위험도가 감소하지 않는 후보는 선택 대상에서 제외하였다. 비용 항은 신뢰성을 직접 높이기 위한 항이 아니라 유사한 위험도 감소 효과를 제공하는 후보 중 실행비용이 작은 후보를 선택하기 위한 항이다.

## 3. 실행 절차

제안방법은 초기 실행계획의 모든 도구 간 의존관계를 검사한 후 각 의존관계의 실행조건 결손도와 위험도를 계산한다. 전체 실행계획 위험도가 임계값 이하이면 초기 실행계획을 그대로 실행한다. 임계값을 초과하면 위반 조건에 대응하는 보완 후보를 생성하고, 각 후보를 적용한 후의 잔여 위험도와 비용을 계산한다. 식 (10)의 목적함수가 최소인 후보를 삽입한 뒤 수정된 실행계획을 다시 검증한다.

**Algorithm 1. Risk-Aware MCP Execution-Plan Repair**

```text
Input: Initial execution plan W, tool registry G, θ, λ
1: Validate all tool dependencies in W
2: Compute condition deficits and dependency risks
3: Compute execution-plan risk R(W)
4: if R(W) <= θ then return W
5: Generate repair candidates for violated conditions
6: Evaluate residual risk and cost for each candidate
7: Select r* minimizing R(W⊕r) + λC(r)
8: Insert r* and revalidate the execution plan
9: return repaired execution plan
```

그림 1은 제안방법의 처리 절차를 나타낸다.

**[그림 1 삽입]**  
`results/paper_figures/fig_proposed_architecture.pdf`

**그림 1. 제안하는 위험도 기반 MCP 오케스트레이션 절차**  
**Fig. 1. Processing flow of the proposed risk-aware MCP orchestration method**

---

# Ⅳ. 실험 및 결과

## 1. 실험 환경 및 비교방법

평가환경은 Python 기반 deterministic simulator로 구성하였다. 본 실험에서는 24개의 기본 도구와 별도의 보완 후보 도구를 등록하였다. Task는 basic route planning, threat-aware route planning, weather-aware route planning, communication-aware route planning, multi-constraint route planning, situation analysis and recommendation의 6개 유형으로 구성하였다.

Seed당 각 유형에서 50개의 task를 생성하여 총 300개의 task를 구성하였으며, seed 42, 123, 2026을 사용하여 방법별 총 900개 task를 평가하였다. 각 유형은 normal 20개, minor 15개, critical 15개로 구성하였다. 실행조건 위반은 coordinate, unit, freshness, confidence, provenance 및 compound의 6개 유형으로 구성하였다. Compound는 2–4개의 조건 위반이 동시에 발생하도록 설정하였다.

비교방법은 Direct Tool-Planning, MIRROR-inspired, Tool-MVR-inspired 및 Proposed로 구성하였다. Direct Tool-Planning은 별도의 실행조건 검증이나 보완을 수행하지 않는다. MIRROR-inspired는 MIRROR[4]의 pre-execution reflection 개념을 단순화하여 실행 전에 공개된 schema와 의존관계를 검토하고 보완한다. Tool-MVR-inspired는 Tool-MVR[5]의 Error–Reflection–Correction 구조를 반영하여 초기 실행 후 observable error가 발생한 경우 보완과 재실행을 수행한다. 두 baseline은 원 논문의 완전 재현이 아니라 동일 simulator에서 correction timing을 비교하기 위한 결정론적 구현이다.

제안방법의 주요 설정은 \(\theta=0.05\), \(\lambda=0.25\), `risk_mode=max`, `structural_dependency=false`이다. Oracle은 제안방법의 validator와 분리된 독립 모듈로 구현하여 strict validity, operational validity 및 task success를 계산하였다.

실행계획 평가는 네 지표로 구분하였다. Schema Connectivity는 선행 도구 출력과 후속 도구 입력의 구조적 연결 여부를 평가한다. Strict Condition Conformance Rate(SCCR)은 모든 실행조건의 엄격한 요구값을 충족한 실행계획의 비율이다. Operational Execution Plan Validity Rate(OEPVR)은 사전에 정의한 운용 허용범위를 충족한 실행계획의 비율이다. Task Success Rate(TSR)은 독립적인 Oracle이 계산한 최종 작업 성공 비율이다.

Operational validity에서 schema, semantic type, unit, reference frame 및 provenance는 strict requirement와 동일한 기준을 사용하였다. Confidence의 운용 최소값은 strict minimum보다 0.05 낮게 설정하였고, freshness의 운용 최대 age는 strict maximum age의 1.4배로 설정하였다. 두 값은 본 simulator에서 실험 전에 고정한 파라미터이며 외부 표준이나 실환경 허용치를 의미하지 않는다.

## 2. 실행 유효성 비교

표 2는 external baseline과 제안방법의 주요 결과를 나타낸다.

**표 2. 비교방법별 실행 유효성 및 실행비용**  
**Table 2. Execution validity and cost of the compared methods**

| Method | SCCR | OEPVR | TSR | Avg. Calls | Avg. Latency (ms) |
|---|---:|---:|---:|---:|---:|
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | **6.167** | **1380.5** |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1818.8 |
| **Proposed** | **0.772** | **0.832** | **0.914** | 7.366 | 1541.7 |

제안방법은 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였다. MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

Paired comparison에서 Proposed와 Direct의 operational validity difference는 +0.2522였으며 discordant pair는 \(b_{01}=253\), \(b_{10}=26\)이었다. Proposed와 각 reflection-inspired baseline의 operational validity difference는 +0.1667이었으며 discordant pair는 \(b_{01}=228\), \(b_{10}=78\)이었다. TSR에서는 Proposed만 성공한 task가 193개였고 external baseline만 성공한 task는 0개였다.

Violation 유형별 분석에서도 차이가 확인되었다. Coordinate에서 Direct의 OEPVR은 29.9%, Proposed는 80.5%였고, unit에서는 30.0%와 87.8%, provenance에서는 37.8%와 91.1%를 기록하였다. Freshness에서는 58.0%와 79.5%, confidence에서는 54.8%와 82.8%, compound에서는 35.9%와 79.3%를 기록하였다. 결과는 제안방법의 OEPVR 증가가 특정 단일 실행조건에만 의존하지 않음을 보여준다.

**[그림 2 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf`

**그림 2. 비교방법별 SCCR, OEPVR 및 TSR**  
**Fig. 2. SCCR, OEPVR, and TSR of the compared methods**

## 3. 보완 시점 및 실행비용 분석

MIRROR-inspired와 Tool-MVR-inspired는 각각 SCCR 60.0%, OEPVR 66.6%, TSR 70.0%로 동일한 유효성 결과를 기록하였다. 두 방법 모두 공개된 schema와 의존관계에 대한 오류는 보완하지만, 본 연구에서 정의한 실행조건 metadata를 직접 평가하지 않기 때문이다.

보완 시점은 실행비용에 차이를 발생시켰다. MIRROR-inspired는 실행 전 보완을 task당 평균 0.333회 수행하였고 평균 added latency는 140.0 ms였다. Tool-MVR-inspired는 초기 실행 이후 Error–Reflection–Correction–Retry 절차를 수행하여 평균 added calls 1.500, added latency 495.1 ms를 기록하였다.

Tool-MVR-inspired의 평균 total latency는 MIRROR-inspired보다 276.8 ms 높았으며 95% bootstrap CI는 250.2–306.1 ms였다. 평균 call count difference는 +0.667이며 95% CI는 0.611–0.729였다. 제안방법의 total latency는 1541.7 ms로 MIRROR-inspired의 1542.0 ms와 통계적으로 유사하였고, Tool-MVR-inspired보다 277.1 ms 낮았다. 반면 평균 도구 호출 수는 제안방법이 MIRROR-inspired와 Tool-MVR-inspired보다 각각 약 0.866회, 0.199회 많았다.

따라서 external comparison에서 제안방법이 모든 비용 지표에서 최소값을 갖는 것은 아니다. 제안방법의 이점은 추가 도구 호출을 사용하는 대신 OEPVR과 TSR을 증가시키고, total latency를 MIRROR-inspired와 유사하게 유지하면서 Tool-MVR-inspired보다 낮게 유지한 점에 있다.

**[그림 3 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf`

**그림 3. 비교방법별 실행비용**  
**Fig. 3. Execution cost of the compared methods**

## 4. 선택적 보완 및 소거 실험

제안방법의 선택적 보완 효과를 확인하기 위해 모든 strict condition violation에 보완을 적용하는 Strict 방식과 비교하였다. Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. SCCR은 Strict 83.2%, Proposed 77.2%로 Proposed가 6.0%p 낮았다. Proposed의 900개 task 중 54개는 strict condition을 완전히 만족하지 않았지만 operational validity는 만족하였다.

보완 수행률은 Strict 100%, Proposed 47.3%로 Proposed가 52.7%p 낮았다. Repair precision은 Strict 21.4%, Proposed 45.3%, repair F1은 각각 35.3%, 62.4%였다. Average added latency는 53.7 ms에서 43.7 ms로 10.0 ms 감소하였고 average added calls는 0.533에서 0.473으로 감소하였다.

비용 항의 효과는 Risk-only와 Risk-Cost를 비교하여 평가하였다. 두 방법은 TSR 91.4%, added calls 0.473, repair F1 0.624로 동일하였다. 반면 added latency는 Risk-only 53.9 ms, Risk-Cost 43.7 ms로 10.2 ms 감소하였다. Multi-candidate task 중 약 14.8%에서 비용 항에 의해 선택된 보완 후보가 변경되었다. 따라서 비용 항은 신뢰성을 증가시키기보다는 동일한 보완 효과를 유지하면서 latency가 낮은 후보를 선택하는 역할을 한다.

**표 3. 선택적 보완 및 비용 항 소거 실험**  
**Table 3. Ablation results for selective repair and cost-aware selection**

| Method | TSR | Added Latency (ms) | Added Calls | Repair F1 |
|---|---:|---:|---:|---:|
| Strict | 0.914 | 53.7 | 0.533 | 0.353 |
| Risk-only Selective | 0.914 | 53.9 | 0.473 | 0.624 |
| **Risk-Cost Selective** | **0.914** | **43.7** | **0.473** | **0.624** |

## 5. 실험 결과에 대한 논의

본 실험은 orchestration layer의 차이를 분리하여 비교하기 위해 deterministic simulator와 deterministic planner를 사용하였다. 따라서 보고된 latency는 실제 MCP server, network 또는 LLM inference의 wall-clock latency가 아니라 simulator에서 정의한 실행비용이다. 또한 OEPVR에 사용한 confidence tolerance 0.05와 freshness multiplier 1.4는 산업 또는 군용 시스템의 표준 허용치가 아니라 실험 전에 고정한 simulator parameter이다. 실제 시스템에서는 sensor accuracy, update period, service-level requirement 및 safety requirement에 따라 운용 허용범위를 정의해야 한다.

MIRROR-inspired와 Tool-MVR-inspired도 각 원 논문의 full learning framework를 재현한 것이 아니다. 두 방법은 pre-execution reflection과 post-execution recovery의 동작 차이를 동일 환경에서 비교하기 위한 baseline으로 구현하였다. 따라서 본 논문의 수치를 실제 MIRROR 또는 Tool-MVR의 절대 성능으로 해석해서는 안 된다.

제안방법은 정형화 가능한 unit, reference frame, freshness, confidence 및 provenance 조건을 결정론적으로 검증한다. 반면 semantic ambiguity나 비정형 실행 오류는 LLM reasoning 또는 reflection이 더 적합할 수 있다. 실제 시스템에서는 실행조건 검증과 reflection을 결합한 hybrid orchestration 구조를 적용할 수 있으며, 해당 결합 효과는 후속 연구에서 검증할 필요가 있다.

---

# Ⅴ. 결 론

본 논문은 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터의 실행조건을 정량적으로 평가하고, 실행 위험도와 보완 비용을 기반으로 필요한 보완을 선택하는 오케스트레이션 기법을 제안하였다. 제안방법은 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance의 7개 실행조건을 정의하고, 조건 결손도로부터 도구 간 의존관계 위험도와 전체 실행계획 위험도를 계산한다. 실행계획 위험도가 임계값을 초과한 경우에만 보완을 수행하며, 복수의 보완 후보가 존재하는 경우 잔여 위험도와 추가 latency 및 도구 호출 수를 함께 고려하여 최종 후보를 선택한다.

24개 기본 도구와 6개 task 유형으로 구성된 deterministic MCP simulator에서 방법별 900개 task를 평가한 결과, 제안방법은 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였으며, MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다. Strict 방식과 비교에서는 동일한 OEPVR과 TSR을 유지하면서 보완 수행률을 100%에서 47.3%로 감소시켰다. 또한 Risk-Cost 방식은 Risk-only 방식과 동일한 TSR과 repair F1을 유지하면서 added latency를 53.9 ms에서 43.7 ms로 감소시켰다.

향후 연구에서는 실제 LLM planner와 실제 MCP server를 결합하여 제안방법의 외적 타당성을 검증하고, tool specification과 sensor specification에서 운용 허용조건을 자동으로 추출하는 방법을 연구할 예정이다. 또한 network overhead, monetary cost 및 server reliability를 포함한 다목적 보완 선택과 시간에 따라 변하는 데이터 조건을 반영한 동적 위험도 모델을 검토한다.

---

# REFERENCES

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
