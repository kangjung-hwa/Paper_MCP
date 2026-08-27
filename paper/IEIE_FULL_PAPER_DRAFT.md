# 실행계획 유효성과 위험도 기반 선택적 보완을 고려한 MCP AI 에이전트 오케스트레이션 기법

## An MCP-Based AI Agent Orchestration Method with Execution-Plan Validity and Risk-Aware Selective Repair

> 대한전자공학회 정규논문 투고용 원고 초안. 본문 내 `[삽입]` 표시는 저장소의 실제 그림/결과 파일을 가리킨다. 외부 비교군인 MIRROR-inspired와 Tool-MVR-inspired는 원 논문의 완전 재현이 아닌 controlled simulator용 inspired baseline으로 명시한다.

---

## 요 약

최근 대규모 언어모델(Large Language Model, LLM)을 기반으로 외부 도구를 선택하고 실행하는 AI 에이전트가 빠르게 발전하고 있으며, Model Context Protocol(MCP)은 AI 응용과 외부 데이터 및 도구 간 상호운용을 위한 표준화된 인터페이스를 제공한다. 기존 LLM 기반 도구 사용 및 에이전트 계획 연구는 주로 적절한 도구의 선택, 호출 순서 생성, 입력·출력 스키마 연결 또는 실행 후 발생한 오류의 수정에 초점을 두고 있다. 그러나 도구 간 출력과 입력이 구조적으로 연결 가능하다는 사실만으로 생성된 실행계획이 실제 수행 환경에서도 유효함을 보장하기는 어렵다. 예를 들어 입력과 출력의 데이터 형식이 호환되더라도 좌표계, 단위, 데이터 최신성, 신뢰도 및 출처와 같은 실행조건이 후속 도구의 요구조건을 만족하지 못하면 실행 결과가 유효하지 않을 수 있다.

본 논문에서는 MCP 기반 AI 에이전트가 생성한 실행계획에 대해 실행조건을 명시적으로 모델링하고, 조건 위반의 크기를 기반으로 실행 위험도를 정량화하여 필요한 경우에만 보완 도구를 삽입하는 위험도 기반 선택적 오케스트레이션 기법을 제안한다. 각 도구 간 연결에 대해 스키마형, 의미형, 단위, 기준좌표계, 최신성, 신뢰도 및 출처의 결손도를 계산하고, 이를 이용하여 edge 및 workflow 수준의 실행 위험도를 산정한다. 위험도가 사전에 정의된 임계값을 초과하는 경우 복수의 보완 후보를 생성하고, 보완 이후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 함께 고려하는 risk-cost 목적함수를 이용하여 최종 보완 방안을 선택한다.

제안방법은 24개의 기본 도구와 6개의 작업 유형으로 구성된 MCP 모사 환경에서 평가하였다. Seed 42, 123, 2026에 대해 각각 300개의 작업을 생성하여 방법별 총 900개의 task execution을 수행하였다. 실험 결과 제안방법은 Operational Execution Plan Validity Rate(OEPVR) 83.2%, Task Success Rate(TSR) 91.4%를 달성하여 Direct Tool-Planning의 58.0%, 70.0%와 reflection 기반 비교방법의 66.6%, 70.0%보다 높은 결과를 보였다. 또한 모든 실행조건 위반을 보완하는 Strict 방식과 비교할 때 동일한 OEPVR과 TSR을 유지하면서 보완 수행률을 52.7%p 감소시켰으며, risk-cost 기반 후보 선택을 통해 risk-only 방식의 평균 추가 지연시간 53.9 ms를 43.7 ms로 감소시켰다. 이러한 결과는 MCP 에이전트의 실행계획 평가에서 구조적 도구 연결 여부뿐 아니라 실행조건 유효성과 보완 비용을 함께 고려할 필요가 있음을 보여준다.

**Keywords—** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Large language model (LLM)-based agents increasingly perform complex tasks by selecting and invoking external tools. The Model Context Protocol (MCP) provides a standardized interface for connecting AI applications with external data sources and executable tools. Existing tool-use and agent-planning studies have mainly focused on tool selection, call sequencing, schema-level compatibility, or post-execution correction. However, structural compatibility between tool outputs and subsequent tool inputs does not necessarily guarantee that an execution plan is valid under actual operating conditions. Even if input and output schemas are compatible, mismatches in reference frames, units, data freshness, confidence, or provenance may invalidate the resulting workflow.

This paper proposes a risk-aware MCP-based AI agent orchestration method that explicitly models execution conditions and selectively inserts repair tools according to quantified execution risk. For each dependency between tools, deficits are computed for schema type, semantic type, unit, reference frame, freshness, confidence, and provenance. Edge-level and workflow-level execution risks are subsequently calculated from these deficits. If the workflow risk exceeds a predefined threshold, repair candidates are generated, and the candidate minimizing the combined residual-risk and execution-cost objective is selected. The execution cost consists of additional latency and tool-call count.

The proposed method was evaluated in a controlled MCP testbed composed of 24 base tools and six task families. Three random seeds, 42, 123, and 2026, were used to generate 300 tasks per seed, resulting in 900 task executions per method. The proposed method achieved an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%, whereas Direct Tool-Planning achieved 58.0% and 70.0%, and reflection-based baselines achieved 66.6% and 70.0%, respectively. Compared with a strict strategy that repairs every detected condition violation, the proposed method preserved the same OEPVR and TSR while reducing the repair rate by 52.7 percentage points. Furthermore, cost-aware repair selection reduced the average added latency from 53.9 ms to 43.7 ms compared with risk-only selection. These results indicate that MCP-based agent orchestration should account for execution-condition validity and repair cost in addition to structural tool connectivity.

---

# I. 서 론

