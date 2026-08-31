# 실행계획 유효성과 위험도 기반 선택적 보완을 고려한 MCP AI 에이전트 오케스트레이션 기법

## An MCP-Based AI Agent Orchestration Method with Execution-Plan Validity and Risk-Aware Selective Repair

---

## 요 약

Model Context Protocol(MCP)은 AI 에이전트가 외부 도구를 표준화된 방식으로 탐색하고 호출할 수 있도록 지원한다. 그러나 도구 간 입·출력 schema가 연결되더라도 전달 데이터의 단위, 기준좌표계, 최신성, 신뢰도 및 출처 조건이 후속 도구의 요구조건과 일치하지 않으면 실행계획의 운용 유효성이 저하될 수 있다. 본 논문은 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터의 실행조건을 명시적으로 정의하고, 조건 위반 정도로부터 실행 위험도를 계산하여 위험도가 임계값을 초과한 경우에만 보완을 수행하는 오케스트레이션 기법을 제안한다. 복수의 보완 후보가 존재할 때는 보완 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 함께 고려하여 보완 방법을 선택한다. 실험 결과 제안방법은 OEPVR 83.2%와 TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고, MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다. 또한 모든 조건 위반을 보완하는 Strict 방식과 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률을 100%에서 47.3%로 감소시켰다. 결과는 MCP 기반 실행계획을 평가할 때 schema 연결성뿐 아니라 전달 데이터의 실행조건과 보완 비용을 함께 고려해야 함을 보여준다.

**주요어:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Although Model Context Protocol (MCP) enables AI agents to discover and invoke external tools through a standardized interface, schema-level connectivity alone does not guarantee the operational validity of a multi-tool execution plan. Data exchanged between tools may violate downstream requirements on units, reference frames, freshness, confidence, or provenance even when their schemas are structurally compatible. This paper proposes a risk-aware MCP-based AI agent orchestration method that explicitly models execution conditions of inter-tool data, quantifies the degree of condition violations, and selectively inserts repair tools only when the resulting execution risk exceeds a predefined threshold. When multiple repair candidates are available, the proposed method jointly considers residual risk, additional latency, and tool-call cost. Experimental results show that the proposed method achieves an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%. Compared with Direct Tool-Planning, OEPVR and TSR increase by 25.2 and 21.4 percentage points, respectively. Compared with MIRROR-inspired and Tool-MVR-inspired baselines, OEPVR and TSR increase by 16.7 and 21.4 percentage points, respectively. In addition, the proposed method preserves the same OEPVR and TSR as the Strict all-repair strategy while reducing the repair rate from 100% to 47.3%. The results indicate that MCP-based orchestration should consider execution-condition validity and repair cost in addition to schema-level connectivity.

**Keywords:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

# I. 서 론

대규모 언어모델(Large Language Model, LLM)은 자연어 생성과 질의응답을 넘어 외부 함수, API 및 데이터베이스를 호출하여 복합 작업을 수행하는 AI 에이전트의 핵심 구성요소로 활용되고 있다. 에이전트의 도구 활용 범위가 확대됨에 따라 단일 함수 호출의 정확성뿐 아니라 복수 도구의 선택, 호출 순서 및 의존관계를 포함하는 실행계획 생성 능력이 중요해지고 있다. Berkeley Function Calling Leaderboard(BFCL)는 함수 선택과 인자 생성을 포함하는 함수 호출(function calling) 평가를 병렬·순차 호출과 stateful multi-step 환경으로 확장하였다[1]. PlanningArena는 응용 서비스의 API를 이용해 사용자 목표를 달성하는 과정에서 도구 선택, 호출 순서, 논리적 추론 및 사용자 정보 해석을 평가한다[2]. 두 연구는 LLM 기반 도구 활용의 평가 범위가 단일 호출에서 다단계 실행계획으로 확장되고 있음을 보여준다.

복수 도구를 하나의 AI 응용에서 사용할 수 있도록 인터페이스를 표준화하려는 움직임도 진행되고 있다. Model Context Protocol(MCP)은 AI 응용과 외부 데이터 및 도구 간 상호작용 방식을 정의하는 개방형 프로토콜로, MCP server가 제공하는 tools, resources 및 prompts의 탐색과 호출을 지원한다[3]. MCP 기반 에이전트는 서로 다른 서버의 도구를 조합하여 다단계 실행계획을 구성할 수 있다. 그러나 도구 간 입·출력 schema가 구조적으로 연결된다는 사실만으로 실행계획이 실제 운용조건을 만족한다고 볼 수는 없다. 동일한 데이터 구조가 연결되더라도 값의 단위, 기준좌표계, 최신성, 신뢰도 및 출처가 후속 도구의 요구조건과 불일치할 수 있기 때문이다.

이 문제는 복수 도구가 연속적으로 연결되는 실행계획에서 더욱 명확하게 나타난다. 선행 도구가 생성한 위치 데이터가 후속 경로계획 도구의 입력 schema와 일치하더라도 두 도구가 서로 다른 좌표계를 사용하면 결과는 구조적으로는 연결되지만 운용상 유효하지 않을 수 있다. 또한 센서 정보의 형식이 동일하더라도 데이터가 지나치게 오래되었거나 요구되는 confidence보다 낮으면 후속 분석 결과의 신뢰성이 저하될 수 있다. 따라서 MCP 기반 실행계획을 평가할 때는 도구 간 구조적 연결성뿐 아니라 전달 데이터가 후속 도구의 실행조건을 충족하는지 별도로 평가할 필요가 있다.

기존 도구 계획(tool planning) 연구는 주로 도구 선택, 호출 순서, 인자 생성 및 schema-level compatibility를 주요 평가 대상으로 설정한다[1], [2]. Reflection 기반 연구는 계획 또는 실행 과정에서 발생한 오류를 LLM의 추론을 통해 검토하고 수정한다. MIRROR는 실행 전 intra-reflection과 실행 후 inter-reflection을 결합하여 도구 사용 추론 과정을 개선하고[4], Tool-MVR은 meta-verification과 Error–Reflection–Correction 구조를 이용하여 도구 사용 오류를 수정하는 능력을 학습한다[5]. 그러나 구조적으로 연결된 도구 사이에서 전달되는 데이터의 운용조건을 명시적으로 표현하고, 조건 위반의 크기를 수치화한 뒤 실행 전에 보완 필요성을 결정하는 문제는 기존 연구의 주요 범위에 포함되지 않는다.

