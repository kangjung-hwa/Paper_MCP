# 실행계획 유효성과 위험도 기반 선택적 보완을 고려한 MCP AI 에이전트 오케스트레이션 기법

## An MCP-Based AI Agent Orchestration Method with Execution-Plan Validity and Risk-Aware Selective Repair

---

## 요 약

Model Context Protocol(MCP)은 AI 에이전트가 외부 도구를 표준화된 방식으로 탐색하고 호출할 수 있도록 지원한다. 그러나 도구 간 입·출력 스키마가 호환되더라도 전달 데이터의 단위, 기준좌표계, 최신성, 신뢰도 및 출처 조건이 후속 도구의 요구조건과 일치하지 않으면 실행계획의 운용 유효성이 저하될 수 있다. 본 논문은 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터의 실행조건을 명시적으로 정의하고, 조건 위반 정도로부터 실행 위험도를 계산하여 위험도가 임계값을 초과한 경우에만 보완을 수행하는 오케스트레이션 기법을 제안한다. 복수의 보완 후보가 존재할 때는 보완 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 함께 고려하여 보완 방법을 선택한다. 실험 결과 제안방법은 OEPVR 83.2%와 TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고, MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다. 또한 모든 조건 위반을 보완하는 Strict 방식과 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률을 100%에서 47.3%로 감소시켰다. 결과는 MCP 기반 실행계획을 평가할 때 스키마 연결성뿐 아니라 전달 데이터의 실행조건과 보완 비용을 함께 고려해야 함을 보여준다.

**주요어:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Although Model Context Protocol (MCP) enables AI agents to discover and invoke external tools through a standardized interface, schema-level connectivity alone does not guarantee the operational validity of a multi-tool execution plan. Data exchanged between tools may violate downstream requirements on units, reference frames, freshness, confidence, or provenance even when their schemas are structurally compatible. This paper proposes a risk-aware MCP-based AI agent orchestration method that explicitly models execution conditions of inter-tool data, quantifies the degree of condition violations, and selectively inserts repair tools only when the resulting execution risk exceeds a predefined threshold. When multiple repair candidates are available, the proposed method jointly considers residual risk, additional latency, and tool-call cost. Experimental results show that the proposed method achieves an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%. Compared with Direct Tool-Planning, OEPVR and TSR increase by 25.2 and 21.4 percentage points, respectively. Compared with MIRROR-inspired and Tool-MVR-inspired baselines, OEPVR and TSR increase by 16.7 and 21.4 percentage points, respectively. In addition, the proposed method preserves the same OEPVR and TSR as the Strict all-repair strategy while reducing the repair rate from 100% to 47.3%. The results indicate that MCP-based orchestration should consider execution-condition validity and repair cost in addition to schema-level connectivity.

**Keywords:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

# I. 서 론

대규모 언어모델(Large Language Model, LLM)은 자연어 생성과 질의응답을 넘어 외부 함수, API 및 데이터베이스를 호출하여 복합적인 작업을 수행하는 AI 에이전트의 핵심 구성요소로 활용되고 있다. 에이전트의 도구 활용 범위가 확대됨에 따라 단일 함수의 선택과 인자 생성뿐만 아니라 복수 도구의 선택, 호출 순서 및 의존관계를 포함하는 다단계 실행계획의 평가가 요구된다. Berkeley Function Calling Leaderboard(BFCL)[1]는 도구 사용 능력을 평가하는 벤치마크로 함수 선택과 인자 생성을 포함하는 함수 호출 평가를 단일 호출에서 병렬 호출, 순차 호출 및 앞선 호출 결과를 다음 호출에 사용하는 다단계 함수 호출까지 확장하였다. 또한, PlanningArena[2]는 응용 서비스의 API를 이용해 사용자 목표를 달성하는 과정에서 도구 선택, 호출 순서, 논리적 추론 및 사용자 정보 해석을 평가한다. 두 벤치마크는 LLM 기반 도구 활용의 평가 범위가 단일 호출에서 다단계 실행계획으로 확장되고 있음을 보여준다.
복수 도구를 하나의 에이전트에서 활용하기 위한 인터페이스 표준화도 진행되고 있다. Model Context Protocol(MCP)은 AI 시스템과 외부 데이터 및 도구 간 상호작용 방식을 표준화하는 개방형 프로토콜이며, MCP 서버가 제공하는 프롬프트, 리소스 및 도구의 탐색과 호출을 지원한다[3]. MCP 기반 에이전트는 서로 다른 서버에서 제공되는 도구의 입·출력을 연결하여 다단계 실행계획을 구성한다. 그러나 도구 간 입·출력 스키마의 호환성은 실행계획의 운용 유효성을 보장하지 않는다. 동일한 데이터 형식이 연결되더라도 단위, 기준좌표계, 데이터 최신성, 신뢰도 및 출처 조건이 후속 도구의 요구조건과 불일치할 수 있다. 복수 도구가 연속적으로 연결되는 실행계획에서 선행 도구가 생성한 위치 데이터가 후속 경로계획 도구의 입력 스키마와 일치하더라도 두 도구가 서로 다른 좌표계를 사용하면 결과는 구조적으로는 연결되지만 운용상 유효하지 않다. 또한 센서 정보의 형식이 동일하더라도 데이터가 오래되었거나 요구되는 신뢰도보다 낮으면 후속 분석 결과의 신뢰성이 저하된다. 따라서 MCP 기반 다중 도구 실행계획에서는 구조적 연결성과 실행조건 유효성을 구분하여 평가해야 한다.
기존 도구 사용 계획 연구는 도구 선택, 호출 순서, 함수 인자 생성 및 스키마 레벨 호환성을 주요 평가 대상으로 한다[1], [2]. Reflection 기반 연구는 계획 또는 실행 과정에서 발생한 오류를 추론 단계에서 검토하고 수정한다. MIRROR[4]는 실행 전 intra-reflection과 실행 후inter-reflection을 결합하여 도구 사용 추론 과정을 개선하고, Tool-MVR[5]은 meta-verification과 Error–Reflection–Correction 구조를 이용하여 도구 사용 오류의 수정 능력을 학습한다. 그러나 구조적으로 연결된 도구 사이에서 전달되는 데이터의 운용 조건을 정형화하고, 조건 위반의 크기를 수치화하여 실행 전 보완 필요성을 결정하는 방법은 기존 연구의 주요 범위에 포함되지 않는다. 모든 조건 위반을 동일하게 처리하면 운용상 허용 가능한 작은 편차에도 보완 도구가 삽입되어 추가 호출과 지연시간이 증가한다. 실행 유효성을 유지하면서 불필요한 보완을 제한하려면 조건 위반의 정도와 보완 비용을 함께 고려하는 의사결정 기준이 필요하다.
국내에서도 LLM 기반 작업계획, AI 기능의 단계적 연계 및 멀티에이전트 협업에 관한 연구가 수행되고 있다. [6]에서는 강화학습 기반 순차 작업계획에 LLM이 생성한 단계별 행동 마스크를 적용하여 탐색 공간을 제한하고 계획 효율을 향상시키는 방법을 제안하였다. [7]에서는 Retrieval-Augmented Generation(RAG) 프롬프트 기반 생성과 Deep Q-Network(DQN) 기반 검증·수정·최적화를 결합하여 생성-검증-최적화 과정을 자동화한 통합 시스템을 제안하였다. [8]은 복수 에이전트가 멀티모달 지식 정보를 처리·융합하여 전장 상황인식과 의사결정을 지원하는 유·무인 협업 시스템을 구축하였다. 국내 선행연구는 작업계획, 단계적 AI 기능 연계 및 멀티에이전트 협업 구조를 제시하지만, 복수 도구 사이의 전달 데이터에 대해 실행조건을 정량적으로 평가하고 위험도에 따라 보완 여부를 결정하는 문제는 다루지 않는다.