대규모 언어모델은 자연어 생성과 질의응답 기능을 넘어 외부 도구, API, 데이터베이스 및 실행가능한 소프트웨어 기능을 조합하여 복합적인 목적을 수행하는 AI 에이전트로 발전하고 있다. 이 과정에서 tool use 또는 function calling은 모델이 외부 환경과 상호작용하기 위한 핵심 기능으로 자리 잡고 있다. 최근 Berkeley Function Calling Leaderboard(BFCL)는 단일 함수 호출뿐 아니라 병렬 호출, 순차 호출 및 장기간 상태를 유지하는 multi-step agentic task까지 평가 범위를 확장하였으며, 최신 모델에서도 복합적이고 상태를 유지해야 하는 tool-use 환경에서 상당한 성능 저하가 발생함을 보고하였다[1]. PlanningArena 역시 실제 응용 상황을 모사하는 다양한 API tool을 활용하여 도구 선택, 복합 계획 및 사용자 정보 해석 능력을 평가하였으며, 강력한 최신 모델도 복잡한 tool planning 환경에서는 제한적인 성능을 보이는 것으로 나타났다[2].

이러한 연구 흐름과 함께 AI 응용과 외부 시스템을 연결하기 위한 인터페이스 표준화도 진행되고 있다. Model Context Protocol(MCP)은 client-server 기반 구조에서 tool, resource, prompt 등의 기능을 노출하고 AI 응용이 이를 표준화된 방식으로 발견하고 호출할 수 있도록 하는 개방형 프로토콜이다[3]. MCP와 같은 표준화된 tool interface가 확산되면서 실제 에이전트의 성능은 더 이상 “호출할 수 있는 tool이 존재하는가”만으로 평가하기 어렵다. 에이전트는 여러 MCP server가 제공하는 tool을 조합하여 하나의 workflow를 생성할 수 있으며, 각 tool은 선행 tool의 결과를 다음 tool의 입력으로 사용한다. 이 과정에서 출력과 입력의 schema 또는 semantic type이 일치한다고 해도 실제 데이터의 실행조건까지 항상 만족한다고 볼 수는 없다.

예를 들어 위치 정보를 생성하는 도구의 출력 schema가 `Position`이고 후속 경로계획 도구 역시 `Position`을 요구한다면 두 도구는 schema 수준에서는 정상적으로 연결될 수 있다. 그러나 선행 도구가 WGS84 좌표를 생성하고 후속 도구가 ENU 좌표계를 전제로 할 경우 해당 입력은 직접 실행에 사용할 수 없다. 마찬가지로 meter를 요구하는 도구에 kilometer 단위 데이터가 입력되거나, 생성된 지 오래된 위치 정보가 최신 데이터로 간주되거나, 신뢰도가 요구값보다 낮은 추정치가 전달되는 경우에도 schema 수준에서는 문제를 식별하기 어렵다.

따라서 본 논문에서는 다음 두 개념을 구분한다.

\[
\text{Structural Compatibility} \neq \text{Execution Validity}
\]

더 나아가 실행조건을 엄격하게 만족하지 않는 모든 경우를 반드시 보완하는 것이 바람직하다고 볼 수도 없다. 실제 시스템에서는 일부 연속형 요구조건이 엄격한 기준값을 약간 벗어나더라도 운용 허용범위 내에서는 사용할 수 있다. 반대로 모든 미세한 위반을 강제로 보완할 경우 추가 tool 호출과 latency가 증가하여 전체 workflow 효율이 감소할 수 있다.

국내에서도 LLM Agent와 외부 기능 연계에 관한 연구가 증가하고 있다. Baek 등은 ReAct 구조를 이용해 사용자 특성을 추출하고 Thought–Action–Observation 기반 에이전트를 구성하였으며[4], 제조·산업 응용 분야에서도 AI Agent를 활용한 자동 분석 및 platform orchestration 구조에 대한 연구가 보고되고 있다[5]. 그러나 이러한 연구는 주로 agent reasoning 또는 응용기능 구성에 초점을 두고 있으며, tool 간 artifact 전달 과정의 실행조건을 정량적으로 평가하는 문제는 충분히 다루어지지 않았다.

본 논문은 이러한 문제를 해결하기 위해 MCP tool workflow의 실행조건 유효성을 정량화하고 위험도에 따라 선택적으로 보완하는 오케스트레이션 방법을 제안한다. 본 연구의 주요 기여는 다음과 같다.

1. MCP workflow의 tool dependency에 대해 schema type뿐 아니라 semantic type, unit, reference frame, freshness, confidence, provenance를 포함하는 **execution-condition model**을 정의하고 각 조건의 위반 크기를 deficit으로 정량화한다.
2. 각 tool dependency의 condition deficit을 기반으로 execution risk를 계산하고 workflow 위험도가 threshold를 초과할 경우에만 보완을 수행하는 **risk-aware selective repair**를 제안한다.
3. 복수 repair candidate가 존재하는 경우 residual risk뿐 아니라 추가 latency와 tool-call count를 동시에 고려하는 **risk-cost candidate selection**을 제안한다.
4. 실행계획 평가를 Schema Connectivity, Strict Condition Conformance Rate(SCCR), Operational Execution Plan Validity Rate(OEPVR) 및 Task Success Rate(TSR)의 네 수준으로 구분하여 구조적 연결, 엄격 조건 충족, 운용 유효성 및 최종 task outcome의 차이를 실험적으로 분석한다.

이후 II장에서는 관련 연구를 분석하고, III장에서 제안하는 execution-condition 기반 오케스트레이션 기법을 설명한다. IV장에서는 실험환경과 비교방법을 정의하며, V장에서 연구질문별 실험결과와 ablation을 분석한다. VI장에서는 연구의 한계와 적용 범위를 논의하고 VII장에서 결론을 제시한다.

---

# II. 관련 연구

## 1. Tool-Use 및 Tool Planning

LLM 기반 tool-use 연구는 모델이 자연어 요구를 해석하고 적절한 외부 tool을 선택하며 tool의 입력 parameter를 생성하는 문제에서 시작하였다. 최근에는 single-call correctness보다 복수 tool 간 dependency와 multi-step planning 능력이 중요한 평가대상으로 확대되고 있다.