모든 조건 위반을 동일한 수준으로 처리하는 것도 적절하지 않을 수 있다. 예를 들어 confidence가 기준보다 매우 조금 낮거나 freshness가 허용 기준을 소폭 초과한 경우에도 무조건 보완 도구를 실행하면 추가 호출과 지연시간이 증가한다. 반대로 좌표계나 단위가 완전히 불일치하는 경우에는 보완 없이 실행하면 이후 단계 전체가 영향을 받을 수 있다. 따라서 실행 유효성을 확보하면서 불필요한 보완을 제한하려면 조건 위반의 정도와 보완 비용을 함께 고려하는 의사결정 기준이 필요하다.

국내에서도 LLM 기반 작업계획, AI 기능의 단계적 연계 및 멀티에이전트 협업에 관한 연구가 수행되고 있다. 조준형과 정소이는 강화학습 기반 순차 작업계획에 LLM이 생성한 단계별 행동 마스크를 적용하여 탐색 공간을 제한하고 계획 효율을 향상시키는 방법을 제안하였다[6]. 우성영 등은 RAG 프롬프트 기반 생성과 DQN 기반 검증·수정·최적화를 결합하여 생성-검증-최적화 과정을 자동화한 통합 시스템을 제안하였다[7]. 이창은 등은 복수 에이전트가 멀티모달 지식 정보를 처리·융합하여 전장 상황인식과 의사결정을 지원하는 유·무인 협업 시스템을 구성하였다[8]. 이러한 국내 선행연구는 작업계획, 단계적 AI 기능 연계 및 멀티에이전트 협업 구조를 제시하지만, 복수 도구 사이의 전달 데이터에 대해 실행조건을 정량적으로 평가하고 위험도에 따라 보완 여부를 선택하는 문제는 다루지 않는다.

본 논문은 MCP 기반 다중 도구 실행계획의 전달 데이터에 대해 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance의 7개 실행조건을 정의하고, 각 조건의 위반 정도를 이용하여 실행 위험도를 계산하는 방법을 제안한다. 계산된 위험도가 임계값을 초과한 경우에만 보완을 수행하며, 복수의 보완 후보가 존재하는 경우에는 보완 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 함께 고려하여 보완 후보를 선택한다.

본 연구의 기여는 다음과 같다. 첫째, MCP 기반 실행계획에서 도구 간 전달 데이터의 실행조건을 명시적으로 정의하고 조건 위반 정도를 수치화하였다. 둘째, 도구 간 의존관계별 위험도와 실행계획 전체의 위험도를 계산하여 임계값을 초과한 경우에만 보완하는 선택적 보완 방법을 제안하였다. 셋째, 복수 보완 후보가 존재할 때 잔여 위험도와 실행비용을 함께 고려하는 후보 선택 기준을 정의하였다. 넷째, 실행계획 평가를 Schema Connectivity, Strict Condition Conformance Rate(SCCR), Operational Execution Plan Validity Rate(OEPVR) 및 Task Success Rate(TSR)로 구분하고 구조적 연결성, 엄격 조건 충족, 운용 유효성 및 최종 작업 성공 간 차이를 실험적으로 분석하였다.

논문의 구성은 다음과 같다. II장에서는 LLM 기반 도구 사용, reflection 기반 오류 수정, MCP 기반 도구 생태계 및 국내 관련연구를 정리한다. III장에서는 실행조건 모델, 위험도 산정, 선택적 보완 및 비용 기반 후보 선택 방법을 설명한다. IV장에서는 실험환경, 비교방법, 평가 지표 및 실험결과를 제시하고 결과의 적용 범위와 한계를 함께 논의한다. V장에서 결론을 제시한다.

---

# II. 관련 연구

## 1. LLM 기반 도구 사용 및 도구 계획

LLM 기반 도구 사용은 사용자 질의를 바탕으로 외부 함수 또는 API를 선택하고, 실행에 필요한 인자를 생성하며, 실행 결과를 후속 추론에 반영하는 문제를 다룬다. 초기에는 단일 함수 선택과 인자 정확도가 주요 평가 대상이었으나 최근에는 복수 도구 간 의존관계와 다단계 실행계획까지 평가 범위가 확장되고 있다.

BFCL은 LLM의 함수 호출 성능을 평가하는 벤치마크로 serial, parallel 및 stateful multi-step function calling을 포함한다[1]. BFCL은 단일 함수 호출뿐 아니라 복수 함수가 연속적으로 사용되는 상황을 평가하여 LLM의 도구 사용 능력을 정량화한다. PlanningArena는 여러 응용 서비스의 API를 포함하는 planning 벤치마크로, 사용자 목표를 달성하기 위한 도구 선택, 논리적 추론, 호출 순서 및 사용자 정보 해석을 평가한다[2]. PlanGenLLMs는 LLM planning 연구를 completeness, executability, optimality, representation, generalization 및 efficiency의 여섯 평가 기준으로 정리하였다[9].

기존 연구는 실행계획이 목표를 달성하는 데 필요한 도구를 선택했는지, 호출 순서가 적절한지, 함수 인자가 올바른지 등을 평가하는 기반을 제공한다. 그러나 도구 사이에서 전달되는 데이터의 단위, 기준좌표계, 최신성, confidence 및 provenance를 별도의 실행조건으로 모델링하고 조건 위반 정도를 정량화하는 문제는 직접적으로 다루지 않는다.

본 연구는 도구 선택 정확도 또는 실행계획 생성 정확도를 대체하는 것을 목표로 하지 않는다. 연구 범위는 계획 생성기(planner)가 생성한 실행계획을 입력으로 받아 각 도구 간 의존관계에서 전달 데이터가 후속 도구의 요구조건을 충족하는지 평가하고, 필요한 경우 보완 도구를 삽입하는 오케스트레이션 단계에 한정한다. 따라서 계획 생성기의 성능과 실행계획의 운용 유효성을 분리하여 평가한다.

## 2. Reflection 기반 오류 수정

LLM agent의 실행 오류를 줄이기 위한 연구에서는 reflection을 이용하여 계획 또는 실행 결과를 재검토한다. MIRROR는 intended action 실행 전의 intra-reflection과 실행 후 observation을 반영하는 inter-reflection을 결합하여 tool learning 과정의 reasoning trajectory를 개선한다[4]. Tool-MVR은 Multi-Agent Meta-Verification과 Exploration-based Reflection Learning을 결합하고 Error–Reflection–Correction 구조를 이용해 tool-use 오류 수정 능력을 학습한다[5].