본 논문은 MCP 기반 다중 도구 실행계획의 전달 데이터에 대해 스키마 유형, 의미 유형, 단위, 기준좌표계, 최신성, 신뢰도 및 출처의 7개 실행조건을 정의하고, 각 조건의 위반 정도를 이용하여 실행 위험도를 계산하는 방법을 제안한다. 계산된 위험도가 임계값을 초과한 경우에만 보완을 수행하며, 복수의 보완 후보가 존재하는 경우에는 보완 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 함께 고려하여 보완 후보를 선택한다.
본 연구의 기여는 다음과 같다. 첫째, MCP 기반 실행계획에서 도구 간 전달 데이터의 실행조건을 정의하고 조건 위반 정도를 수치화하였다. 둘째, 도구 간 의존관계별 위험도와 실행계획 전체의 위험도를 계산하여 임계값을 초과한 경우에만 보완하는 선택적 보완 방법을 제안하였다. 셋째, 복수 보완 후보가 존재할 때 잔여 위험도와 실행비용을 함께 고려하는 후보 선택 기준을 정의하였다. 넷째, 실행계획 평가를 스키마 연결성, Strict Condition Conformance Rate(SCCR), Operational Execution Plan Validity Rate(OEPVR) 및 Task Success Rate(TSR)로 구분하고 평가요소 간 차이를 실험적으로 분석하였다.
논문의 구성은 다음과 같다. II장에서는 LLM 기반 도구 사용, reflection 기반 오류 수정, MCP 기반 도구 사용 관련연구를 정리한다. III장에서는 실행조건 모델, 위험도 산정, 선택적 보완 및 비용 기반 후보 선택 방법을 설명한다. IV장에서는 실험환경, 비교방법, 평가 지표 및 실험결과를 제시한다. V장에서 결론을 제시한다.

---

# II. 관련 연구

## 1. LLM 기반 도구 사용 및 도구 계획

LLM 기반 도구 사용은 사용자 질의를 바탕으로 외부 함수 또는 API를 선택하고, 실행에 필요한 인자를 생성하며, 실행 결과를 후속 추론에 반영하는 문제를 다룬다. 초기에는 단일 함수 선택과 인자 정확도가 주요 평가 대상이었으나 최근에는 복수 도구 간 의존관계와 다단계 실행계획까지 평가 범위가 확장되고 있다.

BFCL은 LLM의 함수 호출 성능을 평가하는 벤치마크로 순차 호출, 병렬 호출 및 앞선 함수의 실행 결과를 다음 함수 호출에 사용하는 다단계 함수 호출을 포함한다[1]. BFCL은 단일 함수 호출뿐 아니라 복수 함수가 연속적으로 사용되는 상황을 평가하여 LLM의 도구 사용 능력을 정량화한다. PlanningArena는 여러 응용 서비스의 API를 포함하는 계획 벤치마크로, 사용자 목표를 달성하기 위한 도구 선택, 논리적 추론, 호출 순서 및 사용자 정보 해석을 평가한다[2]. PlanGenLLMs는 LLM 계획 연구를 완전성, 실행 가능성, 최적성, 표현 방식, 일반화 및 효율성의 여섯 평가 기준으로 정리하였다[9].

기존 연구는 실행계획이 목표를 달성하는 데 필요한 도구를 선택했는지, 호출 순서가 적절한지, 함수 인자가 올바른지 등을 평가하는 기반을 제공한다. 그러나 도구 사이에서 전달되는 데이터의 단위, 기준좌표계, 최신성, 신뢰도 및 출처를 별도의 실행조건으로 모델링하고 조건 위반 정도를 정량화하는 문제는 직접적으로 다루지 않는다.

본 연구는 도구 선택 정확도 또는 실행계획 생성 정확도를 대체하는 것을 목표로 하지 않는다. 연구 범위는 계획 생성기가 생성한 실행계획을 입력으로 받아 각 도구 간 의존관계에서 전달 데이터가 후속 도구의 요구조건을 충족하는지 평가하고, 필요한 경우 보완 도구를 삽입하는 오케스트레이션 단계에 한정한다. 따라서 계획 생성기의 성능과 실행계획의 운용 유효성을 분리하여 평가한다.

## 2. 자기검토 기반 오류 수정

LLM 에이전트의 실행 오류를 줄이기 위한 연구에서는 자기검토(reflection)를 이용하여 계획 또는 실행 결과를 재검토한다. MIRROR는 실행 전 자기검토(intra-reflection)와 실행 후 관찰 결과를 반영하는 자기검토(inter-reflection)를 결합하여 도구 사용 과정의 추론을 개선한다[4]. Tool-MVR은 Multi-Agent Meta-Verification과 Exploration-based Reflection Learning을 결합하고 Error–Reflection–Correction 구조를 이용해 도구 사용 오류 수정 능력을 학습한다[5].

자기검토 기반 접근은 에이전트가 생성한 계획이나 실행결과를 다시 검토한다는 점에서 본 연구와 문제 범위가 인접한다. 그러나 자기검토의 판단 근거는 주로 도구 설명, 스키마, 실행 과정 및 실행 피드백으로 구성된다. 반면 본 연구는 단위, 기준좌표계, 최신성, 신뢰도 및 출처와 같이 정형화 가능한 실행조건을 명시적인 메타데이터로 표현하고, 해당 조건을 결정론적 검증기에서 평가한다.

따라서 본 연구의 실행조건 검증은 자기검토를 대체하는 구조가 아니다. 정형화 가능한 실행조건은 규칙 기반으로 평가하고, 의미적 모호성이나 비정형 실행 실패는 LLM 추론 또는 자기검토로 처리하는 구조로 기능을 구분할 수 있다. 본 논문에서는 두 기능의 결합 성능을 평가하지 않고, 실행조건 검증 계층의 효과를 분리하여 분석한다.

## 3. MCP 기반 도구 생태계

MCP는 AI 시스템과 외부 데이터 또는 도구 간 상호작용을 표준화하는 프로토콜이다[3]. Protocol Revision 2025-11-25에서 MCP는 JSON-RPC 2.0 기반의 클라이언트-서버 통신을 사용하며, 초기화 과정에서 프로토콜 버전과 클라이언트 및 서버가 지원하는 기능 정보를 교환한다. 이후 서버가 제공하는 프롬프트, 리소스 및 도구를 탐색하고 사용할 수 있다. 이 가운데 도구는 AI 시스템이 호출할 수 있는 실행 기능을 의미한다.

MCP 환경을 대상으로 한 벤치마크로 MCP-AgentBench가 제안되었다[10]. MCP-AgentBench는 33개의 운용 중인 MCP 서버와 188개의 도구로 구성된 시험환경에서 600개의 질의를 평가하고, MCP를 통한 도구 상호작용의 작업 성공률을 측정한다. MCP 기반 에이전트의 평가 범위를 실제 도구 상호작용으로 확장하였으나, 도구 간 전달 데이터의 실행조건 위반 정도와 위험도 기반 선택적 보완은 평가 대상으로 포함하지 않는다.