BFCL은 function calling을 위한 AST 기반 정확도 평가를 제안하고 single, parallel, multiple 및 multi-turn function calling까지 평가한다[1]. 특히 최신 연구에서는 단순한 함수 선택 능력과 실제 agentic execution 성능 사이에 차이가 있음을 강조한다. 이는 tool schema를 정확하게 선택하는 것과 실제 복합 workflow를 안정적으로 실행하는 것이 동일한 문제가 아님을 의미한다.

PlanningArena[2]는 다양한 app과 API tool을 포함하는 planning benchmark를 구성하고 tool selection과 논리적 planning을 동시에 분석하였다. 이들 연구는 tool selection과 planning 능력을 평가하는 데 중요한 기반을 제공하지만, 대부분 도구의 설명, API signature, schema 또는 실행 결과를 중심으로 평가한다. 본 연구가 다루는 핵심 문제는 계획 생성 이후의 **artifact-level execution condition**이다. 즉 올바른 tool을 올바른 순서로 선택했더라도 전달되는 artifact가 요구좌표계, 단위, freshness, confidence 또는 provenance를 충족하는지 여부는 별도의 문제이다.

## 2. Reflection 및 Error Correction

도구 사용 과정에서 발생하는 오류를 줄이기 위해 최근 agent 연구에서는 reflection을 적극적으로 활용한다.

MIRROR는 action 이후에만 수행하던 reflection의 한계를 지적하고, intended action을 실행하기 전에 검토하는 intra-reflection과 실행 이후 observation을 기반으로 trajectory를 수정하는 inter-reflection을 결합한다[6]. 즉 action을 실행하기 전에 잠재적 오류를 검토함으로써 잘못된 trajectory가 진행되는 것을 방지하는 구조이다.

Tool-MVR은 unreliable tool planning과 낮은 reflection 능력을 해결하기 위해 Multi-Agent Meta-Verification과 Exploration-based Reflection Learning을 제안한다[7]. 특히 Error → Reflection → Correction 학습 패러다임을 적용하여 execution feedback을 이용한 오류 수정 능력을 강화한다.

Reflection 계열 방법은 잘못된 계획 또는 실행 오류를 agent reasoning을 통해 수정한다는 점에서 본 연구와 밀접하지만 두 가지 차이가 있다. 첫째, reflection은 주로 natural-language reasoning과 observable execution feedback에 의존한다. 둘째, 실행 전에 tool dependency의 모든 정형조건을 numerical deficit으로 계산하지는 않는다.

본 연구에서는 reflection 자체를 대체하려는 것이 아니라, **정형화 가능한 실행조건에 대해서는 LLM reflection 이전에 deterministic validation을 수행할 수 있다**는 관점에서 접근한다. 즉 schema, unit, reference frame, freshness, confidence, provenance와 같이 기계적으로 검증가능한 조건을 별도의 execution-risk model로 처리한다.

## 3. MCP 기반 Tool Ecosystem

MCP는 AI application과 external data/tool 사이의 연결을 표준화하기 위한 protocol로, client와 server 간 메시지에는 JSON-RPC 2.0을 사용한다. Server는 prompts, resources 및 tools를 제공하고 client는 capability negotiation 이후 해당 기능을 사용할 수 있다[3]. 이러한 구조는 서로 다른 provider가 구현한 tool을 하나의 AI application에서 통합하는 것을 용이하게 한다.

그러나 interface의 표준화는 tool 내부 의미와 실제 실행조건의 완전한 정합성을 자동으로 보장하지 않는다. MCP tool schema가 정확하게 기술될 수 있더라도 동일 field가 어떤 좌표계와 단위를 사용하는지, 생성된 정보가 얼마 동안 유효한지, confidence threshold는 얼마인지 등의 domain-specific condition은 추가 metadata 또는 application-level validation을 필요로 한다. 따라서 MCP 기반 multi-tool workflow가 증가할수록 “tool discovery”와 “tool schema compatibility”뿐 아니라 **execution-condition compatibility**를 검증하는 orchestration layer의 필요성이 커진다.

## 4. 기존 연구와 본 연구의 차이

**표 1. 기존 연구와 제안방법의 비교**  
**Table 1. Comparison of related methods and the proposed approach**

| Method | Tool Selection | Pre-execution Check | Post-execution Correction | Explicit Execution Conditions | Risk-based Selective Repair | Cost-aware Repair |
|---|---:|---:|---:|---:|---:|---:|
| Direct Tool Planning | O | X | X | X | X | X |
| MIRROR | O | O | O | X | X | X |
| Tool-MVR | O | △ | O | X | X | X |
| **Proposed** | O | **O** | - | **O** | **O** | **O** |

표 1에서 볼 수 있듯이 기존 방법은 tool planning 또는 reflection을 통해 trajectory를 개선하지만, 본 연구는 execution condition의 **정량적 deviation**을 직접 계산하고 이를 repair decision에 사용한다는 점에서 차이가 있다.

---

# III. 제안하는 MCP 기반 오케스트레이션

## 1. 전체 구조

제안방법의 전체 구조는 그림 1과 같다.

**[그림 1 삽입]**  
`results/paper_figures/fig_proposed_architecture.pdf`

**그림 1. 제안하는 위험도 기반 MCP AI 에이전트 오케스트레이션 구조**  
**Fig. 1. Overall architecture of the proposed risk-aware MCP AI agent orchestration**

초기 planner는 사용자 task를 기반으로 MCP tool sequence와 artifact dependency로 구성된 workflow \(W\)를 생성한다. 이후 execution-condition validator는 각 tool edge에 전달되는 artifact의 현재 condition과 downstream tool이 요구하는 condition을 비교한다. Validator 결과는 deficit calculation 단계에서 normalized deficit으로 변환되고, edge risk 및 workflow risk를 계산하는 데 사용된다.

Workflow risk가 threshold 이하인 경우 초기 workflow를 그대로 실행한다. 반면 threshold를 초과하는 경우 offending condition에 대응할 수 있는 repair candidate set을 생성한다. 각 후보를 workflow에 가상 적용한 후 residual risk와 추가 cost를 계산하고, risk-cost objective가 최소인 후보를 선택해 최종 workflow에 삽입한다.

