# Patent workspace

본 폴더는 `paper/IEIE_FULL_PAPER_DRAFT.md`의 발명 내용을 직무발명 신고 및 특허 출원 초안 형태로 재구성하여 관리한다.

## 발명명칭(안)

**외부 도구 연계형 AI 에이전트의 다중 도구 실행계획 위험도 평가 및 비용 기반 선택적 보완 방법 및 시스템**

영문(안): **Method and System for Risk Evaluation and Cost-Aware Selective Repair of Multi-Tool Execution Plans in Tool-Integrated AI Agents**

## 파일 구성

- `직무발명신고서.md`: 직무발명 신고서 본문 전체
  - 1. 발명(고안)의 상세한 설명
  - 2. 도면의 간단한 설명
  - 3. 권리청구의 범위
  - 4. 도면
- `권리청구범위.md`: 청구항만 별도로 검토하기 위한 파일
- `도면부호.md`: 도면부호 및 구성요소 대응표
- `figures/fig1_prior_art.svg`: 도 1. 종래 다중 도구 실행계획 처리 구조
- `figures/fig2_invention_architecture.svg`: 도 2. 본 발명의 전체 시스템 블록도
- `figures/fig3_condition_risk.svg`: 도 3. 실행조건 결손도 및 위험도 산정 구조
- `figures/fig4_selective_repair.svg`: 도 4. 선택적 보완 후보 생성 및 최적화 구조
- `figures/fig5_embodiment_example.svg`: 도 5. 구체적 실시예
- `figures/fig6_method_flow.svg`: 도 6. 전체 처리 방법 흐름도

## 작성 원칙

1. 논문의 특정 실험 설정에 권리범위가 과도하게 한정되지 않도록, 독립항은 MCP 자체보다 **외부 도구 호출 인터페이스를 사용하는 AI 에이전트**로 상위 개념화하였다.
2. MCP, 7종 실행조건, max-risk, 위험도 임계값, 지연시간/호출 수 기반 비용함수 등은 종속항 및 실시예에서 구체화하였다.
3. 논문의 핵심 차별점인 **실행 전 실행조건 정량평가 → 위험도 기반 보완 여부 판단 → 잔여 위험도와 실행비용을 고려한 보완 후보 선택 → 재검증**의 연결관계를 독립항에 포함하였다.
4. 도면은 특허 명세서에 사용하기 쉽도록 흑백 블록도/흐름도 형태의 SVG로 새로 작성하였다.

> 본 초안은 논문 및 구현 저장소를 기준으로 작성된 발명자 초안이다. 실제 출원 전에는 선행특허 검색 결과와 회사/대리인 양식에 맞춰 청구항의 범위와 용어를 최종 조정하는 것이 바람직하다.