MCP는 클라이언트와 서버 간 통신 방식과 도구 인터페이스를 표준화한다. 표준화된 도구 인터페이스를 통해 서로 다른 제공자가 구현한 도구를 하나의 AI 시스템에서 호출할 수 있다. 그러나 도메인별 실행조건은 도구 스키마만으로 모두 표현되지 않을 수 있다. 동일한 필드가 위치 정보를 나타내더라도 도구마다 사용하는 기준좌표계가 다를 수 있으며, 신뢰도 필드의 최솟값도 후속 도구의 요구조건에 따라 달라질 수 있다. 또한 데이터의 허용 경과시간과 출처 요구조건은 시스템 수준의 메타데이터로 관리할 필요가 있다.

본 연구는 MCP 도구 인터페이스에 실행조건 메타데이터를 추가하고, 도구 간 의존관계별로 조건 충족 여부를 평가하는 오케스트레이션 계층을 구성한다. MCP 자체의 프로토콜 동작은 변경하지 않으며, MCP를 통해 연결된 다중 도구 실행계획의 운용 유효성을 평가하고 필요한 보완을 결정하는 상위 계층을 제안한다.

## 4. 기존 연구와 제안방법의 차이

표 1은 관련 연구와 제안방법의 기능 범위를 비교한다.

**표 1. 기존 연구와 제안방법의 기능 비교**  
**Table 1. Functional comparison of related approaches and the proposed method**

| 방법 | 도구 선택/계획 | 실행 전 검토 | 실행 후 수정 | 명시적 실행조건 모델 | 위험도 기반 선택적 보완 | 비용 기반 보완 선택 |
|---|---:|---:|---:|---:|---:|---:|
| Direct Tool-Planning | O | X | X | X | X | X |
| MIRROR | O | O | O | X | X | X |
| Tool-MVR | O | △ | O | X | X | X |
| **Proposed** | O | **O** | - | **O** | **O** | **O** |

MIRROR와 Tool-MVR은 자기검토 또는 오류 수정을 통해 도구 사용 과정을 개선한다[4], [5]. 제안방법은 도구 간 전달 데이터의 실행조건 차이를 직접 계산하고 계산된 위험도와 보완 비용을 보완 여부와 후보 선택에 사용한다. 따라서 제안방법의 차별점은 자기검토의 수행 여부가 아니라 정형화된 실행조건의 수치화, 위험도 기반 선택적 보완, 비용을 고려한 보완 후보 선택에 있다.

---

# III. 제안하는 위험도 기반 MCP 오케스트레이션 기법

## 1. 실행조건 모델 및 위험도 산정

본 논문에서는 MCP 기반 다중 도구 실행계획에서 도구 간 전달 데이터가 후속 도구의 실행조건을 충족하는지 평가하고, 조건 위반 정도에 따라 보완 여부를 결정하는 오케스트레이션 기법을 제안한다. 제안방법은 도구 간 전달 데이터의 실행조건을 정의하고, 각 조건의 위반 정도로부터 의존관계별 위험도와 실행계획 전체 위험도를 계산한다.

초기 실행계획은 사용자 요청과 사용 가능한 도구 정보를 바탕으로 생성되며, 복수의 도구와 도구 간 데이터 의존관계로 구성된다. 선행 도구의 출력 데이터가 후속 도구의 입력으로 전달되는 관계를 의존관계 \((i,j)\)로 정의한다. 제안방법의 전체 구성과 실행 흐름은 그림 1에 나타내었다.

**[그림 1 삽입]**  
`results/paper_figures/fig_proposed_architecture.pdf`

**그림 1. 제안하는 위험도 기반 MCP AI 에이전트 오케스트레이션 구조**  
**Fig. 1. Overall architecture of the proposed risk-aware MCP AI agent orchestration**

그림 1에서 계획 생성기는 사용자 요청과 도구 레지스트리(tool registry)를 이용하여 초기 실행계획 \(W\)를 생성한다. 실행조건 검증기는 각 의존관계에서 선행 도구의 출력 데이터와 후속 도구가 요구하는 조건을 비교한다. 조건 위반 정도는 조건 결손도로 변환되고, 의존관계별 위험도와 전체 실행계획 위험도를 계산하는 데 사용된다. 위험도가 임계값 이하이면 초기 실행계획을 유지하고, 임계값을 초과하면 보완 후보를 생성한다. 복수 후보가 존재하는 경우 각 후보 적용 후의 잔여 위험도와 실행비용을 계산하여 최종 보완 도구를 선택한다.

도구 \(T_i\)의 출력 데이터가 도구 \(T_j\)의 입력으로 전달되는 의존관계 \((i,j)\)에서 후속 도구가 요구하는 실행조건을 식 (1)과 같이 정의한다.

\[
C_{ij}=(\tau_{ij},s_{ij},u_{ij},r_{ij},t_{ij},q_{ij},p_{ij})
\tag{1}
\]

여기서 \(i\)와 \(j\)는 각각 선행 도구와 후속 도구의 인덱스이며, \(C_{ij}\)는 도구 \(T_i\)의 출력이 도구 \(T_j\)의 입력으로 사용될 때 만족해야 하는 실행조건 집합을 의미한다. \(\tau_{ij}\)는 스키마 유형, \(s_{ij}\)는 의미 유형, \(u_{ij}\)는 단위, \(r_{ij}\)는 기준좌표계, \(t_{ij}\)는 최신성, \(q_{ij}\)는 신뢰도, \(p_{ij}\)는 출처에 대한 요구조건을 나타낸다. 식 (1)에 포함된 7개 실행조건의 의미와 정의는 표 2에 정리하였다.

**표 2. 실행조건 구성요소**  
**Table 2. Execution conditions considered in the proposed method**

| 실행조건 | 기호 | 정의 |
|---|---|---|
| 스키마 유형 | \(\tau\) | 데이터 구조 및 형식의 호환 조건 |
| 의미 유형 | \(s\) | 전달 데이터가 표현하는 의미 유형 |
| 단위 | \(u\) | 물리량 또는 데이터 값의 단위 |
| 기준좌표계 | \(r\) | 좌표계 또는 기준계 |
| 최신성 | \(t\) | 허용 가능한 최대 데이터 경과시간 |
| 신뢰도 | \(q\) | 요구되는 최소 신뢰도 |
| 출처 | \(p\) | 요구되는 데이터 출처 또는 검증 속성 |

표 2에서 스키마 유형과 의미 유형은 데이터의 구조적·의미적 연결 조건을 정의한다. 단위와 기준좌표계는 후속 계산에 입력되기 위한 표현 조건을 정의한다. 최신성은 정보가 허용 가능한 시간 범위 안에 있는지를 나타내며, 신뢰도는 후속 도구가 요구하는 최소 신뢰수준을 의미한다. 출처는 데이터의 생성 또는 제공 주체와 검증 속성에 대한 요구조건을 나타낸다.

실제 전달 데이터의 상태와 후속 도구의 요구조건 사이의 차이를 조건 결손도(condition deficit)로 정의한다. 의존관계 \((i,j)\)의 결손도 벡터는 식 (2)와 같다.

\[
D_{ij}=[d_{ij,1},d_{ij,2},\dots,d_{ij,m}]
\tag{2}
\]

여기서 \(D_{ij}\)는 의존관계 \((i,j)\)에서 계산된 실행조건별 결손도를 포함하는 벡터이며, \(d_{ij,k}\)는 \(k\)번째 실행조건의 위반 정도를 나타낸다. \(k\)는 실행조건의 인덱스이고 \(m\)은 고려하는 실행조건의 수이다. 본 연구에서는 7개의 실행조건을 사용하므로 \(m=7\)이다.