## 2. Execution Condition 모델

Tool \(T_i\)의 출력 artifact가 tool \(T_j\)의 입력으로 전달되는 edge \((i,j)\)를 고려한다. 후속 tool이 요구하는 execution condition을 다음과 같이 정의한다.

\[
C_{ij}=(\tau_{ij},s_{ij},u_{ij},r_{ij},t_{ij},q_{ij},p_{ij})
\tag{1}
\]

각 변수의 의미는 표 2와 같다.

**표 2. Execution condition 구성요소**  
**Table 2. Execution conditions considered in the proposed method**

| Condition | Symbol | Description |
|---|---|---|
| Schema type | \(\tau\) | Data structure/type compatibility |
| Semantic type | \(s\) | Semantic role of the artifact |
| Unit | \(u\) | Physical/data unit |
| Reference frame | \(r\) | Coordinate/reference system |
| Freshness | \(t\) | Maximum allowable data age |
| Confidence | \(q\) | Minimum required confidence |
| Provenance | \(p\) | Required source/verification property |

Schema type과 semantic type은 structural 및 semantic connection을 나타낸다. Unit과 reference frame은 artifact가 downstream computation에서 직접 사용가능한지를 결정한다. Freshness는 시간에 따른 정보 유효성을, confidence는 추정값에 대한 최소 신뢰수준을, provenance는 데이터 출처 또는 검증속성을 표현한다.

## 3. Condition Deficit

각 condition의 requirement와 actual value 사이의 편차를

\[
D_{ij}=[d_{ij,1},d_{ij,2},\dots,d_{ij,m}]
\tag{2}
\]

로 정의한다.

Schema, semantic type, unit, reference frame 및 provenance와 같은 categorical condition은 다음과 같이 정의한다.

\[
d_{ij,k}=\begin{cases}
0,&c^{act}_{ij,k}=c^{req}_{ij,k}\\
1,&\text{otherwise}
\end{cases}
\tag{3}
\]

Confidence와 같이 minimum requirement를 갖는 연속형 조건은 다음과 같이 정규화한다.

\[
d_{ij,k}=\min\left[1,\max\left(0,\frac{c^{req}_{ij,k}-c^{act}_{ij,k}}{c^{req}_{ij,k}}\right)\right]
\tag{4}
\]

Freshness의 경우 artifact age를 \(a\), maximum allowable age를 \(a_{\max}\)라 하면

\[
d^{fresh}_{ij}=\min\left[1,\max\left(0,\frac{a-a_{\max}}{a_{\max}}\right)\right]
\tag{5}
\]

로 정의한다. 따라서 요구 age보다 1% 오래된 데이터와 요구 age를 크게 초과한 데이터는 서로 다른 risk contribution을 갖는다.

## 4. Edge Risk 및 Workflow Risk

각 edge의 execution risk는 condition deficit의 weighted sum으로 정의한다.

\[
R_{ij}=\sum_{k=1}^{m}w_kd_{ij,k}
\tag{6}
\]

본 실험에서는 결과에 맞춘 임의의 중요도 부여를 피하기 위해 기본적으로 동일한 condition weight를 사용한다.

워크플로 수준의 위험도는

\[
R(W)=\max_{(i,j)\in E}R_{ij}
\tag{7}
\]

로 정의한다. Average aggregation 대신 maximum을 사용한 이유는 위험한 단일 edge가 다른 정상 edge들에 의해 평균화되는 현상을 방지하기 위해서이다. 특히 multi-tool workflow에서는 한 개의 critical data dependency만 잘못되어도 downstream result가 전체적으로 잘못될 수 있다.

## 5. SCCR, OEPVR 및 TSR의 구분

실행계획 평가에서 strict condition satisfaction과 실제 operational validity를 동일하게 처리하면 minor deviation에 대한 과잉 보완이 발생할 수 있다. 본 연구에서는 그림 2와 같이 네 수준을 구분한다.

**[그림 2 삽입]**  
`results/paper_figures/fig_validity_hierarchy_concept.pdf`

**그림 2. 실행계획 유효성의 개념적 계층**  
**Fig. 2. Conceptual hierarchy of execution-plan validity**

Schema Connectivity는 tool output과 downstream input이 구조적으로 연결 가능한지 평가한다. SCCR(Strict Condition Conformance Rate)은 정의된 mandatory execution condition을 모두 strict하게 만족한 workflow 비율이다. OEPVR(Operational Execution Plan Validity Rate)은 simulator에서 정의된 operational acceptance envelope까지 고려하여 실제 운용상 사용가능한 workflow의 비율이다. TSR(Task Success Rate)은 최종 goal이 성공했는지를 나타낸다.

따라서

\[
\text{Schema Connectivity}\neq\text{SCCR}\neq\text{OEPVR}\neq\text{TSR}
\tag{8}
\]

이다.

본 controlled simulator의 operational validity에서는 hard categorical condition은 그대로 유지하고 confidence minimum은 strict requirement보다 0.05 낮게, freshness max-age는 strict value의 1.4배로 설정하였다. 이는 외부 표준이 아니라 실험 전에 고정한 simulator assumption이며 결과에 맞추어 tuning한 값이 아니다.

## 6. Risk-Aware Selective Repair

Workflow risk가

\[
R(W)>\theta
\tag{9}
\]

일 때만 repair를 수행한다. 본 실험의 threshold는

\[
\theta=0.05
\tag{10}
\]

이다.

Strict 방식에서는 하나의 deficit이라도 발견되면 repair를 수행하는 반면 Proposed는 deficit magnitude와 aggregate risk를 이용하여 low-risk violation을 그대로 유지할 수 있다.

**[그림 3 삽입]**  
`results/paper_figures/fig_selective_repair_example.pdf`

**그림 3. Strict all-repair와 제안하는 selective repair의 비교**  
**Fig. 3. Comparison between strict all-repair and risk-aware selective repair**

이 선택적 구조의 목적은 strict conformance를 무조건 최대화하는 것이 아니라 **operational validity와 task success를 유지하면서 불필요한 repair overhead를 줄이는 것**이다.