Reflection 기반 접근은 에이전트가 생성한 계획이나 실행결과를 다시 검토한다는 점에서 본 연구와 문제 범위가 인접한다. 그러나 reflection의 판단 근거는 주로 tool description, schema, trajectory 및 execution feedback으로 구성된다. 반면 본 연구는 unit, reference frame, freshness, confidence 및 provenance와 같이 정형화 가능한 실행조건을 명시적인 메타데이터로 표현하고, 해당 조건을 결정론적 검증기에서 평가한다.

따라서 본 연구의 실행조건 검증은 reflection을 대체하는 구조가 아니다. 정형화 가능한 실행조건은 규칙 기반으로 평가하고, semantic ambiguity나 비정형 실행 실패는 LLM reasoning 또는 reflection으로 처리하는 구조가 기능적으로 구분될 수 있다. 본 논문에서는 두 기능의 결합 성능을 평가하지 않고, 실행조건 검증 계층의 효과를 분리하여 분석한다.

## 3. MCP 기반 도구 생태계

MCP는 AI application과 외부 데이터 또는 도구 간 상호작용을 표준화하는 protocol이다[3]. Protocol Revision 2025-11-25에서 MCP는 JSON-RPC 2.0 기반의 client-server 통신과 capability negotiation을 정의하고, server primitive로 prompts, resources 및 tools를 제공한다. Tool은 AI application이 호출할 수 있는 실행 기능으로 노출된다.

MCP 환경을 대상으로 한 정식 벤치마크 연구로 MCP-AgentBench가 제안되었다[10]. MCP-AgentBench는 33개의 operational MCP server와 188개의 tool로 구성된 시험환경에서 600개의 query를 평가하고 MCP-mediated tool interaction의 task success를 측정한다. MCP 기반 에이전트의 평가 범위를 실제 tool interaction으로 확장했다는 점에서 의미가 있으나, 도구 간 전달 데이터의 실행조건 위반 정도와 위험도 기반 선택적 보완을 평가 대상으로 사용하지 않는다.

MCP가 표준화하는 핵심은 client-server 상호작용과 tool interface이다. 표준화된 interface는 서로 다른 provider가 구현한 tool을 하나의 AI application에서 사용할 수 있는 기반을 제공한다. 그러나 domain-specific execution condition은 tool schema만으로 완전하게 표현되지 않을 수 있다. 동일한 field가 위치를 표현하더라도 좌표 기준이 다를 수 있고, 동일한 confidence field라도 후속 기능이 요구하는 최소값이 다를 수 있다. 또한 데이터의 허용 age와 provenance 요구조건은 application-level 메타데이터로 관리되어야 할 수 있다.

본 연구는 MCP tool interface 위에 별도의 실행조건 메타데이터를 부가하고 도구 간 의존관계 단위로 조건 적합성을 평가하는 오케스트레이션 계층을 구성한다. 따라서 MCP 자체의 protocol 동작을 변경하는 것이 아니라, MCP를 통해 연결된 다중 도구 실행계획의 운용 유효성을 평가하고 필요한 보완을 결정하는 상위 계층을 제안한다.

## 4. 기존 연구와 제안방법의 차이

표 1은 관련 연구와 제안방법의 기능 범위를 비교한다.

**표 1. 기존 연구와 제안방법의 기능 비교**  
**Table 1. Functional comparison of related approaches and the proposed method**

| Method | Tool selection / planning | Pre-execution review | Post-execution correction | Explicit execution-condition model | Risk-based selective repair | Cost-aware repair |
|---|---:|---:|---:|---:|---:|---:|
| Direct Tool-Planning | O | X | X | X | X | X |
| MIRROR | O | O | O | X | X | X |
| Tool-MVR | O | △ | O | X | X | X |
| **Proposed** | O | **O** | - | **O** | **O** | **O** |

MIRROR와 Tool-MVR은 reflection 또는 error correction을 통해 tool-use trajectory를 개선한다[4], [5]. 제안방법은 도구 간 전달 데이터의 실행조건 차이를 직접 계산하고 계산된 위험도와 보완 비용을 보완 여부와 후보 선택에 사용한다. 따라서 제안방법의 차별점은 reflection의 수행 여부가 아니라 정형화된 실행조건의 수치화, 위험도 기반 선택적 보완, 비용을 고려한 보완 후보 선택에 있다.

---

# III. 제안하는 위험도 기반 MCP 오케스트레이션 기법

## 1. 실행조건 모델 및 위험도 산정

제안방법은 계획 생성기가 생성한 초기 실행계획을 입력으로 받아 도구 간 전달 데이터의 실행조건을 검사한다. 실행계획은 도구의 실행 순서와 도구 사이의 데이터 의존관계로 구성된다. 선행 도구의 출력 데이터가 후속 도구의 입력으로 사용되는 연결을 edge \((i,j)\)로 정의한다.

**[그림 1 삽입]**  
`results/paper_figures/fig_proposed_architecture.pdf`

**그림 1. 제안하는 위험도 기반 MCP AI 에이전트 오케스트레이션 구조**  
**Fig. 1. Overall architecture of the proposed risk-aware MCP AI agent orchestration**

그림 1에서 계획 생성기는 사용자 작업과 도구 레지스트리(tool registry)를 이용하여 초기 실행계획 \(W\)를 생성한다. 실행조건 검증기는 각 edge에서 선행 도구의 출력 데이터와 후속 도구가 요구하는 조건을 비교한다. 조건 위반 정도는 deficit으로 변환되고, edge 위험도와 전체 실행계획 위험도를 계산하는 데 사용된다. 위험도가 임계값 이하이면 초기 실행계획을 유지하고, 임계값을 초과하면 보완 후보를 생성한다. 복수 후보가 존재하는 경우 각 후보 적용 후의 잔여 위험도와 실행비용을 계산하여 최종 보완 도구를 선택한다.

도구 \(T_i\)의 출력 데이터가 도구 \(T_j\)의 입력으로 전달되는 edge \((i,j)\)에서 후속 도구가 요구하는 실행조건을 식 (1)과 같이 정의한다.

\[
C_{ij}=(\tau_{ij},s_{ij},u_{ij},r_{ij},t_{ij},q_{ij},p_{ij})
\tag{1}
\]

