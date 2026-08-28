# Short Summary / Abstract for IEIE Paper

## 요 약

최근 Model Context Protocol(MCP)을 활용한 AI 에이전트의 도구 연계가 확대되고 있으나, 도구 간 스키마가 연결 가능하더라도 데이터의 단위, 좌표계, 최신성, 신뢰도 등의 실행조건이 충족되지 않으면 생성된 실행계획의 유효성을 보장하기 어렵다. 본 논문에서는 이러한 실행조건의 결손 정도를 기반으로 워크플로의 실행 위험도를 산정하고, 위험도가 임계값을 초과하는 경우에만 보완 도구를 선택적으로 삽입하는 MCP 기반 AI 에이전트 오케스트레이션 기법을 제안한다. 또한 복수의 보완 후보에 대해 잔여 위험도와 추가 지연시간 및 도구 호출 비용을 함께 고려하여 최적의 보완 방법을 선택한다. 실험 결과 제안방법은 OEPVR 83.2%와 TSR 91.4%를 달성하여 Direct Tool-Planning 및 reflection 기반 비교방법보다 높은 실행 유효성과 작업 성공률을 보였다. 또한 모든 위반을 보완하는 방식과 동일한 OEPVR 및 TSR을 유지하면서 보완 수행률을 52.7%p 감소시켰다. 이를 통해 MCP 기반 에이전트 오케스트레이션에서 구조적 도구 연결뿐 아니라 실행조건의 유효성과 보완 비용을 함께 고려할 필요가 있음을 확인하였다.

**주요어:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning

---

## Abstract

Although Model Context Protocol (MCP) enables AI agents to integrate heterogeneous external tools, schema-level connectivity alone does not guarantee the operational validity of an execution plan when conditions such as units, reference frames, freshness, and confidence are not satisfied. This paper proposes a risk-aware MCP-based AI agent orchestration method that quantifies execution risk from condition deficits and selectively inserts repair tools only when the risk exceeds a predefined threshold. When multiple repair candidates are available, the proposed method jointly considers residual risk, additional latency, and tool-call cost. Experimental results show that the proposed method achieves an Operational Execution Plan Validity Rate (OEPVR) of 83.2% and a Task Success Rate (TSR) of 91.4%, outperforming Direct Tool-Planning and reflection-based baselines. It also preserves the same OEPVR and TSR as an all-repair strategy while reducing the repair rate by 52.7 percentage points. These results demonstrate the importance of considering execution-condition validity and repair cost in MCP-based AI agent orchestration.

**Keywords:** Model Context Protocol, AI Agent, Tool Orchestration, Execution Validity, Risk-Aware Planning