## 7. Repair Candidate 생성

Violation type에 따라 대응 가능한 candidate pool을 구성한다. 예를 들어 coordinate mismatch에는 CoordinateTransform 계열을, unit mismatch에는 UnitConversion을 사용할 수 있다. Freshness violation에는 RefreshPosition 또는 RefreshThreatInfo, confidence 부족에는 ConfidenceEnhancement, SensorFusion 등 서로 다른 repair tool을 사용할 수 있다.

복수 candidate가 존재하는 이유는 동일 condition을 개선하더라도 latency와 call cost 및 개선효과가 다를 수 있기 때문이다. 예를 들어 confidence를 개선하는 빠른 단일 enhancement tool은 latency가 작지만 개선폭이 제한적일 수 있고, SensorFusion은 높은 confidence를 제공하는 대신 추가 처리비용이 클 수 있다.

## 8. Risk-Cost Repair Optimization

Candidate \(r\)의 execution cost는

\[
C(r)=\beta_L\hat L(r)+\beta_N\hat N(r)
\tag{11}
\]

로 정의한다. \(\hat L(r)\)은 normalized added latency이고 \(\hat N(r)\)은 normalized added tool-call count이다.

현재 구현은

\[
\beta_L=\beta_N=0.5
\tag{12}
\]

를 사용하며 latency는 1000 ms, call count는 3을 기준으로 normalization한 후 1로 clipping한다.

후보 \(r\)을 workflow에 삽입한 결과를 \(W\oplus r\)라고 하면 최종 selection은

\[
r^{*}=\arg\min_{r\in\mathcal{R}}[R(W\oplus r)+\lambda C(r)]
\tag{13}
\]

으로 정의한다. 본 실험에서는

\[
\lambda=0.25
\tag{14}
\]

를 사용하였다.

## 9. 전체 알고리즘

**Algorithm 1. Risk-Aware MCP Workflow Repair**

```text
Input:
    Initial workflow W
    Tool registry G
    Risk threshold θ
    Cost coefficient λ

1: Validate all dependency edges in W
2: for each edge (i,j) do
3:     compute condition deficit D_ij
4:     compute edge risk R_ij
5: end for
6: R(W) ← max R_ij
7: if R(W) ≤ θ then
8:     return W
9: end if
10: identify violated execution conditions
11: generate repair candidate set R
12: for each repair candidate r in R do
13:     W_r ← apply r to W
14:     calculate residual risk R(W_r)
15:     calculate repair cost C(r)
16:     J(r) ← R(W_r) + λ C(r)
17: end for
18: r* ← argmin J(r)
19: insert r* into W
20: return repaired workflow
```

Algorithm 1은 LLM reasoning에 의존하지 않고 metadata 기반으로 deterministic하게 수행 가능하다는 특징이 있다. 따라서 동일 execution condition specification을 사용할 경우 planner model과 독립적으로 validation 및 repair layer를 적용할 수 있다.

---

# IV. 실험 설계

## 1. Tool Testbed

실험환경에는 총 24개의 기본 tool을 구성하였다. Tool은 information acquisition, conversion, refresh, enhancement, analysis agent, planning, validation 및 visualization으로 구분된다.

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

## 2. Task Family

Task는 총 6개의 family로 구성하였다. F1은 basic route planning, F2는 threat-aware route, F3는 weather-aware route, F4는 communication-aware route, F5는 multi-constraint route, F6는 situation analysis 및 recommendation이다.

각 family는 50개의 task로 구성되고 seed당 300개 task를 생성한다. 각 family에는 normal 20개, minor 15개, critical 15개가 포함된다. Minor와 critical label은 Proposed risk 식으로 결정하지 않고 independent Oracle outcome에 의해 정의한다. Minor case는 strict execution condition을 일부 위반해도 최종 task success에 영향을 주지 않을 수 있고, critical case는 해당 violation이 hidden environment의 obstacle, threat, weather 또는 communication failure와 결합하여 outcome failure로 이어지도록 구성하였다.

## 3. Violation 생성

실험에서는 다음 6가지 violation type을 사용한다.

**표 4. 실행조건 위반 종류**  
**Table 4. Injected execution-condition violations**

| Violation | Example |
|---|---|
| Coordinate | WGS84 → ENU requirement mismatch |
| Unit | kilometer → meter requirement |
| Freshness | artifact age > maximum age |
| Confidence | actual confidence < required confidence |
| Provenance | unverified source for verified requirement |
| Compound | simultaneous 2–4 condition violations |

이를 통해 단일 structural error뿐 아니라 실제 multi-condition artifact의 유효성 문제를 함께 평가한다.

## 4. 비교 방법

본 실험의 external comparison은 다음 네 방법으로 수행한다.

**Direct Tool-Planning**은 task와 public tool metadata만을 이용해 tool selection 및 sequence를 생성하며 별도의 reflection이나 execution-condition validation을 수행하지 않는다.

**MIRROR-inspired**는 MIRROR[6]의 pre-execution intra-reflection 개념을 참고하여 실행 전 public schema, dependency, tool order를 검토한다. 실제 MIRROR의 multi-agent learning은 재현하지 않으므로 정확히 `MIRROR-inspired`로 표현한다.

**Tool-MVR-inspired**는 Tool-MVR[7]의 Error → Reflection → Correction 구조를 참고하며 initial workflow 실행 이후 observable public error가 발생했을 때 correction 및 retry를 수행한다. Training/fine-tuning은 재현하지 않는다.

**Proposed**는 본 연구에서 정의한 execution condition deficit, risk threshold 및 risk-cost repair selection을 사용한다.

**[그림 4 삽입]**  
`results/paper_figures/fig_correction_timing_concept.pdf`

**그림 4. 비교 방법별 correction timing**  
**Fig. 4. Correction timing of the compared methods**

## 5. 공정성 및 Oracle 분리

모든 방법은 동일한 task set, tool registry 및 simulator environment를 사용한다. Seed는 \(\{42,123,2026\}\)이며 seed별 300개, 방법별 총 900개 task를 평가한다.