스키마 유형, 의미 유형, 단위, 기준좌표계 및 출처와 같은 범주형 조건의 결손도는 식 (3)과 같이 계산한다.

\[
d_{ij,k}=\begin{cases}
0,&c^{act}_{ij,k}=c^{req}_{ij,k}\\
1,&c^{act}_{ij,k}\neq c^{req}_{ij,k}
\end{cases}
\tag{3}
\]

여기서 \(d_{ij,k}\)는 의존관계 \((i,j)\)에서 \(k\)번째 실행조건의 결손도이며, \(c^{act}_{ij,k}\)는 선행 도구 출력의 실제 조건값, \(c^{req}_{ij,k}\)는 후속 도구가 요구하는 조건값을 의미한다. 두 값이 일치하면 결손도를 0, 일치하지 않으면 1로 설정한다.

신뢰도와 같이 최소 요구값이 존재하는 연속형 조건은 위반 크기를 요구값에 대해 정규화하여 식 (4)와 같이 계산한다.

\[
d_{ij,k}=\min\left(1,\max\left(0,\frac{c^{req}_{ij,k}-c^{act}_{ij,k}}{c^{req}_{ij,k}}\right)\right)
\tag{4}
\]

식 (4)에서 \(d_{ij,k}\), \(c^{act}_{ij,k}\), \(c^{req}_{ij,k}\)의 의미는 식 (3)과 동일하다. 실제값이 요구값 이상이면 결손도는 0이며, 요구값보다 낮으면 두 값의 차이를 요구값으로 정규화한다. 결손도의 상한은 1로 제한한다.

최신성 조건의 결손도 \(d^{fresh}_{ij}\)는 데이터 경과시간과 허용 가능한 최대 경과시간의 차이를 이용하여 식 (5)와 같이 계산한다.

\[
d^{fresh}_{ij}=\min\left(1,\max\left(0,\frac{a-a_{\max}}{a_{\max}}\right)\right)
\tag{5}
\]

여기서 \(d^{fresh}_{ij}\)는 의존관계 \((i,j)\)의 최신성 조건에 대한 결손도이며, \(a\)는 선행 도구 출력 데이터의 경과시간, \(a_{\max}\)는 후속 도구가 허용하는 최대 경과시간을 의미한다. 데이터 경과시간이 허용 범위 이내이면 결손도는 0이며, 허용 범위를 초과하면 초과 정도를 \(a_{\max}\)에 대해 정규화하고 상한을 1로 제한한다.

연속형 결손도를 사용하면 기준 초과 정도를 구분할 수 있다. 이진 위반 여부만 사용하면 작은 편차와 큰 편차가 동일한 위반으로 처리되지만, 식 (4)와 식 (5)는 위반 크기를 이후 위험도 계산에 반영한다.

각 의존관계의 실행 위험도 \(R_{ij}\)는 조건 결손도의 가중합으로 식 (6)과 같이 계산한다.

\[
R_{ij}=\sum_{k=1}^{m}w_kd_{ij,k}
\tag{6}
\]

여기서 \(R_{ij}\)는 의존관계 \((i,j)\)의 실행 위험도, \(w_k\)는 \(k\)번째 실행조건에 부여된 가중치, \(d_{ij,k}\)는 해당 실행조건의 결손도, \(m\)은 실행조건의 수를 의미한다. 주요 실험에서는 7개 실행조건에 동일한 가중치를 적용하였다. 동일 가중치는 각 조건의 중요도가 동일하다는 일반적 주장을 의미하지 않는다. 본 실험에서는 도메인별 수동 가중치의 영향을 배제하고 제안방법의 구조적 효과를 비교하기 위한 통제된 설정으로 동일 가중치를 사용하였다.

전체 실행계획의 위험도 \(R(W)\)는 모든 의존관계 위험도 중 최댓값으로 식 (7)과 같이 정의한다.

\[
R(W)=\max_{(i,j)\in E}R_{ij}
\tag{7}
\]

여기서 \(W\)는 전체 실행계획, \(E\)는 실행계획에 포함된 도구 간 의존관계의 집합, \(R(W)\)는 실행계획 전체의 위험도를 의미한다. 최댓값 집계는 하나의 높은 위험도를 갖는 의존관계가 다수의 정상 의존관계에 의해 평균화되는 현상을 방지하기 위해 사용하였다. 주요 실험에서는 `risk_mode=max`, `structural_dependency=false`를 적용하였다. 후속 구조적 의존성을 별도 가중치로 추가하는 방식은 소거 실험에서 평가하였으나 주요 제안방법에는 포함하지 않았다.

## 2. 위험도 기반 선택적 보완 및 비용 기반 후보 선택

제안방법은 모든 조건 위반에 보완을 적용하지 않는다. 실행계획 위험도가 식 (8)의 조건을 만족하는 경우에만 보완을 수행한다.

\[
R(W)>\theta
\tag{8}
\]

여기서 \(R(W)\)는 식 (7)에서 정의한 실행계획 위험도이며, \(\theta\)는 보완 수행 여부를 결정하는 위험도 임계값이다. 주요 실험에서는 \(\theta=0.05\)로 고정하였다. Strict 방식은 하나 이상의 필수 실행조건이 사전 정의 기준을 만족하지 않는 모든 작업에 보완을 수행하지만, Proposed는 정규화된 위험도가 임계값을 초과한 경우에만 보완한다. 두 방식의 보완 여부 결정 차이는 그림 2에 나타내었다.

**[그림 2 삽입]**  
`results/paper_figures/fig_selective_repair_example.pdf`

**그림 2. Strict 방식과 제안하는 선택적 보완의 개념 비교**  
**Fig. 2. Conceptual comparison between strict all-repair and risk-aware selective repair**

그림 2에서 Strict 방식은 하나 이상의 필수 실행조건이 사전 정의 기준을 만족하지 않으면 보완을 수행하는 반면, Proposed는 계산된 실행계획 위험도가 임계값을 초과한 경우에만 보완을 수행한다. 선택적 보완의 목적은 모든 필수 실행조건을 사전 정의 기준에 맞추는 것 자체를 최대화하는 데 있지 않다. 본 연구의 목적은 운용 유효성과 작업 성공률을 유지하면서 운용상 허용 가능한 작은 조건 편차에 대한 불필요한 보완을 제한하는 것이다.

보완 후보는 위반 조건과 후보 도구의 입·출력 조건을 이용해 생성한다. 기준좌표계 조건에는 `CoordinateTransform`과 `PreciseCoordinateTransform`, 단위 조건에는 `UnitConversion`, 최신성 조건에는 `RefreshPosition`, `RefreshThreatInfo`, `FastThreatRefresh` 및 `SensorBasedThreatRefresh`를 사용한다. 신뢰도 조건에는 `ConfidenceEnhancement`, `SensorFusion` 및 대상 데이터에 따라 `TrackObject`를 사용한다. 출처 조건에는 `ValidateSource` 또는 신뢰 가능한 출처 속성을 제공하는 갱신 계열 도구를 사용한다.

동일한 조건에 복수의 후보를 허용한 이유는 보완 결과와 실행비용이 후보마다 다를 수 있기 때문이다. 각 후보에 대해 적용 후의 잔여 위험도와 추가 지연시간 및 도구 호출 수를 계산한다.