**표 2. 실행조건 구성요소**  
**Table 2. Execution conditions considered in the proposed method**

| Condition | Symbol | Definition |
|---|---|---|
| Schema type | \(\tau\) | 데이터 구조 및 형식의 호환 조건 |
| Semantic type | \(s\) | 전달 데이터가 표현하는 의미 유형 |
| Unit | \(u\) | 물리량 또는 데이터 값의 단위 |
| Reference frame | \(r\) | 좌표계 또는 기준계 |
| Freshness | \(t\) | 허용 가능한 최대 데이터 age |
| Confidence | \(q\) | 요구되는 최소 신뢰도 |
| Provenance | \(p\) | 요구되는 데이터 출처 또는 검증 속성 |

Schema type과 semantic type은 데이터의 구조적·의미적 연결 조건을 정의한다. Unit과 reference frame은 후속 계산에 입력되기 위한 표현 조건을 정의한다. Freshness는 정보가 허용 가능한 시간 범위 안에 있는지를 나타내며, confidence는 후속 도구가 요구하는 최소 신뢰수준을 의미한다. Provenance는 데이터의 출처 또는 검증 속성에 대한 요구조건을 나타낸다.

실제 전달 데이터의 상태와 후속 도구의 요구조건 사이의 차이를 condition deficit으로 정의한다. Edge \((i,j)\)의 deficit vector는 식 (2)와 같다.

\[
D_{ij}=[d_{ij,1},d_{ij,2},\dots,d_{ij,m}]
\tag{2}
\]

Schema type, semantic type, unit, reference frame 및 provenance와 같은 categorical condition은 요구조건과 실제값이 일치하면 0, 불일치하면 1로 계산한다.

\[
d_{ij,k}=\begin{cases}
0,&c^{act}_{ij,k}=c^{req}_{ij,k}\\
1,&c^{act}_{ij,k}\neq c^{req}_{ij,k}
\end{cases}
\tag{3}
\]

Confidence와 같이 최소 요구값이 존재하는 continuous condition은 위반 크기를 요구값에 대해 정규화한다.

\[
d_{ij,k}=\min\left(1,\max\left(0,\frac{c^{req}_{ij,k}-c^{act}_{ij,k}}{c^{req}_{ij,k}}\right)\right)
\tag{4}
\]

Freshness는 데이터 age \(a\)와 허용 가능한 최대 age \(a_{\max}\)의 차이를 이용해 식 (5)와 같이 계산한다.

\[
d^{fresh}_{ij}=\min\left(1,\max\left(0,\frac{a-a_{\max}}{a_{\max}}\right)\right)
\tag{5}
\]

연속형 deficit을 사용하면 기준을 조금 초과한 경우와 크게 초과한 경우를 구분할 수 있다. Binary violation만 사용하면 두 경우가 동일한 위반으로 처리되지만, 식 (4)와 식 (5)는 위반의 크기를 이후 위험도 계산에 반영한다.

각 edge의 실행 위험도는 condition deficit의 가중합으로 계산한다.

\[
R_{ij}=\sum_{k=1}^{m}w_kd_{ij,k}
\tag{6}
\]

주요 실험에서는 7개 condition에 동일한 weight를 적용하였다. Equal weighting은 각 조건의 중요도가 동일하다는 일반적 주장을 의미하지 않는다. 본 실험에서는 domain-specific manual weighting의 영향을 배제하고 제안방법의 구조적 효과를 비교하기 위한 통제된 설정으로 동일 가중치를 사용하였다.

전체 실행계획의 위험도는 모든 edge 위험도 중 최댓값으로 정의한다.

\[
R(W)=\max_{(i,j)\in E}R_{ij}
\tag{7}
\]

Max aggregation은 하나의 높은 위험도를 갖는 edge가 다수의 정상 edge에 의해 평균화되는 현상을 방지하기 위해 사용하였다. 주요 실험에서는 `risk_mode=max`, `structural_dependency=false`를 적용하였다. 후속 구조적 의존성을 별도 가중치로 추가하는 방식은 소거 실험에서 평가하였으나 주요 제안방법에는 포함하지 않았다.

## 2. 위험도 기반 선택적 보완 및 비용 기반 후보 선택

제안방법은 모든 조건 위반에 보완을 적용하지 않는다. 실행계획 위험도가 식 (8)의 조건을 만족하는 경우에만 보완을 수행한다.

\[
R(W)>\theta
\tag{8}
\]

주요 실험의 임계값은 \(\theta=0.05\)로 고정하였다. Strict 방식은 엄격 조건 위반이 존재하는 모든 작업에 보완을 수행하지만, Proposed는 정규화된 위험도가 임계값을 초과한 경우에만 보완한다.

**[그림 2 삽입]**  
`results/paper_figures/fig_selective_repair_example.pdf`

**그림 2. Strict all-repair와 제안하는 선택적 보완의 개념 비교**  
**Fig. 2. Conceptual comparison between strict all-repair and risk-aware selective repair**

선택적 보완의 목적은 strict conformance를 최대화하는 데 있지 않다. 본 연구의 목적은 운용 유효성과 task success를 유지하면서 운용상 허용 가능한 low-risk deviation에 대한 불필요한 보완을 제한하는 것이다.

보완 후보는 위반 조건과 후보 도구의 입·출력 조건을 이용해 생성한다. Coordinate condition에는 `CoordinateTransform`과 `PreciseCoordinateTransform`, unit condition에는 `UnitConversion`, freshness condition에는 `RefreshPosition`, `RefreshThreatInfo`, `FastThreatRefresh` 및 `SensorBasedThreatRefresh`를 사용한다. Confidence condition에는 `ConfidenceEnhancement`, `SensorFusion` 및 대상 데이터에 따라 `TrackObject`를 사용한다. Provenance condition에는 `ValidateSource` 또는 trusted-source 속성을 제공하는 refresh 계열 도구를 사용한다.

동일한 condition에 복수의 후보를 허용한 이유는 보완 결과와 실행비용이 후보마다 다를 수 있기 때문이다. 각 후보에 대해 적용 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 계산한다.

보완 후보 \(r\)의 실행비용은 식 (9)와 같이 정의한다.

\[
C(r)=\beta_L\hat L(r)+\beta_N\hat N(r)
\tag{9}
\]