주요 parameter는 \(\theta=0.05\), \(\lambda=0.25\), deterministic planner, temperature 0.0이며 risk mode는 max이다. Oracle은 planner 또는 baseline이 사용하지 않으며 사후 평가에서만 GT strict validity, operational validity 및 task outcome을 계산한다. Oracle implementation은 orchestration validator와 분리된 별도 module로 구성하여 Proposed risk와 평가 ground truth 사이의 직접적인 함수 재사용을 방지하였다.

**[그림 5 삽입]**  
`results/paper_figures/fig_experimental_pipeline.pdf`

**그림 5. 실험 평가 파이프라인**  
**Fig. 5. Experimental evaluation pipeline**

## 6. 연구 질문

실험은 다음 연구질문을 기준으로 분석한다.

- **RQ1.** Schema-level tool planning과 reflection 기반 방법에 비해 execution-condition validation이 OEPVR 및 TSR을 향상시키는가?
- **RQ2.** Pre-execution selective repair는 post-execution reflection/correction과 비교하여 어떤 reliability-cost trade-off를 보이는가?
- **RQ3.** 모든 violation을 repair하는 Strict 방식에 비해 selective repair가 동일한 operational validity와 success를 유지하면서 불필요한 repair를 감소시키는가?
- **RQ4.** Cost-aware candidate selection은 risk-only 방식 대비 동일 reliability 조건에서 latency를 감소시키는가?

---

# V. 실험 결과

## 1. RQ1: Execution Validity 비교

메인 결과는 표 5와 같다.

**표 5. External baseline과 Proposed의 비교**  
**Table 5. Comparison with external baselines**

**Source:** `results/v4_1_external_baselines/summary/paper_table_external_main.csv`

| Method | SCCR | OEPVR | TSR | Avg. Calls | Avg. Latency |
|---|---:|---:|---:|---:|---:|
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | **6.167** | **1380.5** |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1818.8 |
| **Proposed** | **0.772** | **0.832** | **0.914** | 7.366 | 1541.7 |

Proposed의 OEPVR은 83.2%로 Direct보다 25.2%p, MIRROR-inspired 및 Tool-MVR-inspired보다 16.7%p 높았다. TSR 역시 91.4%로 세 external baseline의 70.0%보다 21.4%p 높았다.

Paired statistics에서도 Proposed와 Direct의 operational-validity effect는 +0.2522, MIRROR 및 Tool-MVR 대비 +0.1667이었다. TSR에서는 Proposed가 성공하고 baseline이 실패한 task가 193개 존재한 반면 반대 case는 0개였다.