보완 후보 \(r\)의 실행비용 \(C(r)\)은 식 (9)와 같이 정의한다.

\[
C(r)=\beta_L\hat L(r)+\beta_N\hat N(r)
\tag{9}
\]

여기서 \(r\)은 하나의 보완 후보, \(C(r)\)은 해당 보완 후보의 실행비용을 의미한다. \(\hat L(r)\)은 보완 후보 \(r\)의 정규화된 추가 지연시간, \(\hat N(r)\)은 정규화된 추가 도구 호출 수이며, \(\beta_L\)과 \(\beta_N\)은 두 비용 항에 부여되는 가중치이다. 주요 실험에서는 \(\beta_L=0.5\), \(\beta_N=0.5\)를 사용하였다. 추가 지연시간은 1000 ms로 나눈 뒤 최댓값을 1로 제한하고, 추가 호출 수는 3으로 나눈 뒤 최댓값을 1로 제한한다.

후보 \(r\)을 실행계획에 적용한 결과를 \(W\oplus r\)로 정의하면 최종 후보 선택은 식 (10)과 같다.

\[
r^{*}=\arg\min_{r\in\mathcal{R}}\left[R(W\oplus r)+\lambda C(r)\right]
\tag{10}
\]

여기서 \(\mathcal{R}\)은 현재 조건 위반에 적용 가능한 보완 후보의 집합, \(W\oplus r\)은 보완 후보 \(r\)을 실행계획 \(W\)에 적용한 실행계획, \(R(W\oplus r)\)은 보완 이후의 잔여 위험도, \(C(r)\)은 식 (9)에서 정의한 보완 비용을 의미한다. \(\lambda\)는 보완 비용의 반영 정도를 조절하는 비용 계수이며, \(r^{*}\)는 잔여 위험도와 보완 비용의 합을 최소화하는 최종 보완 후보를 나타낸다. 주요 실험에서는 \(\lambda=0.25\)로 설정하였다. 위험도를 감소시키지 않는 후보는 선택 대상에서 제외한다. 비용 항은 작업 성공률 자체를 증가시키기 위한 항이 아니라 유사한 위험도 감소 효과를 제공하는 후보 가운데 추가 실행비용이 작은 후보를 선택하기 위해 사용한다.

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

Algorithm 1의 검증과 후보 선택은 실행조건 메타데이터를 사용하여 결정론적으로 수행한다. 계획 생성기의 내부 추론 과정은 위험도 계산에 포함하지 않는다. 따라서 동일한 실행계획과 실행조건 메타데이터가 입력되면 동일한 보완 결과를 산출한다.

---

# IV. 실험 및 결과

## 1. 실험 환경 및 비교방법

평가환경은 Python 기반 결정론적 시뮬레이터로 구성하였다. 주요 실험에서는 24개의 기본 도구와 별도의 보완 대안 도구를 등록하였다. 기본 도구는 정보 획득, 변환, 갱신, 보강, 분석 에이전트, 계획, 검증 및 시각화 기능으로 구성된다. 시험환경에 등록한 주요 도구와 기능 구분은 표 3에 정리하였다.

**표 3. 시험환경의 주요 MCP 도구**  
**Table 3. Major MCP tools used in the testbed**

| 구분 | 도구 |
|---|---|
| 정보 획득 | GetOwnPosition, DetectObject, GetDestination, GetWeather, GetTerrain, GetThreatInfo |
| 변환 | CoordinateTransform, UnitConversion |
| 갱신 | RefreshPosition, RefreshThreatInfo |
| 보강 | SensorFusion, ConfidenceEnhancement, ValidateSource |
| 에이전트 | ThreatAnalysisAgent, SituationAnalysisAgent, CommunicationAnalysisAgent |
| 계획 | RoutePlanning, ThreatAwareRoutePlanning, WeatherAwareRoutePlanning, CommunicationAwareRoutePlanning |
| 검증 | RouteValidation |
| 시각화 | ResultVisualization |

표 3의 도구에는 정보 획득부터 변환, 갱신, 보강, 분석, 계획, 검증 및 시각화까지 실행계획 구성에 필요한 기능을 포함하였다. 도구 실행 지연시간은 시뮬레이터에 정의된 기본 지연시간과 수정·재실행 지연시간을 사용한다. 따라서 본 논문의 지연시간 결과는 실제 LLM 또는 네트워크의 실측 지연시간이 아니라 통제된 시뮬레이터에서 계산한 실행비용이다.

작업은 F1 기본 경로계획, F2 위협 고려 경로계획, F3 기상 고려 경로계획, F4 통신 고려 경로계획, F5 다중 제약 경로계획, F6 상황분석 및 추천의 6개 유형으로 구성하였다. 난수 시드별로 각 유형에서 50개 작업을 생성하여 총 300개 작업을 구성하였다. 각 유형은 정상 20개, 경미 위반 15개, 심각 위반 15개로 구성된다. 주요 실험에서는 난수 시드 42, 123, 2026을 사용하였으며 방법별 총 900개 작업 실행을 평가하였다.

경미 위반과 심각 위반의 구분은 Proposed의 위험도 함수와 독립적으로 생성하였다. 경미 위반은 필수 실행조건이 사전 정의 기준에서 벗어나더라도 숨겨진 환경 상태에서 작업 실패를 직접 유발하지 않는 조건을 포함한다. 심각 위반은 조건 위반과 숨겨진 환경 상태의 결합이 작업 실패에 영향을 주도록 구성하였다. 독립 평가 모듈(Oracle)은 비교방법이 접근하지 않는 숨겨진 환경 상태를 이용하여 필수 실행조건 충족 여부, 운용 유효성 및 작업 성공 여부를 계산한다.

실행조건 위반은 기준좌표계, 단위, 최신성, 신뢰도, 출처 및 복합 위반의 6개 유형으로 구분하였으며, 각 위반 유형의 정의는 표 4에 정리하였다.

**표 4. 실행조건 위반 유형**  
**Table 4. Injected execution-condition violations**

| 위반 유형 | 정의 |
|---|---|
| 기준좌표계 | 전달 데이터의 기준좌표계와 후속 도구의 요구조건이 불일치 |
| 단위 | 전달 데이터의 단위와 후속 도구의 요구조건이 불일치 |
| 최신성 | 전달 데이터의 경과시간이 허용 가능한 최대 경과시간을 초과 |
| 신뢰도 | 전달 데이터의 신뢰도가 요구되는 최솟값보다 낮음 |
| 출처 | 전달 데이터의 출처 또는 검증 속성이 요구조건을 충족하지 않음 |
| 복합 위반 | 2–4개의 실행조건 위반이 동시에 발생 |

표 4의 단일 위반 유형은 하나의 실행조건만 기준을 벗어나도록 구성하였으며, 복합 위반은 2–4개의 실행조건 위반이 동시에 발생하도록 구성하였다.

외부 비교에는 Direct Tool-Planning, MIRROR-inspired, Tool-MVR-inspired 및 Proposed를 사용하였다. Direct Tool-Planning은 작업과 공개 도구 메타데이터를 이용하여 실행계획을 생성하지만 별도의 자기검토, 실행조건 검증 또는 보완을 수행하지 않는다.

MIRROR-inspired는 MIRROR[4]의 실행 전 자기검토 개념을 비교 목적으로 단순화한 결정론적 비교방법이다. 실행 전에 공개 데이터, 스키마, 의미적 의존관계, 목표 경로, 중복 도구 및 도구 순서를 검토하고 공개 스키마에서 확인 가능한 의존관계 오류를 수정한다. MIRROR의 전체 다중 에이전트 학습 구조를 재현하지 않았으므로 본 논문의 수치는 원 MIRROR의 절대 성능을 의미하지 않는다.