\(\hat L(r)\)은 정규화된 추가 지연시간이며, \(\hat N(r)\)은 정규화된 추가 도구 호출 수이다. 주요 실험에서는 \(\beta_L=0.5\), \(\beta_N=0.5\)를 사용하였다. 추가 지연시간은 1000 ms로 나눈 뒤 1로 clipping하고, 추가 호출 수는 3으로 나눈 뒤 1로 clipping한다.

후보 \(r\)을 실행계획에 적용한 결과를 \(W\oplus r\)로 정의하면 최종 후보 선택은 식 (10)과 같다.

\[
r^{*}=\arg\min_{r\in\mathcal{R}}\left[R(W\oplus r)+\lambda C(r)\right]
\tag{10}
\]

주요 실험의 비용 계수는 \(\lambda=0.25\)로 설정하였다. 위험도를 감소시키지 않는 후보는 선택 대상에서 제외한다. 비용 항은 reliability 자체를 증가시키기 위한 항이 아니라 유사한 위험도 감소 효과를 제공하는 후보 가운데 추가 실행비용이 작은 후보를 선택하기 위해 사용한다.

## 3. 실행 절차

제안방법의 전체 실행 절차는 Algorithm 1과 같다.

**Algorithm 1. Risk-Aware MCP Execution-Plan Repair**

```text
Input:
    Initial execution plan W
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
13:     Apply r to obtain candidate execution plan W_r
14:     Compute residual risk R(W_r)
15:     Compute repair cost C(r)
16:     Compute J(r) = R(W_r) + λC(r)
17: end for
18: Select r* = argmin J(r) among risk-reducing candidates
19: Insert r* into W
20: Revalidate the repaired execution plan
21: return repaired execution plan
```

Algorithm 1의 검증과 후보 선택은 실행조건 메타데이터를 사용하여 결정론적으로 수행한다. 계획 생성기의 내부 reasoning은 위험도 계산에 포함하지 않는다. 따라서 동일한 실행계획과 실행조건 메타데이터가 입력되면 동일한 보완 결과를 산출한다.

---

# IV. 실험 및 결과

## 1. 실험 환경 및 비교방법

평가환경은 Python 기반 결정론적 시뮬레이터로 구성하였다. 주요 실험에서는 24개의 기본 도구와 별도의 보완 대안 도구를 등록하였다. 기본 도구는 정보 획득, 변환, 갱신, 보강, 분석 에이전트, 계획, 검증 및 시각화 기능으로 구성된다.

**표 3. 시험환경의 주요 MCP Tool**  
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

도구 실행 지연시간은 시뮬레이터에 정의된 기본 지연시간과 correction/retry 지연시간을 사용한다. 따라서 본 논문의 지연시간 결과는 실제 LLM 또는 network의 wall-clock 지연시간이 아니라 통제된 시뮬레이터에서 계산한 실행비용이다.

작업은 F1 basic route planning, F2 threat-aware route planning, F3 weather-aware route planning, F4 communication-aware route planning, F5 multi-constraint route planning, F6 situation analysis and recommendation의 6개 family로 구성하였다. Seed당 각 family에서 50개 작업을 생성하여 총 300개 작업을 구성하였다. 각 family는 normal 20개, minor 15개, critical 15개로 구성된다. 주요 실험에서는 seed 42, 123, 2026을 사용하였으며 방법별 총 900개 작업 실행을 평가하였다.

Minor와 critical label은 Proposed의 위험도 함수와 독립적으로 생성하였다. Minor case는 엄격 조건 편차가 존재하더라도 hidden-world 작업 결과에 직접적인 실패를 유발하지 않는 조건을 포함한다. Critical case는 조건 위반과 hidden environment state의 결합이 작업 실패에 영향을 주도록 구성하였다. Oracle은 비교방법이 접근하지 않는 hidden-world state를 이용하여 엄격 유효성, 운용 유효성 및 작업 성공 여부를 계산한다.

실행조건 위반은 coordinate, unit, freshness, confidence, provenance 및 compound의 6개 group으로 구분하였다.

**표 4. 실행조건 위반 유형**  
**Table 4. Injected execution-condition violations**

| Violation | Definition |
|---|---|
| Coordinate | 전달 데이터의 reference frame과 후속 도구의 요구조건이 불일치 |
| Unit | 전달 데이터의 unit과 후속 도구의 요구조건이 불일치 |
| Freshness | 전달 데이터의 age가 허용 가능한 maximum age를 초과 |
| Confidence | 전달 데이터의 confidence가 required minimum보다 낮음 |
| Provenance | 전달 데이터의 source 또는 verification property가 요구조건을 충족하지 않음 |
| Compound | 2–4개의 condition violation이 동시에 발생 |

외부 비교에는 Direct Tool-Planning, MIRROR-inspired, Tool-MVR-inspired 및 Proposed를 사용하였다. Direct Tool-Planning은 작업과 공개 도구 메타데이터를 이용하여 실행계획을 생성하지만 별도의 reflection, 실행조건 검증 또는 보완을 수행하지 않는다.

MIRROR-inspired는 MIRROR[4]의 실행 전 reflection 개념을 비교 목적으로 단순화한 결정론적 비교방법이다. 실행 전에 공개 데이터, schema, semantic dependency, goal path, duplicate 및 tool order를 검토하고 public-schema dependency gap에 대한 correction을 수행한다. MIRROR의 full multi-agent learning framework를 재현하지 않았으므로 본 논문의 수치는 원 MIRROR의 절대 성능을 의미하지 않는다.

Tool-MVR-inspired는 Tool-MVR[5]의 Error–Reflection–Correction 구조를 비교 목적으로 구현한 결정론적 비교방법이다. 초기 실행계획을 먼저 실행한 뒤 관측 가능한 공개 오류가 발생한 작업에서 reflection, correction 및 retry를 수행한다. Tool-MVR의 training 및 fine-tuning 절차는 포함하지 않았다.

Strict 방식은 외부 비교방법이 아니라 Proposed의 선택적 보완 효과를 평가하기 위한 내부 소거 실험으로 사용하였다. Strict는 엄격 조건 위반이 탐지된 모든 작업에 보완을 적용한다.

**[그림 3 삽입]**  
`results/paper_figures/fig_correction_timing_concept.pdf`

**그림 3. 비교 방법별 correction timing**  
**Fig. 3. Correction timing of the compared methods**