**[그림 6 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf`

**그림 6. External baseline 대비 SCCR, OEPVR 및 TSR**  
**Fig. 6. SCCR, OEPVR, and TSR compared with external baselines**

Direct Tool-Planning의 Schema Connectivity Rate는 83.3%인데 SCCR은 53.3%, OEPVR은 58.0%에 그쳤다. 즉 구조적으로 tool들이 연결된 상당수 workflow가 실제 실행조건 관점에서는 유효하지 않았다. 이는 본 연구의 주요 가정인

\[
\text{Schema Connectivity}\not\Rightarrow\text{Execution Validity}
\]

를 실험적으로 뒷받침한다.

## 2. RQ2: Reflection과 Selective Repair 비교

MIRROR-inspired와 Tool-MVR-inspired는 SCCR, OEPVR 및 TSR에서 동일한 결과를 기록하였다. 두 방법은 public schema 및 dependency error를 보완할 수 있지만 hidden execution condition을 직접 검사하지 않기 때문이다.

그러나 execution cost는 달랐다. MIRROR-inspired는 pre-execution correction을 평균 0.333회 수행하여 140.0 ms의 added latency를 발생시켰다. Tool-MVR-inspired는 initial execution 이후 error를 관찰하고 correction/retry를 수행하기 때문에 평균 1.5회의 added call과 495.1 ms의 added latency를 발생시켰다. Proposed는 평균 added calls 0.473, added latency 43.7 ms였다.

Tool-MVR과 MIRROR의 평균 latency difference는 276.8 ms였으며 bootstrap CI는 약 250.2~306.1 ms였다.

**[그림 7 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf`

**그림 7. External baseline과 Proposed의 실행비용 비교**  
**Fig. 7. Execution-cost comparison with external baselines**

이 결과는 correction timing이 reliability뿐 아니라 execution cost에도 영향을 미침을 보여준다. 특히 post-execution correction은 이미 수행한 upstream operation의 비용과 retry cost를 동시에 발생시킨다.

다만 Proposed가 모든 cost metric에서 최적이라고 볼 수는 없다. Direct Tool-Planning은 가장 낮은 tool calls와 latency를 갖고 MIRROR-inspired도 Proposed보다 call 수가 적다. 따라서 Proposed의 장점은 “항상 가장 저렴한 방법”이라기보다 **높은 OEPVR/TSR과 제한된 repair overhead 사이의 trade-off**로 해석해야 한다.

## 3. Violation Type별 분석

제안방법의 특성을 보다 세부적으로 확인하기 위해 violation type별 결과를 분석하였다.

Coordinate violation에서 Direct Tool-Planning의 OEPVR은 약 29.9%, TSR은 약 43.7%였으나 Proposed는 OEPVR 80.5%, TSR 81.6%를 기록하였다. Unit violation 역시 Direct의 OEPVR 30.0%에서 Proposed 87.8%로 증가하였다.

Provenance에서는 Direct의 OEPVR이 약 37.8%인 반면 Proposed는 91.1%였고, TSR도 약 57.8%에서 88.9%로 증가하였다. Freshness의 경우 Direct OEPVR 58.0%, Proposed 79.5%, Confidence는 Direct 54.8%, Proposed 82.8%로 나타났다.

Compound violation에서는 여러 조건이 동시에 위반되기 때문에 다른 case보다 난도가 높았다. Direct OEPVR은 약 35.9%, Proposed는 약 79.3%를 기록했으며 TSR은 53.3%에서 89.1%로 증가하였다.

**Source:** `results/v4_1_external_baselines/summary/by_violation_type.csv`

이 결과는 제안방법의 이점이 특정 단일 조건에만 의존하는 것이 아니라 coordinate, unit, provenance 및 compound condition에서 공통적으로 나타남을 보여준다.

## 4. RQ3: Strict All-Repair와 Selective Repair

Strict method와 Proposed의 OEPVR 및 TSR은 모두 각각 83.2%, 91.4%로 동일하였다. 반면 SCCR은 Strict 83.2%, Proposed 77.2%였다. Proposed가 strict condition을 덜 만족하면서도 operational validity와 task success는 동일하게 유지되었다는 점은 일부 strict deviation을 의도적으로 repair하지 않았음을 의미한다.

Operational transition 분석에서 Proposed는 **54/900개의 task에서 SCCR=0이지만 OEPV=1**이었다. 즉 strict requirement를 완전하게 만족하지 않더라도 simulator-defined operational tolerance에서는 valid한 workflow가 존재하였다.

Strict 대비 Proposed의 변화는 다음과 같다.

- Repair Rate: −52.7%p
- OURR: −5.6%p
- Avg Added Latency: −10.0 ms
- Avg Tool Calls: −0.06
- OEPVR: 변화 없음
- TSR: 변화 없음

따라서 Selective Repair의 기여는 strict conformance를 최대화하는 것이 아니라 **필요 이상의 repair를 줄이면서 operational validity를 보존하는 것**이다.

**[그림 8 삽입]**  
`results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf`

**그림 8. Strict all-repair 대비 Proposed의 repair 효율성**  
**Fig. 8. Repair efficiency of the proposed method compared with strict all-repair**

## 5. RQ4: Risk-Cost Ablation

Cost term의 효과를 확인하기 위해 Strict, Risk-only Selective, Risk-Cost Selective를 비교하였다.

**표 6. Risk-cost ablation 결과**  
**Table 6. Ablation study of risk-cost repair selection**

**Source:** `results/v4_1_external_baselines/summary/paper_table_ablation.csv`

| Method | TSR | Added Latency | Repair F1 |
|---|---:|---:|---:|
| Strict | 0.914 | 53.7 ms | 0.353 |
| Risk-only | 0.914 | 53.9 ms | 0.624 |
| **Risk-Cost** | **0.914** | **43.7 ms** | **0.624** |

Risk-only와 Risk-Cost는 동일한 TSR 및 repair F1을 보였지만 added latency가 약 10.2 ms 감소하였다. 따라서 cost term의 효과는 reliability 향상이 아니라 **동일한 reliability 및 repair decision에서 더 저비용 candidate를 선택하는 것**으로 볼 수 있다.

---

# VI. 논의 및 Threats to Validity

본 실험 결과는 execution-condition-aware orchestration의 가능성을 보여주지만 해석 범위에는 몇 가지 제한이 존재한다.

첫째, 현재 controlled experiment는 reproducibility를 위해 deterministic planner를 사용한다. 따라서 실제 LLM이 생성하는 stochastic plan error, hallucinated tool argument, reasoning variation 등은 본 실험의 main comparison에 포함되지 않는다. Testbed에는 OpenAI-compatible LLM validation hook이 존재하지만 main result는 deterministic mode 기준이다.

둘째, MIRROR-inspired 및 Tool-MVR-inspired는 원 논문의 full reproduction이 아니다. MIRROR는 실제 multi-agent intra/inter reflection framework이고 Tool-MVR은 meta-verification dataset과 reflection learning을 통해 학습된 모델이다. 본 실험에서는 각 연구의 핵심 correction timing과 public-tool feedback 구조를 controlled simulator에 맞춰 deterministic baseline으로 구현하였다. 따라서 본 논문의 수치를 근거로 실제 MIRROR 또는 Tool-MVR 자체보다 Proposed가 우수하다고 일반화해서는 안 된다. 원 논문의 핵심 구조를 반영한 비교이므로 baseline 명칭에는 `-inspired`를 명시하였다.

셋째, OEPVR의 operational tolerance는 실제 군용·산업 장비의 공인 허용치가 아니라 simulator 내부의 사전고정 조건이다. Confidence minimum의 0.05 relaxation과 freshness max-age의 1.4배 허용은 strict conformance와 operational validity를 구분하기 위한 experimental assumption이다. 향후 실제 시스템에서는 tool provider, sensor specification 및 application requirement로부터 operational envelope를 정의해야 한다.

넷째, cost model은 latency와 tool-call count 두 요소만 고려한다. 실제 MCP ecosystem에서는 monetary API cost, server utilization, network traffic, energy consumption 및 failure probability 등 다양한 cost가 존재할 수 있다. 본 연구의 cost 식은 이러한 항목을 추가할 수 있도록 확장 가능하지만 현재 실험에서는 실제로 측정가능한 latency와 calls만 사용하였다.

다섯째, testbed는 route planning과 situation-analysis 중심의 6개 family를 사용한다. 따라서 software engineering, enterprise workflow, web automation 등 전혀 다른 tool ecosystem에서도 동일한 risk distribution을 갖는다고 볼 수 없다. 향후 다양한 domain의 실제 MCP server를 이용해 일반화 여부를 검증할 필요가 있다.

마지막으로 본 연구의 목적은 reflection 기반 agent reasoning을 대체하는 것이 아니다. 오히려 deterministic하게 검증가능한 execution condition은 orchestration layer에서 먼저 검사하고, semantic ambiguity 또는 unstructured failure는 LLM reflection에 맡기는 **hybrid architecture**가 실제 시스템에서는 더 적절할 수 있다.

---

# VII. 결 론

본 논문에서는 MCP 기반 AI 에이전트가 생성한 multi-tool execution plan의 유효성을 평가하고, condition deficit과 execution risk에 따라 필요한 경우에만 repair tool을 삽입하는 위험도 기반 선택적 오케스트레이션 기법을 제안하였다.

기존 tool-planning 연구가 주로 tool selection, schema connectivity 및 trajectory correction을 다루는 것과 달리, 본 연구에서는 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance를 execution condition으로 명시적으로 모델링하였다. 또한 condition violation을 단순 binary 값이 아닌 magnitude 기반 deficit으로 변환하고, workflow risk가 threshold를 초과하는 경우에만 repair를 수행하였다.

복수 repair candidate가 존재할 경우 residual execution risk와 normalized latency 및 tool-call cost를 함께 고려하여 최종 repair를 선택하도록 구성하였다.

24개의 기본 tool과 6개의 task family로 구성된 MCP simulator에서 seed 3개, 방법별 총 900개 task를 평가한 결과 Proposed는 OEPVR 83.2%, TSR 91.4%를 달성하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 높았으며 reflection-inspired baselines 대비 OEPVR은 16.7%p 높았다.

Strict all-repair와의 ablation에서는 Proposed가 strict conformance를 일부 포기하면서도 동일한 OEPVR 및 TSR을 유지했고 repair rate를 52.7%p 감소시켰다. 또한 Risk-Cost selection은 Risk-only 방식과 동일한 reliability 및 repair F1을 유지하면서 평균 added latency를 53.9 ms에서 43.7 ms로 낮추었다.

이러한 결과는 MCP 기반 AI agent orchestration에서 **도구가 연결되는가**, **실행조건을 strict하게 만족하는가**, **운용상 실행 가능한가**, **최종 task가 성공하는가**를 서로 구분해 평가할 필요가 있음을 보여준다.

향후 연구에서는 실제 LLM planner와 실제 MCP server를 결합한 실험으로 확장하고, 실제 서비스 specification 기반 operational tolerance를 정의할 예정이다. 또한 latency 및 calls 외에 monetary cost, network overhead, server reliability를 포함하는 multi-objective repair optimization과 시간에 따라 변화하는 artifact condition을 반영하는 dynamic execution-risk model을 연구할 계획이다.

---

# References

[1] S. G. Patil et al., “The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models,” *Proc. 42nd Int. Conf. Machine Learning (ICML)*, 2025.

[2] Z. Zheng, T. Cui, C. Xie, J. Pan, Q. Chen, and L. He, “PlanningArena: A Modular Benchmark for Multidimensional Evaluation of Planning and Tool Learning,” *Proc. 63rd Annual Meeting of the Association for Computational Linguistics (ACL)*, pp. 31047–31086, 2025.

[3] Model Context Protocol, “Model Context Protocol Specification,” Model Context Protocol, 2025.

[4] S. Baek, S. Lee, and T. Ha, “Persona-Based Review Generation with LLM Agents,” *Proc. 2025 IEIE Summer Conference*, pp. 3994–3998, 2025.

[5] D. Yoon, B. Shim, B. Jeon, W. Na, and J. Kang, “Design of an AI Agent Platform for Supporting the Digital Transformation of Injection Molding Processes,” *Proc. 2025 IEIE Summer Conference*, pp. 4003–4005, 2025.

[6] Z. Guo, B. Xu, X. Wang, and Z. Mao, “MIRROR: Multi-Agent Intra- and Inter-Reflection for Optimized Reasoning in Tool Learning,” *Proc. 34th International Joint Conference on Artificial Intelligence (IJCAI)*, pp. 117–125, 2025.

[7] X. Wang et al., “Advancing Tool-Augmented Large Language Models via Meta-Verification and Reflection Learning,” *Proc. 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining*, pp. 2078–2089, 2025.

[8] Z. Guo, B. Xu, C. Zhu, W. Hong, X. Wang, and Z. Mao, “MCP-AgentBench: Evaluating Real-World Language Agent Performance with MCP-Mediated Tools,” *Proc. AAAI Conf. Artificial Intelligence*, 2026.

[9] H. Wei, Z. Zhang, S. He, T. Xia, S. Pan, and F. Liu, “PlanGenLLMs: A Modern Survey of LLM Planning Capabilities,” *Proc. 63rd Annual Meeting of the Association for Computational Linguistics (ACL)*, 2025.

[10] Z. Luo et al., “MCP-Universe: Benchmarking Large Language Models with Real-World Model Context Protocol Servers,” *arXiv preprint arXiv:2508.14704*, 2025.

---

# 편집용 Figure/Table 매핑

| 번호 | 권장 위치 | 파일 |
|---|---|---|
| Fig. 1 | III-1 전체 구조 | `results/paper_figures/fig_proposed_architecture.pdf` |
| Fig. 2 | III-5 유효성 계층 | `results/paper_figures/fig_validity_hierarchy_concept.pdf` |
| Fig. 3 | III-6 선택적 보완 | `results/paper_figures/fig_selective_repair_example.pdf` |
| Fig. 4 | IV-4 비교방법 | `results/paper_figures/fig_correction_timing_concept.pdf` |
| Fig. 5 | IV-5 실험설계 | `results/paper_figures/fig_experimental_pipeline.pdf` |
| Fig. 6 | V-1 메인 결과 | `results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf` |
| Fig. 7 | V-2 효율 결과 | `results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf` |
| Fig. 8 | V-4 Strict vs Proposed | `results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf` |
| Table 5 | 메인 비교 | `results/v4_1_external_baselines/summary/paper_table_external_main.csv` |
| Table 6 | Ablation | `results/v4_1_external_baselines/summary/paper_table_ablation.csv` |
| Violation analysis | V-3 | `results/v4_1_external_baselines/summary/by_violation_type.csv` |

## 페이지 편집 우선순위

전자공학회 2단 편집에서 9~10페이지를 목표로 할 때 지면이 부족하면 다음 순서로 줄이는 것을 권장한다.

1. Fig. 4 `fig_correction_timing_concept` 제거
2. Fig. 5 `fig_experimental_pipeline` 크기 축소 또는 본문 설명으로 대체
3. Table 3의 tool 목록 축약
4. VI장 제한점 문단 일부 압축

반대로 9페이지에 미달하면 violation type별 결과를 표로 추가하고, SCCR→OEPVR transition(54/900)을 별도 소절 또는 표로 확장한다.
