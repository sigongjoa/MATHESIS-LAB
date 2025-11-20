# RAG 시스템 문서

이 폴더는 **RAG 기반 교육과정 지능형 질의응답 시스템**의 설계 및 구현 문서를 포함합니다.

## 📚 문서 목록

### 1. 기획 및 설계
- **[RAG_SYSTEM_PLANNING.md](./RAG_SYSTEM_PLANNING.md)**: 전체 시스템 기획서 ✅
  - 프로젝트 개요 및 목표
  - 시스템 아키텍처
  - 데이터 처리 전략
  - 검색 및 생성 로직
  - 환각 방지 및 신뢰성 확보
  - 다중 소스 통합
  - 벤치마크 및 품질 관리
  - 운영 전략

- **[SDD.md](./SDD.md)**: 상세 설계서 (Software Design Description) ✅
  - 컴포넌트 설계
  - 인터페이스 정의
  - 데이터 흐름
  - 예외 처리 전략
  - 레거시 통합
  - 성능 요구사항

### 2. API 및 데이터베이스
- **[API_SPEC.md](./API_SPEC.md)**: API 명세서 ✅
  - OpenAPI 스타일 엔드포인트 정의
  - Request/Response 스키마
  - 에러 코드
  - Rate Limiting
  - 스트리밍 응답

- **[DB_SCHEMA.md](./DB_SCHEMA.md)**: 데이터베이스 스키마 ✅
  - ERD (Entity-Relationship Diagram)
  - 테이블 정의
  - 인덱스 전략
  - 마이그레이션 스크립트
  - 데이터 정합성 규칙

- **[METADATA_SCHEMA.md](./METADATA_SCHEMA.md)**: 메타데이터 스키마 정의 ✅
  - 필수/선택 메타데이터 필드
  - 데이터 타입 및 제약 조건
  - 예시 및 검증 규칙

### 3. 테스트 및 품질
- **[TEST_PLAN.md](./TEST_PLAN.md)**: 테스트 계획서 ✅
  - 단위 테스트 (pytest)
  - 통합 테스트
  - E2E 테스트 (Playwright)
  - 성능 테스트 (Locust)
  - RAG 품질 테스트 (Golden Set, Ragas)

- **[DOD_USECASE_SEQUENCE.md](./DOD_USECASE_SEQUENCE.md)**: DoD, 유즈케이스, 시퀀스 다이어그램 ✅
  - Definition of Done (기능/스프린트/릴리스)
  - 주요 유즈케이스 시나리오
  - 시퀀스 다이어그램
  - 상태 다이어그램

### 4. 구현 가이드 (예정)
- **[DATA_PARSING_GUIDE.md](./DATA_PARSING_GUIDE.md)**: 문서 파싱 가이드 *(예정)*
  - PDF/HWP 파싱 방법
  - 구조적 청킹 전략
  - 메타데이터 자동 추출
  
- **[VECTOR_DB_SETUP.md](./VECTOR_DB_SETUP.md)**: 벡터 DB 설정 가이드 *(예정)*
  - 벡터 DB 선정 기준
  - 인덱스 구성 방법
  - 메타데이터 필터링 설정

- **[BENCHMARK_DATASET.md](./BENCHMARK_DATASET.md)**: 벤치마크 데이터셋 구축 가이드 *(예정)*
  - 골든셋 구성 방법
  - 평가 지표 정의
  - 테스트 케이스 예시

- **[QUALITY_METRICS.md](./QUALITY_METRICS.md)**: RAG 품질 지표 정의 *(예정)*
  - Faithfulness, Context Recall, Context Precision
  - 측정 방법 및 도구
  - 임계값 설정

- **[RAGOPS_GUIDE.md](./RAGOPS_GUIDE.md)**: RAGOps 운영 가이드 *(예정)*
  - 데이터 파이프라인 관리
  - 모니터링 및 알림
  - 버전 관리 및 롤백

## 🎯 시작하기

RAG 시스템 구축을 시작하려면 다음 순서로 문서를 읽으세요:

1. **[RAG_SYSTEM_PLANNING.md](./RAG_SYSTEM_PLANNING.md)** - 전체 시스템 이해
2. **[METADATA_SCHEMA.md](./METADATA_SCHEMA.md)** - 데이터 구조 파악
3. **[DATA_PARSING_GUIDE.md](./DATA_PARSING_GUIDE.md)** - 파싱 구현
4. **[VECTOR_DB_SETUP.md](./VECTOR_DB_SETUP.md)** - 인프라 구축
5. **[BENCHMARK_DATASET.md](./BENCHMARK_DATASET.md)** - 품질 관리 준비

## 🔗 관련 리소스

### 원본 문서
- [assets/](../../assets/) - 교육과정 원본 문서 보관소

### 코드베이스
- `backend/app/services/rag_service.py` - RAG 서비스 구현 *(예정)*
- `backend/app/services/parser_service.py` - 문서 파싱 서비스 *(예정)*
- `backend/app/models/rag_chunk.py` - 청크 데이터 모델 *(예정)*

### 기존 시스템 연동
- [docs/gcp/](../gcp/) - GCP 통합 문서
- `MATHESIS-LAB_FRONT/components/AIAssistant.tsx` - AI 보조 기능
- `MATHESIS-LAB_FRONT/components/NodeGraph.tsx` - 지식 맵 시각화

## 📝 문서 작성 규칙

새로운 문서를 추가할 때는 다음 형식을 따라주세요:

```markdown
# [문서 제목]

## 개요
[문서의 목적과 범위]

## 목차
1. [섹션 1]
2. [섹션 2]
...

## 본문
[상세 내용]

## 예시
[구체적인 예시 코드 또는 데이터]

## 참고 자료
[관련 문서 링크]

---
**문서 버전**: X.X  
**작성일**: YYYY-MM-DD  
**작성자**: [작성자명]
```

## 🤝 기여 가이드

문서 개선 제안이나 오류 발견 시:
1. 이슈 생성
2. 수정 사항 작성
3. Pull Request 제출

---

**최종 업데이트**: 2025-11-20  
**관리자**: MATHESIS LAB 개발팀