모든 비교방법은 동일한 작업 집합과 도구 레지스트리를 입력으로 사용한다. 주요 계획 생성기는 결과 재현성을 위해 결정론적 모드로 설정하고 temperature는 0.0으로 고정하였다. Proposed의 주요 parameter는 \(\theta=0.05\), \(\lambda=0.25\), `risk_mode=max`, `structural_dependency=false`이다.

Oracle은 오케스트레이션 방법이 접근하지 않는 사후 평가 모듈로 분리하였다. Oracle implementation은 `src/orchestration/validator.py`를 호출하거나 import하지 않으며 독립적인 시뮬레이터 상태와 작업 결과 logic으로 ground truth를 계산한다. 이를 통해 Proposed의 검증 규칙과 평가 label 사이의 직접적인 함수 재사용을 방지하였다.

**[그림 4 삽입]**  
`results/paper_figures/fig_experimental_pipeline.pdf`

**그림 4. 실험 평가 파이프라인**  
**Fig. 4. Experimental evaluation pipeline**

평가 지표는 네 수준으로 구분하였다. Schema Connectivity는 선행 도구 출력과 후속 도구 입력의 구조적 연결 여부를 평가한다. Strict Condition Conformance Rate(SCCR)은 모든 mandatory execution condition을 strict requirement에 따라 충족한 실행계획의 비율이다. Operational Execution Plan Validity Rate(OEPVR)은 사전에 정의한 operational acceptance envelope를 충족한 실행계획의 비율이다. Task Success Rate(TSR)은 independent Oracle이 계산한 최종 작업 성공 비율이다.

운용 유효성의 hard categorical condition인 schema, semantic type, unit, reference frame 및 provenance는 strict requirement와 동일하게 설정하였다. Confidence는 strict minimum보다 0.05 낮은 값을 operational minimum으로 설정하였고 freshness의 operational maximum age는 strict maximum age의 1.4배로 설정하였다. 0.05와 1.4는 실험 전에 고정한 시뮬레이터 parameter이며 외부 표준 또는 실환경 허용치를 의미하지 않는다.

Repair Rate는 보완이 수행된 작업의 비율이며, repair precision·recall·F1은 Oracle 기준으로 필요한 보완을 얼마나 정확하게 수행했는지 평가한다. OURR은 unnecessary repair와 관련된 비율을 평가하며 Avg. Added Latency와 Avg. Added Calls는 보완으로 증가한 실행비용을 측정한다. Binary outcome 비교에는 McNemar test를 사용하고 지연시간과 호출 수 차이에는 bootstrap confidence interval을 사용하였다.

## 2. 실행 유효성 비교

표 5는 외부 비교의 주요 결과를 제시한다.

**표 5. 외부 비교방법과 Proposed의 비교**  
**Table 5. Comparison with external baselines**

| Method | SCCR | OEPVR | TSR | Avg. Calls | Avg. Latency (ms) |
|---|---:|---:|---:|---:|---:|
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | **6.167** | **1380.5** |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1818.8 |
| **Proposed** | **0.772** | **0.832** | **0.914** | 7.366 | 1541.7 |

Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였다. MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

Paired comparison에서 Proposed와 Direct의 운용 유효성 차이는 +0.2522였으며 discordant pair는 \(b_{01}=253\), \(b_{10}=26\)이었다. Proposed와 각 reflection-inspired 비교방법의 운용 유효성 차이는 +0.1667이었으며 discordant pair는 \(b_{01}=228\), \(b_{10}=78\)이었다. TSR comparison에서는 Proposed만 성공한 작업이 193개였고 외부 비교방법만 성공한 작업은 0개였다.