Tool-MVR-inspired는 Tool-MVR[5]의 Error–Reflection–Correction 구조를 비교 목적으로 구현한 결정론적 비교방법이다. 초기 실행계획을 먼저 실행한 뒤 관측 가능한 공개 오류가 발생한 작업에서 자기검토, 수정 및 재실행을 수행한다. Tool-MVR의 학습 및 미세조정 절차는 포함하지 않았다.

Strict 방식은 외부 비교방법이 아니라 Proposed의 선택적 보완 효과를 평가하기 위한 내부 소거 실험으로 사용하였다. Strict는 하나 이상의 필수 실행조건이 사전 정의 기준을 만족하지 않는 모든 작업에 보완을 적용한다. 비교방법별 보완 시점의 차이는 그림 3에 나타내었다.

**[그림 3 삽입]**  
`results/paper_figures/fig_correction_timing_concept.pdf`

**그림 3. 비교방법별 보완 시점**  
**Fig. 3. Correction timing of the compared methods**

그림 3은 실행 전 검토를 수행하는 MIRROR-inspired, 실행 후 수정·재실행을 수행하는 Tool-MVR-inspired, 실행조건 검증 후 필요한 보완을 실행 전에 삽입하는 Proposed의 처리 시점을 구분한다.

모든 비교방법은 동일한 작업 집합과 도구 레지스트리를 입력으로 사용한다. 주요 계획 생성기는 결과 재현성을 위해 결정론적 모드로 설정하고 temperature는 0.0으로 고정하였다. Proposed의 주요 매개변수는 \(\theta=0.05\), \(\lambda=0.25\), `risk_mode=max`, `structural_dependency=false`이다.

Oracle은 오케스트레이션 방법이 접근하지 않는 사후 평가 모듈로 분리하였다. Oracle 구현은 `src/orchestration/validator.py`를 호출하거나 가져오지 않으며 독립적인 시뮬레이터 상태와 작업 결과 판정 로직으로 정답 데이터를 계산한다. 이를 통해 Proposed의 검증 규칙과 평가 결과 사이의 직접적인 함수 재사용을 방지하였다. 실험의 전체 평가 절차와 오케스트레이션 방법으로부터 독립된 Oracle의 위치는 그림 4에 나타내었다.

**[그림 4 삽입]**  
`results/paper_figures/fig_experimental_pipeline.pdf`

**그림 4. 실험 평가 파이프라인**  
**Fig. 4. Experimental evaluation pipeline**

그림 4의 평가 절차에 따라 모든 비교방법의 실행결과를 독립 평가 모듈에서 동일한 기준으로 평가하였다. 평가 지표는 네 수준으로 구분하였다. 스키마 연결성(Schema Connectivity)은 선행 도구 출력과 후속 도구 입력의 구조적 연결 여부를 평가한다. Strict Condition Conformance Rate(SCCR)은 모든 필수 실행조건을 사전 정의 기준에 따라 충족한 실행계획의 비율이다. Operational Execution Plan Validity Rate(OEPVR)은 사전에 정의한 운용 허용범위를 충족한 실행계획의 비율이다. Task Success Rate(TSR)은 독립 평가 모듈이 계산한 최종 작업 성공 비율이다.

OEPVR에서 스키마 유형, 의미 유형, 단위, 기준좌표계 및 출처의 허용 기준은 SCCR에 적용한 사전 정의 기준과 동일하게 설정하였다. 신뢰도의 운용 최솟값은 SCCR 기준의 최솟값보다 0.05 낮게 설정하였고, 최신성의 운용 최대 경과시간은 SCCR 기준 최대 경과시간의 1.4배로 설정하였다. 0.05와 1.4는 실험 전에 고정한 시뮬레이터 매개변수이며 외부 표준 또는 실환경 허용치를 의미하지 않는다.

보완 수행률(Repair Rate)은 보완이 수행된 작업의 비율이며, 보완 정밀도·재현율·F1은 Oracle 기준으로 필요한 보완을 얼마나 정확하게 수행했는지 평가한다. OURR은 불필요한 보완 비율을 평가하며 평균 추가 지연시간과 평균 추가 호출 수는 보완으로 증가한 실행비용을 측정한다. 이진 결과 비교에는 McNemar 검정을 사용하고 지연시간과 호출 수 차이에는 bootstrap 신뢰구간을 사용하였다.

## 2. 실행 유효성 비교

표 5는 외부 비교의 주요 결과를 제시한다.

**표 5. 외부 비교방법과 Proposed의 비교**  
**Table 5. Comparison with external baselines**

| 방법 | SCCR | OEPVR | TSR | 평균 호출 수 | 평균 지연시간 (ms) |
|---|---:|---:|---:|---:|---:|
| Direct Tool-Planning | 0.533 | 0.580 | 0.700 | **6.167** | **1380.5** |
| MIRROR-inspired | 0.600 | 0.666 | 0.700 | 6.500 | 1542.0 |
| Tool-MVR-inspired | 0.600 | 0.666 | 0.700 | 7.167 | 1818.8 |
| **Proposed** | **0.772** | **0.832** | **0.914** | 7.366 | 1541.7 |

Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였다. MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

대응 비교에서 Proposed와 Direct의 운용 유효성 차이는 +0.2522였으며 불일치 쌍은 \(b_{01}=253\), \(b_{10}=26\)이었다. Proposed와 각 자기검토 기반 비교방법의 운용 유효성 차이는 +0.1667이었으며 불일치 쌍은 \(b_{01}=228\), \(b_{10}=78\)이었다. TSR 비교에서는 Proposed만 성공한 작업이 193개였고 외부 비교방법만 성공한 작업은 0개였다. 외부 비교방법과 Proposed의 SCCR, OEPVR 및 TSR 차이는 그림 5에 나타내었다.

