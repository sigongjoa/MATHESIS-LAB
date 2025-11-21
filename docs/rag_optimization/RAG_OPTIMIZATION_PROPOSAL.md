# [기획서] 교육 도메인 특화 고정밀 RAG 시스템 구축을 위한 성능 최적화 연구

**프로젝트명**: MATHESIS LAB - RAG Pipeline Optimization (Phase 3)  
**작성일**: 2025. 11. 21.  
**작성자**: MATHESIS LAB 연구팀

## 1. 개요 (Executive Summary)

본 프로젝트는 현재 기술적 파이프라인 구축이 완료된 'MATHESIS LAB'의 교육과정 질의응답 시스템을 고도화하는 연구 단계(R&D) 계획이다.

초기 E2E 테스트 결과, 시스템의 엔지니어링적 안정성(파싱-임베딩-저장-검색)은 확보되었으나2, 도메인 특수성(총론 vs 각론, 모호한 키워드 등)으로 인한 검색 품질 저하 문제가 식별되었다33.

이에 본 연구는 **'정량적 평가 데이터셋(Golden Dataset) 구축'**과 **'하이브리드 검색 전략'**을 통해 교육 분야에 특화된 고신뢰성(High-Fidelity) RAG 시스템을 완성하는 것을 목표로 한다.

## 2. 현황 및 문제 정의 (Problem Statement)

### 2.1. 기술적 현황

- **기반 인프라**: Qdrant(Vector DB), Ollama(Embedding), Custom Parser 구축 완료444444444.
- **파이프라인**: 파싱부터 검색까지의 기술적 워크플로우는 성공적으로 동작함5.

### 2.2. 주요 식별 문제 (Key Issues)

초기 E2E 테스트(2025-11-21) 결과, 다음과 같은 한계가 발견됨.

#### 문서 위계 불균형에 따른 검색 실패 (The "Lost in the Middle" Problem)

- **현상**: "교육과정의 성격(총론)" 질의 시, 데이터 양이 압도적으로 많은 "성취기준(각론)" 청크가 상위에 랭크되어 정답 검색에 실패함6.
- **원인**: 단순 Vector Similarity 검색은 문서의 구조적 위계(Hierarchy)나 빈도 불균형을 고려하지 못함.

#### 질의 의도 모호성 및 키워드 매칭 한계

- **현상**: "평가 방법"과 같은 일반적 키워드 질의 시, 사용자가 의도한 '일반 지침'이 아닌 특정 단원의 세부 평가 방법이 반환됨7.
- **원인**: 의미 기반 검색(Dense Retrieval)만으로는 정확한 키워드(Term) 매칭이 필요한 법령/규정/지침 검색에 한계가 있음.

## 3. 연구 목표 (Research Objectives)

1. **정량적 성능 평가 지표 수립**: 주관적 확인이 아닌, 수치화된 성능 지표(Hit Rate, MRR, Accuracy) 확보.
2. **교육 도메인 특화 검색 전략 수립**: 총론/각론의 위계를 고려한 인덱싱 및 하이브리드 검색 구현.
3. **환각(Hallucination) 최소화**: 근거 기반(Citation) 응답 생성을 위한 Context Precision 향상.

## 4. 핵심 연구 과제 (Core Tasks)

### 과제 1: 평가용 골든 데이터셋(Golden Dataset) 구축 (Priority: High)

**목표**: RAG 파이프라인의 성능을 객관적으로 측정하기 위한 기준 데이터셋(Ground Truth) 확보.

**구성 요소**:
- **Query**: 실제 사용자가 던질 법한 다양한 난이도의 질문 (최소 50~100쌍).
- **Context (Positive Chunk)**: 해당 질문에 답하기 위해 반드시 참조해야 할 문서 ID.
- **Ground Truth Answer**: 이상적인 모범 답안.

**데이터셋 카테고리 전략**:
- **Simple Fact**: 단순 사실 조회 (예: "초3 수학 성취기준 코드는?")
- **Reasoning**: 여러 청크 조합 필요 (예: "초등과 중등의 통계 영역 차이점은?")
- **Meta/General**: 총론 및 지침 관련 (예: "평가 유의사항 요약해줘")

### 과제 2: 검색 알고리즘 고도화 (Advanced Retrieval Strategy)

#### 하이브리드 검색 (Hybrid Search) 도입:
- 기존 Vector Search (의미 검색) + BM25 (키워드 매칭) 결합.
- "평가 방법", "교수학습" 등 명확한 용어가 포함된 질의에 대한 정확도(Precision) 개선.

#### 계층적 인덱싱 (Hierarchical Indexing):
- Parent-Child Chunking 전략 적용.
- 검색은 세부 청크(Child)로 수행하되, LLM에게는 상위 문맥(Parent)을 포함하여 전달하여 문맥 단절 문제 해결.

#### 메타데이터 필터링 (Metadata Filtering):
- 파서(Parser) 고도화를 통해 chunk_type (총론/각론), grade (학년), subject (과목) 등을 태깅.
- 검색 전 단계(Pre-filtering)에서 범위를 좁혀 정확도 향상8.

### 과제 3: 임베딩 및 리랭킹 최적화 (Embedding & Reranking)

- **한국어 특화 임베딩 모델 검증**: 현재 nomic-embed-text 외에 upstage-solar 등 한국어 교육 텍스트에 강한 모델 벤치마킹.
- **Cross-Encoder Reranker 도입**: 1차 검색된 상위 문서(Top-K)를 정밀하게 재정렬하여 LLM에 전달되는 Context의 품질 극대화.

## 5. 연구 방법론 및 프로세스 (Methodology)

| 단계 | 활동명 | 주요 내용 | 산출물 |
|------|--------|-----------|--------|
| Step 1 | 데이터셋 구축 | 질문-답변-근거 데이터셋(QA Pair) 50set 생성 | golden_dataset.json |
| Step 2 | Baseline 측정 | 현재 파이프라인(Ollama+Qdrant)의 성능 측정 (RAGAS 활용) | baseline_report.md |
| Step 3 | 알고리즘 개선 | 하이브리드 검색, 메타데이터 필터링 적용 및 튜닝 | 개선된 RAG 모듈 |
| Step 4 | A/B 테스트 | Baseline 대비 개선 모델의 성능 비교 분석 | final_performance_report.pdf |

## 6. 기대 효과 (Expected Outcome)

1. **신뢰성 확보**: "총론" 및 "지침" 관련 질의에 대한 정확도 90% 이상 달성 목표.
2. **확장성**: 수학 외 타 교과목(과학, 사회 등)으로 확장 가능한 표준화된 데이터 처리 파이프라인 정립.
3. **자산화**: 교육 분야에 특화된 RAG 구축 노하우 및 평가 데이터셋 자산화.

## 결론

현재 MATHESIS LAB은 시스템 구축 단계를 넘어 데이터 사이언스 기반의 최적화 단계에 진입했습니다. 본 기획서에 따른 연구 수행은 단순한 기능 구현을 넘어, 실무에서 통용될 수 있는 수준의 고품질 AI 서비스를 만드는 핵심 과정이 될 것입니다.