**[그림 5 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf`

**그림 5. 외부 비교방법 대비 SCCR, OEPVR 및 TSR**  
**Fig. 5. SCCR, OEPVR, and TSR compared with external baselines**

Direct Tool-Planning의 Schema Connectivity Rate는 83.3%였으나 SCCR은 53.3%, OEPVR은 58.0%였다. 구조적으로 연결된 실행계획 가운데 일부가 엄격 또는 운용 실행조건을 충족하지 않았음을 의미한다. 이 결과는 schema-level compatibility와 operational validity가 서로 다른 평가 대상임을 보여준다.

위반 유형별 분석에서는 coordinate, unit, provenance 및 compound group에서 차이가 크게 나타났다. Coordinate group에서 Direct Tool-Planning의 OEPVR과 TSR은 각각 29.9%, 43.7%였고 Proposed는 80.5%, 81.6%를 기록하였다. Unit group의 OEPVR은 Direct 30.0%, Proposed 87.8%였다. Provenance group에서는 Direct의 OEPVR과 TSR이 각각 37.8%, 57.8%였고 Proposed는 91.1%, 88.9%였다.

Freshness group의 OEPVR은 Direct 58.0%, Proposed 79.5%였으며 confidence group은 Direct 54.8%, Proposed 82.8%였다. Compound group의 OEPVR은 Direct 35.9%, Proposed 79.3%였고 TSR은 53.3%에서 89.1%로 증가하였다. 위반 유형별 결과는 Proposed의 주요 결과가 단일 condition에 의해 형성되지 않았음을 보여준다.

## 3. 보완 시점 및 실행비용 분석

MIRROR-inspired와 Tool-MVR-inspired는 각각 SCCR 60.0%, OEPVR 66.6%, TSR 70.0%로 동일한 reliability 결과를 기록하였다. 두 비교방법 모두 공개 schema 및 dependency gap에 대한 correction을 수행하지만 실행조건 메타데이터를 직접 평가하지 않으므로 동일한 작업 집합에서 reliability 차이가 발생하지 않았다.

보완 시점은 실행비용에 차이를 발생시켰다. MIRROR-inspired는 실행 전 correction을 작업당 평균 0.333회 수행하였고 평균 추가 지연시간은 140.0 ms였다. Tool-MVR-inspired는 초기 실행 이후 Error–Reflection–Correction–Retry 절차를 수행하여 평균 추가 호출 수 1.500, 추가 지연시간 495.1 ms를 기록하였다. Tool-MVR-inspired의 비용에는 초기 실패 실행, correction 및 retry가 포함된다.

Tool-MVR-inspired와 MIRROR-inspired의 평균 전체 지연시간 차이는 +276.8 ms였으며 95% bootstrap CI는 250.2–306.1 ms였다. 평균 호출 수 차이는 +0.667이며 95% CI는 0.611–0.729였다. Reliability가 동일한 조건에서 실행 후 복구 방식이 실행 전 correction보다 높은 retry cost를 발생시켰다.

Proposed의 전체 지연시간은 1541.7 ms로 MIRROR-inspired의 1542.0 ms와 거의 동일하였다. Proposed와 MIRROR-inspired의 지연시간 차이는 -0.27 ms였으며 confidence interval에 0이 포함되었다. Proposed의 평균 호출 수는 7.366으로 MIRROR-inspired의 6.500보다 높았다. Tool-MVR-inspired와 비교하면 Proposed의 전체 지연시간은 277.1 ms 낮았고 평균 호출 수는 약 0.199 높았다.

**[그림 6 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf`

**그림 6. 외부 비교방법과 Proposed의 실행비용 비교**  
**Fig. 6. Execution-cost comparison with external baselines**

외부 비교 결과는 Proposed가 모든 비용 지표에서 최소값을 갖는다는 주장을 지원하지 않는다. Direct Tool-Planning은 가장 낮은 지연시간과 호출 수를 기록하였고 MIRROR-inspired는 Proposed보다 적은 호출 수를 사용하였다. Proposed의 외부 비교상 이점은 추가 도구 호출을 사용하는 대신 OEPVR과 TSR을 증가시키고, 전체 지연시간을 MIRROR-inspired와 유사한 수준으로 유지하며 Tool-MVR-inspired보다 낮게 유지한 점에 있다.

## 4. 선택적 보완 및 소거 실험

Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. SCCR은 Strict 83.2%, Proposed 77.2%로 Proposed가 6.0%p 낮았다. Proposed는 strict condition을 완전히 충족하지 않은 일부 실행계획을 유지했지만 operational validity와 task success는 감소하지 않았다.

Validity transition 분석에서 Proposed의 900개 작업 중 54개는 `SCCR=0`이면서 `OEPV=1`이었다. 해당 54개 작업이 Proposed와 Strict의 SCCR 6.0%p 차이를 구성하였다. Operational-validity pair와 task-success pair에서는 Strict와 Proposed 간 차이가 없었다.

보완 행동을 비교하면 Strict의 보완 수행률은 100%였고 Proposed는 47.3%였다. Proposed는 보완 수행률을 52.7%p 감소시켰다. Repair precision은 Strict 21.4%, Proposed 45.3%, repair F1은 Strict 35.3%, Proposed 62.4%였다. OURR은 55.8%에서 50.2%로 5.6%p 감소하였다. 평균 추가 지연시간은 53.7 ms에서 43.7 ms로 10.0 ms 감소하였고 평균 추가 호출 수는 0.533에서 0.473으로 감소하였다.

**[그림 7 삽입]**  
`results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf`

**그림 7. Strict all-repair 대비 Proposed의 보완 효율성**  
**Fig. 7. Repair efficiency of the proposed method compared with strict all-repair**

Strict comparison은 Proposed의 선택적 보완이 strict conformance 자체를 최대화하지 않음을 보여준다. 반면 operational validity와 task success를 유지하면서 보완 빈도와 추가 지연시간을 감소시켰다. 따라서 선택적 보완의 기여는 모든 strict deviation을 제거하는 데 있지 않고 operational outcome에 영향을 주지 않는 low-risk deviation에 대한 보완을 제한하는 데 있다.

Severity별 분석에서도 보완 행동의 차이가 확인되었다. Critical case에서 Strict와 Proposed의 TSR은 모두 71.5%였다. Proposed의 repair precision은 약 91.0%, repair F1은 95.3%, repair rate는 78.5%였다. Strict는 모든 critical case에 repair를 적용하므로 repair rate는 100%였다.

Minor case에서 두 방법의 TSR은 모두 100%였다. Proposed의 repair rate는 56.3%로 Strict의 100%보다 낮았다. Normal case에서도 두 방법의 TSR은 모두 100%였으며 Proposed의 repair rate는 17.2%였다. Severity별 결과는 Proposed가 critical case의 보완을 상대적으로 유지하고 minor 및 normal case에서 보완을 더 많이 생략했음을 보여준다.

비용 항의 효과는 Strict, Risk-only Selective 및 Risk-Cost Selective를 비교하여 평가하였다.

**표 6. Risk-cost 소거 실험 결과**  
**Table 6. Ablation study of risk-cost repair selection**

| Method | TSR | Added Latency (ms) | Added Calls | Repair F1 |
|---|---:|---:|---:|---:|
| Strict | 0.914 | 53.7 | 0.533 | 0.353 |
| Risk-only Selective | 0.914 | 53.9 | 0.473 | 0.624 |
| **Risk-Cost Selective** | **0.914** | **43.7** | **0.473** | **0.624** |

Risk-only와 Risk-Cost는 TSR 91.4%, 보완 수행률, 추가 호출 수 및 repair F1에서 동일한 결과를 기록하였다. 추가 지연시간은 Risk-only 53.9 ms, Risk-Cost 43.7 ms로 10.2 ms 감소하였다. 복수 후보가 존재하는 작업 중 약 14.8%에서 비용 항에 의해 선택 후보가 변경되었다.

비용 관련 소거 실험은 식 (10)의 비용 항이 reliability를 증가시키는 항이 아님을 보여준다. 비용 항은 동일한 보완 결정과 reliability를 유지하면서 더 낮은 지연시간을 갖는 후보를 선택하는 역할을 수행하였다.

## 5. 실험 결과에 대한 논의

본 실험은 결정론적 시뮬레이터에서 수행되었다. 도구 출력, 지연시간, 조건 위반 및 hidden-world 작업 결과는 시뮬레이터에서 생성되므로 보고된 지연시간은 실제 MCP server, network 또는 LLM inference의 wall-clock 지연시간을 의미하지 않는다. 실제 MCP deployment에서는 server response time, network delay, model inference latency 및 API failure가 추가될 수 있다.

주요 실험에서는 결정론적 계획 생성기를 사용하였다. 실제 LLM 계획 생성기에서 발생할 수 있는 stochastic plan variation, hallucinated argument 및 reasoning instability는 주요 결과에 포함하지 않았다. 따라서 현재 결과는 동일한 초기 실행계획 생성 조건에서 오케스트레이션 계층의 차이를 분리하여 평가한 결과로 해석해야 한다. 실제 LLM 계획 생성기와의 결합 평가는 외적 타당성 검증을 위한 후속 연구가 필요하다.

MIRROR-inspired와 Tool-MVR-inspired는 각 원 논문의 완전한 재현이 아니다. MIRROR의 multi-agent intra/inter-reflection learning과 Tool-MVR의 meta-verification 및 reflection learning을 재학습하지 않았다. 두 비교방법은 correction timing과 public tool-feedback 기반 correction 구조를 통제된 시뮬레이터에 맞추어 구현하였다. 따라서 본 논문의 수치로 실제 MIRROR 또는 Tool-MVR의 절대 성능 우열을 판단해서는 안 된다.

OEPVR에 사용한 confidence tolerance 0.05와 freshness multiplier 1.4는 시뮬레이터 가정이다. 두 parameter는 주요 실험 이전에 고정하였으며 산업 또는 군용 시스템의 표준 허용치를 의미하지 않는다. 실제 적용에서는 sensor accuracy, update period, service-level requirement 및 system safety requirement를 기준으로 operational envelope를 정의해야 한다.

주요 실험은 7개 condition에 동일한 weight를 적용하였다. Equal weighting은 condition 중요도의 최적성을 주장하기 위한 설정이 아니라 domain-specific manual weighting을 배제하기 위한 통제된 설정이다. 임계값 \(\theta=0.05\)와 비용 계수 \(\lambda=0.25\)도 주요 실험에서 고정하였다. 실제 시스템에서는 safety requirement와 cost profile에 따라 weight, threshold 및 cost coefficient를 별도로 설정해야 한다.

평가환경은 route planning과 situation analysis 중심의 6개 작업 family 및 24개 기본 도구로 구성하였다. 따라서 결과는 해당 시뮬레이터 분포와 도구 레지스트리에 대한 비교 결과이다. Software engineering, enterprise workflow, web automation 등 다른 MCP ecosystem에 대한 일반화는 추가 검증이 필요하다. 도구 수, dependency depth, error distribution 및 메타데이터 품질이 달라질 경우 위험도 분포와 보완 행동도 달라질 수 있다.

본 연구는 reflection 기반 reasoning의 대체를 목표로 하지 않는다. Structured metadata로 검증 가능한 unit, reference frame, freshness, confidence 및 provenance는 결정론적 검증기가 처리하고, semantic ambiguity와 unstructured execution failure는 LLM reasoning 또는 reflection이 처리하는 방식으로 기능을 구분할 수 있다. 실제 시스템에서는 실행조건 검증과 reflection을 결합한 hybrid orchestration 구조를 고려할 수 있으나 본 논문에서는 두 기능의 결합 효과를 평가하지 않았다.

종합하면 Proposed는 Direct 및 reflection-inspired 비교방법보다 높은 OEPVR과 TSR을 기록하였다. 또한 Strict와 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률과 추가 지연시간을 감소시켰다. Risk-cost 후보 선택은 risk-only selection과 동일한 reliability를 유지하면서 추가 지연시간을 감소시켰다. 실험 결과는 실행조건 인식 기반 위험도 산정과 선택적 보완의 역할을 각각 운용 유효성 향상과 불필요한 보완 제한으로 구분하여 해석할 수 있음을 보여준다.

---

# V. 결 론

본 논문은 MCP 기반 AI 에이전트가 생성한 다중 도구 실행계획의 실행조건을 정량적으로 평가하고, 실행 위험도와 보완 비용을 기반으로 보완 도구를 선택하는 오케스트레이션 기법을 제안하였다. 제안방법은 schema type, semantic type, unit, reference frame, freshness, confidence 및 provenance의 7개 실행조건을 정의하고 condition deficit으로부터 edge 위험도와 실행계획 위험도를 계산한다. 실행계획 위험도가 임계값을 초과한 경우에만 보완을 수행하며, 복수의 보완 후보에 대해서는 잔여 위험도와 정규화된 지연시간 및 도구 호출 비용을 결합한 목적함수를 사용한다.

24개의 기본 도구와 6개의 작업 family로 구성된 결정론적 MCP 시뮬레이터에서 방법별 900개 작업을 평가하였다. Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고 MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

내부 소거 실험에서 Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. Proposed는 보완 수행률을 100%에서 47.3%로 감소시켰고 추가 지연시간을 53.7 ms에서 43.7 ms로 감소시켰다. Risk-only와 Risk-Cost 비교에서는 동일한 TSR과 repair F1을 유지하면서 추가 지연시간이 53.9 ms에서 43.7 ms로 감소하였다.

실험 결과는 MCP 기반 다중 도구 실행계획에서 schema connectivity, strict condition conformance, operational validity 및 task success를 구분하여 평가해야 함을 보여준다. 또한 실행조건 인식 기반 위험도 산정과 선택적 보완을 결합하면 operational outcome을 유지하면서 불필요한 보완을 제한할 수 있음을 확인하였다.

향후 연구에서는 실제 LLM 계획 생성기와 실제 MCP server를 결합한 evaluation을 수행하고, tool specification에서 operational tolerance를 직접 추출하는 방법을 검토할 필요가 있다. 또한 monetary cost, network overhead 및 server reliability를 포함한 multi-objective repair optimization과 시간에 따라 변하는 전달 데이터의 condition을 반영하는 dynamic risk model을 추가로 연구할 수 있다.

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
| Fig. 1 | III-1 실행조건 모델 및 위험도 산정 | `results/paper_figures/fig_proposed_architecture.pdf` |
| Fig. 2 | III-2 선택적 보완 | `results/paper_figures/fig_selective_repair_example.pdf` |
| Fig. 3 | IV-1 비교방법 | `results/paper_figures/fig_correction_timing_concept.pdf` |
| Fig. 4 | IV-1 실험평가 | `results/paper_figures/fig_experimental_pipeline.pdf` |
| Fig. 5 | IV-2 실행 유효성 비교 | `results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf` |
| Fig. 6 | IV-3 실행비용 분석 | `results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf` |
| Fig. 7 | IV-4 선택적 보완 | `results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf` |
| Table 5 | IV-2 메인 비교 | `results/v4_1_external_baselines/summary/paper_table_external_main.csv` |
| Table 6 | IV-4 Cost ablation | `results/v4_1_external_baselines/summary/paper_table_ablation.csv` |
| Violation analysis | IV-2 | `results/v4_1_external_baselines/summary/by_violation_type.csv` |