**[그림 5 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_validity_comparison.pdf`

**그림 5. 외부 비교방법 대비 SCCR, OEPVR 및 TSR**  
**Fig. 5. SCCR, OEPVR, and TSR compared with external baselines**

그림 5에서 Proposed는 외부 비교방법보다 높은 OEPVR과 TSR을 기록하였다. Direct Tool-Planning의 스키마 연결성은 83.3%였으나 SCCR은 53.3%, OEPVR은 58.0%였다. 구조적으로 연결된 실행계획 가운데 일부가 필수 실행조건의 사전 정의 기준 또는 운용 허용범위를 충족하지 않았음을 의미한다. 이 결과는 스키마 수준 호환성과 운용 유효성이 서로 다른 평가 대상임을 보여준다.

위반 유형별 분석에서는 기준좌표계, 단위, 출처 및 복합 위반에서 차이가 크게 나타났다. 기준좌표계 위반에서 Direct Tool-Planning의 OEPVR과 TSR은 각각 29.9%, 43.7%였고 Proposed는 80.5%, 81.6%를 기록하였다. 단위 위반의 OEPVR은 Direct 30.0%, Proposed 87.8%였다. 출처 위반에서는 Direct의 OEPVR과 TSR이 각각 37.8%, 57.8%였고 Proposed는 91.1%, 88.9%였다.

최신성 위반의 OEPVR은 Direct 58.0%, Proposed 79.5%였으며 신뢰도 위반은 Direct 54.8%, Proposed 82.8%였다. 복합 위반의 OEPVR은 Direct 35.9%, Proposed 79.3%였고 TSR은 53.3%에서 89.1%로 증가하였다. 위반 유형별 결과는 Proposed의 주요 결과가 단일 실행조건에 의해 형성되지 않았음을 보여준다.

## 3. 보완 시점 및 실행비용 분석

MIRROR-inspired와 Tool-MVR-inspired는 각각 SCCR 60.0%, OEPVR 66.6%, TSR 70.0%로 동일한 작업 성공 결과를 기록하였다. 두 비교방법 모두 공개 스키마 및 의존관계 오류에 대한 수정을 수행하지만 실행조건 메타데이터를 직접 평가하지 않으므로 동일한 작업 집합에서 유효성 차이가 발생하지 않았다.

보완 시점은 실행비용에 차이를 발생시켰다. MIRROR-inspired는 실행 전 수정을 작업당 평균 0.333회 수행하였고 평균 추가 지연시간은 140.0 ms였다. Tool-MVR-inspired는 초기 실행 이후 Error–Reflection–Correction–Retry 절차를 수행하여 평균 추가 호출 수 1.500, 추가 지연시간 495.1 ms를 기록하였다. Tool-MVR-inspired의 비용에는 초기 실패 실행, 수정 및 재실행이 포함된다.

Tool-MVR-inspired와 MIRROR-inspired의 평균 전체 지연시간 차이는 +276.8 ms였으며 95% bootstrap 신뢰구간은 250.2–306.1 ms였다. 평균 호출 수 차이는 +0.667이며 95% 신뢰구간은 0.611–0.729였다. 작업 성공 결과가 동일한 조건에서 실행 후 복구 방식이 실행 전 수정 방식보다 재실행으로 인한 추가 비용을 발생시켰다.

Proposed의 전체 지연시간은 1541.7 ms로 MIRROR-inspired의 1542.0 ms와 거의 동일하였다. Proposed와 MIRROR-inspired의 지연시간 차이는 -0.27 ms였으며 신뢰구간에 0이 포함되었다. Proposed의 평균 호출 수는 7.366으로 MIRROR-inspired의 6.500보다 높았다. Tool-MVR-inspired와 비교하면 Proposed의 전체 지연시간은 277.1 ms 낮았고 평균 호출 수는 약 0.199 높았다. 외부 비교방법과 Proposed의 평균 지연시간 및 도구 호출 수는 그림 6에 나타내었다.

**[그림 6 삽입]**  
`results/v4_1_external_baselines/figures/fig_external_efficiency_comparison.pdf`

**그림 6. 외부 비교방법과 Proposed의 실행비용 비교**  
**Fig. 6. Execution-cost comparison with external baselines**

그림 6에서 Direct Tool-Planning은 가장 낮은 지연시간과 호출 수를 기록하였고 MIRROR-inspired는 Proposed보다 적은 호출 수를 사용하였다. Proposed는 추가 도구 호출을 사용하는 대신 OEPVR과 TSR을 증가시켰으며, 전체 지연시간은 MIRROR-inspired와 유사하고 Tool-MVR-inspired보다 277.1 ms 낮았다. 따라서 외부 비교 결과는 Proposed가 모든 비용 지표에서 최소값을 갖는다는 주장을 지원하지 않는다.

## 4. 선택적 보완 및 소거 실험

Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. SCCR은 Strict 83.2%, Proposed 77.2%로 Proposed가 6.0%p 낮았다. Proposed는 일부 필수 실행조건이 사전 정의 기준을 만족하지 않는 실행계획을 유지했지만 운용 유효성과 작업 성공률은 감소하지 않았다.

유효성 전이 분석에서 Proposed의 900개 작업 중 54개는 `SCCR=0`이면서 `OEPV=1`이었다. 해당 54개 작업이 Proposed와 Strict의 SCCR 6.0%p 차이를 구성하였다. 운용 유효성과 작업 성공 여부의 대응 비교에서는 Strict와 Proposed 간 차이가 없었다.

보완 행동을 비교하면 Strict의 보완 수행률은 100%였고 Proposed는 47.3%였다. Proposed는 보완 수행률을 52.7%p 감소시켰다. 보완 정밀도는 Strict 21.4%, Proposed 45.3%, 보완 F1은 Strict 35.3%, Proposed 62.4%였다. OURR은 55.8%에서 50.2%로 5.6%p 감소하였다. 평균 추가 지연시간은 53.7 ms에서 43.7 ms로 10.0 ms 감소하였고 평균 추가 호출 수는 0.533에서 0.473으로 감소하였다. Strict와 Proposed의 보완 수행 결과와 실행비용 차이는 그림 7에 나타내었다.

**[그림 7 삽입]**  
`results/v4_1_external_baselines/figures/fig_repair_efficiency.pdf`

**그림 7. Strict 방식 대비 Proposed의 보완 효율성**  
**Fig. 7. Repair efficiency of the proposed method compared with strict all-repair**

그림 7은 Proposed가 Strict와 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률과 추가 지연시간을 감소시킨 결과를 나타낸다. Strict 비교는 Proposed의 선택적 보완이 모든 필수 실행조건을 사전 정의 기준에 맞추는 것 자체를 최대화하지 않음을 보여준다. 선택적 보완의 기여는 모든 기준 편차를 제거하는 데 있지 않고 운용 결과에 영향을 주지 않는 작은 조건 편차에 대한 보완을 제한하는 데 있다.

위반 심각도별 분석에서도 보완 행동의 차이가 확인되었다. 심각 위반에서 Strict와 Proposed의 TSR은 모두 71.5%였다. Proposed의 보완 정밀도는 약 91.0%, 보완 F1은 95.3%, 보완 수행률은 78.5%였다. Strict는 모든 심각 위반 작업에 보완을 적용하므로 보완 수행률은 100%였다.

경미 위반에서 두 방법의 TSR은 모두 100%였다. Proposed의 보완 수행률은 56.3%로 Strict의 100%보다 낮았다. 정상 작업에서도 두 방법의 TSR은 모두 100%였으며 Proposed의 보완 수행률은 17.2%였다. 심각도별 결과에서 Proposed는 심각 위반 작업의 보완을 상대적으로 유지하면서 경미 위반 및 정상 작업에서 보완을 더 많이 생략하였다.

비용 항의 효과는 Strict, Risk-only Selective 및 Risk-Cost Selective를 비교하여 평가하였으며 결과는 표 6에 정리하였다.

**표 6. 위험도-비용 소거 실험 결과**  
**Table 6. Ablation study of risk-cost repair selection**

| 방법 | TSR | 추가 지연시간 (ms) | 추가 호출 수 | 보완 F1 |
|---|---:|---:|---:|---:|
| Strict | 0.914 | 53.7 | 0.533 | 0.353 |
| Risk-only Selective | 0.914 | 53.9 | 0.473 | 0.624 |
| **Risk-Cost Selective** | **0.914** | **43.7** | **0.473** | **0.624** |

표 6에서 Risk-only와 Risk-Cost는 TSR 91.4%, 보완 수행률, 추가 호출 수 및 보완 F1에서 동일한 결과를 기록하였다. 추가 지연시간은 Risk-only 53.9 ms, Risk-Cost 43.7 ms로 10.2 ms 감소하였다. 복수 후보가 존재하는 작업 중 약 14.8%에서 비용 항에 의해 선택 후보가 변경되었다.

비용 관련 소거 실험은 식 (10)의 비용 항이 작업 성공률을 증가시키는 항이 아님을 보여준다. 비용 항은 동일한 보완 결정과 작업 성공률을 유지하면서 더 낮은 지연시간을 갖는 후보를 선택하는 역할을 수행하였다.

## 5. 실험 결과에 대한 논의

본 실험은 결정론적 시뮬레이터에서 수행되었다. 도구 출력, 지연시간, 조건 위반 및 숨겨진 환경에서의 작업 결과는 시뮬레이터에서 생성되므로 보고된 지연시간은 실제 MCP 서버, 네트워크 또는 LLM 추론의 실측 지연시간을 의미하지 않는다. 실제 MCP 적용 환경에서는 서버 응답시간, 네트워크 지연, 모델 추론 지연 및 API 실패가 추가될 수 있다.

주요 실험에서는 결정론적 계획 생성기를 사용하였다. 실제 LLM 계획 생성기에서 발생할 수 있는 확률적 실행계획 변화, 잘못된 인자 생성 및 추론 불안정성은 주요 결과에 포함하지 않았다. 따라서 현재 결과는 동일한 초기 실행계획 생성 조건에서 오케스트레이션 계층의 차이를 분리하여 평가한 결과로 해석해야 한다. 실제 LLM 계획 생성기와의 결합 평가는 외적 타당성 검증을 위한 후속 연구가 필요하다.

MIRROR-inspired와 Tool-MVR-inspired는 각 원 논문의 완전한 재현이 아니다. MIRROR의 다중 에이전트 intra/inter-reflection 학습과 Tool-MVR의 meta-verification 및 reflection learning을 재학습하지 않았다. 두 비교방법은 보완 시점과 공개 도구 피드백 기반 수정 구조를 통제된 시뮬레이터에 맞추어 구현하였다. 따라서 본 논문의 수치로 실제 MIRROR 또는 Tool-MVR의 절대 성능 우열을 판단해서는 안 된다.

OEPVR에 사용한 신뢰도 허용범위 0.05와 최신성 배수 1.4는 시뮬레이터 가정이다. 두 매개변수는 주요 실험 이전에 고정하였으며 산업 또는 군용 시스템의 표준 허용치를 의미하지 않는다. 실제 적용에서는 센서 정확도, 갱신 주기, 서비스 수준 요구사항 및 시스템 안전 요구사항을 기준으로 운용 허용범위를 정의해야 한다.

주요 실험은 7개 실행조건에 동일한 가중치를 적용하였다. 동일 가중치는 실행조건 중요도의 최적성을 주장하기 위한 설정이 아니라 도메인별 수동 가중치를 배제하기 위한 통제된 설정이다. 임계값 \(\theta=0.05\)와 비용 계수 \(\lambda=0.25\)도 주요 실험에서 고정하였다. 실제 시스템에서는 안전 요구사항과 비용 특성에 따라 가중치, 임계값 및 비용 계수를 별도로 설정해야 한다.

평가환경은 경로계획과 상황분석 중심의 6개 작업 유형 및 24개 기본 도구로 구성하였다. 따라서 결과는 해당 시뮬레이터 분포와 도구 레지스트리에 대한 비교 결과이다. 소프트웨어 공학, 기업 업무 자동화 및 웹 자동화 등 다른 MCP 생태계에 대한 일반화는 추가 검증이 필요하다. 도구 수, 의존관계 깊이, 오류 분포 및 메타데이터 품질이 달라질 경우 위험도 분포와 보완 행동도 달라질 수 있다.

본 연구는 자기검토 기반 추론의 대체를 목표로 하지 않는다. 구조화된 메타데이터로 검증 가능한 단위, 기준좌표계, 최신성, 신뢰도 및 출처는 결정론적 검증기가 처리하고, 의미적 모호성과 비정형 실행 실패는 LLM 추론 또는 자기검토가 처리하는 방식으로 기능을 구분할 수 있다. 실제 시스템에서는 실행조건 검증과 자기검토를 결합한 오케스트레이션 구조를 고려할 수 있으나 본 논문에서는 두 기능의 결합 효과를 평가하지 않았다.

종합하면 Proposed는 Direct 및 자기검토 기반 비교방법보다 높은 OEPVR과 TSR을 기록하였다. 또한 Strict와 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률과 추가 지연시간을 감소시켰다. Risk-Cost 후보 선택은 Risk-only 방식과 동일한 작업 성공률을 유지하면서 추가 지연시간을 감소시켰다. 실험 결과는 실행조건 인식 기반 위험도 산정과 선택적 보완의 역할을 각각 운용 유효성 향상과 불필요한 보완 제한으로 구분하여 해석할 수 있음을 보여준다.

---

# V. 결 론

본 논문은 MCP 기반 AI 에이전트가 생성한 다중 도구 실행계획의 실행조건을 정량적으로 평가하고, 실행 위험도와 보완 비용을 기반으로 보완 도구를 선택하는 오케스트레이션 기법을 제안하였다. 제안방법은 스키마 유형, 의미 유형, 단위, 기준좌표계, 최신성, 신뢰도 및 출처의 7개 실행조건을 정의하고 조건 결손도로부터 의존관계별 위험도와 실행계획 위험도를 계산한다. 실행계획 위험도가 임계값을 초과한 경우에만 보완을 수행하며, 복수의 보완 후보에 대해서는 잔여 위험도와 정규화된 지연시간 및 도구 호출 비용을 결합한 목적함수를 사용한다.

24개의 기본 도구와 6개의 작업 유형으로 구성된 결정론적 MCP 시뮬레이터에서 방법별 900개 작업을 평가하였다. Proposed는 OEPVR 83.2%, TSR 91.4%를 기록하였다. Direct Tool-Planning 대비 OEPVR은 25.2%p, TSR은 21.4%p 증가하였고 MIRROR-inspired 및 Tool-MVR-inspired 대비 OEPVR은 16.7%p, TSR은 21.4%p 증가하였다.

내부 소거 실험에서 Strict와 Proposed는 OEPVR 83.2%, TSR 91.4%로 동일하였다. Proposed는 보완 수행률을 100%에서 47.3%로 감소시켰고 추가 지연시간을 53.7 ms에서 43.7 ms로 감소시켰다. Risk-only와 Risk-Cost 비교에서는 동일한 TSR과 보완 F1을 유지하면서 추가 지연시간이 53.9 ms에서 43.7 ms로 감소하였다.

실험 결과는 MCP 기반 다중 도구 실행계획에서 스키마 연결성, 필수 실행조건 충족, 운용 유효성 및 작업 성공을 구분하여 평가해야 함을 보여준다. 또한 실행조건 인식 기반 위험도 산정과 선택적 보완을 결합하면 운용 결과를 유지하면서 불필요한 보완을 제한할 수 있음을 확인하였다.

향후 연구에서는 실제 LLM 계획 생성기와 실제 MCP 서버를 결합한 평가를 수행하고, 도구 명세에서 운용 허용범위를 직접 추출하는 방법을 검토할 필요가 있다. 또한 금전적 비용, 네트워크 부하 및 서버 신뢰성을 포함한 다목적 보완 최적화와 시간에 따라 변하는 전달 데이터의 실행조건을 반영하는 동적 위험도 모델을 추가로 연구할 수 있다.

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
| Table 6 | IV-4 비용 소거 실험 | `results/v4_1_external_baselines/summary/paper_table_ablation.csv` |
| 위반 유형별 분석 | IV-2 | `results/v4_1_external_baselines/summary/by_violation_type.csv` |
