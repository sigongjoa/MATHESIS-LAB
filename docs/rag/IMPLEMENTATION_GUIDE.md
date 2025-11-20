# RAG 시스템 구현 가이드 및 체크리스트

## 📋 목차
1. [문서 통합 체크리스트](#1-문서-통합-체크리스트)
2. [실패 시나리오 및 복구 전략](#2-실패-시나리오-및-복구-전략)
3. [평가 전략 이원화](#3-평가-전략-이원화)
4. [구현 우선순위](#4-구현-우선순위)
5. [개발 착수 전 최종 점검](#5-개발-착수-전-최종-점검)

---

## 1. 문서 통합 체크리스트

### 1.1 Single Source of Truth 확립

각 문서의 역할과 참조 관계를 명확히 합니다.

| 문서 | 역할 | 참조 문서 | 상태 |
|------|------|----------|------|
| **RAG_SYSTEM_PLANNING.md** | 전체 시스템 개요 및 방향성 | 모든 문서의 기반 | ✅ Master |
| **SDD.md** | 컴포넌트 상세 설계 | ENTERPRISE_OPERATIONS.md 반영 필요 | ⚠️ 업데이트 필요 |
| **API_SPEC.md** | API 엔드포인트 명세 | ✅ 스트리밍 포함됨 | ✅ 완료 |
| **DB_SCHEMA.md** | 데이터베이스 스키마 | ENTERPRISE_OPERATIONS.md 최적화 반영 필요 | ⚠️ 업데이트 필요 |
| **METADATA_SCHEMA.md** | 메타데이터 정의 | ✅ 독립적 | ✅ 완료 |
| **TEST_PLAN.md** | 테스트 전략 | 평가 이원화 반영 필요 | ⚠️ 업데이트 필요 |
| **DOD_USECASE_SEQUENCE.md** | DoD, 유즈케이스, 다이어그램 | 실패 시나리오 추가 필요 | ⚠️ 업데이트 필요 |
| **ENTERPRISE_OPERATIONS.md** | 엔터프라이즈 운영 설계 | 다른 문서로 내용 분산 필요 | ⚠️ 통합 대상 |

### 1.2 즉시 수행할 통합 작업

#### ✅ Task 1: DB_SCHEMA.md 업데이트
**ENTERPRISE_OPERATIONS.md의 최적화된 스키마를 DB_SCHEMA.md에 반영**

```sql
-- DB_SCHEMA.md에 추가할 내용

-- ⭐ 최적화된 rag_chunks 테이블 (ENTERPRISE_OPERATIONS.md에서 이관)
CREATE TABLE rag_chunks (
    -- ... 기존 필드
    
    -- ⭐ 자주 쿼리되는 필드를 JSON에서 컬럼으로 승격
    policy_version VARCHAR(20) NOT NULL,
    scope_type VARCHAR(20) NOT NULL,
    institution_id VARCHAR(100),
    grade_level VARCHAR(20),
    domain VARCHAR(50),
    subject VARCHAR(50),
    curriculum_code VARCHAR(50),
    
    -- ⭐ 최적화된 복합 인덱스
    INDEX idx_filter_national (policy_version, scope_type, grade_level, domain),
    INDEX idx_filter_school (policy_version, scope_type, institution_id),
    INDEX idx_curriculum_code (curriculum_code)
);

-- Full-Text Search 인덱스
ALTER TABLE rag_chunks ADD FULLTEXT INDEX idx_content_fulltext (content);
```

#### ✅ Task 2: SDD.md 아키텍처 다이어그램 업데이트
**비동기 처리 아키텍처를 SDD.md에 통합**

```
SDD.md 2.1절에 추가:

┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
└─────────────┬───────────────────────────────────────────────┘
              │ REST API / WebSocket
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Layer (v1/endpoints/)               │   │
│  └────────┬──────────────────────────┬──────────────────┘   │
│           │                          │                      │
│  ┌────────▼──────────┐      ┌────────▼──────────┐          │
│  │  RAG Service      │      │  Celery Tasks     │◄─────┐   │
│  └────────┬──────────┘      └────────┬──────────┘      │   │
│           │                          │                 │   │
│  ┌────────▼──────────────────────────▼──────────┐     │   │
│  │           Data Access Layer                  │     │   │
│  └──────────────────────────────────────────────┘     │   │
└────────────┬──────────────────┬────────────────────────┼───┘
             │                  │                        │
             ▼                  ▼                        ▼
    ┌─────────────┐    ┌─────────────┐        ┌─────────────┐
    │ PostgreSQL  │    │   Qdrant    │        │   Redis     │
    │  (RDB)      │    │ (Vector DB) │        │  (Queue)    │
    └─────────────┘    └─────────────┘        └─────────────┘
```

#### ✅ Task 3: TEST_PLAN.md 평가 전략 이원화
**CI/CD 평가 전략을 명확히 분리**

```markdown
TEST_PLAN.md 6.2절 수정:

### 6.2 평가 전략 이원화

#### CI (Pull Request 시)
- **목적**: 빠른 피드백, 코드 품질 검증
- **실행 시간**: < 5분
- **비용**: 무료 (LLM 미사용)

**테스트 항목:**
1. 단위 테스트 (pytest, LLM Mock)
2. 메타데이터 검증 테스트
3. 파싱 로직 테스트
4. 룰 기반 답변 검증
   - 인용 태그 포함 여부
   - 금지 키워드 미포함 확인

#### CD (배포 전) / Nightly
- **목적**: 실제 LLM 품질 평가
- **실행 시간**: 30분 ~ 1시간
- **비용**: $5 ~ $10 per run

**테스트 항목:**
1. Golden Set 전체 평가 (Ragas)
2. Faithfulness, Context Recall, Answer Relevancy
3. 비용 추적 및 리포트 생성
```

---

## 2. 실패 시나리오 및 복구 전략

### 2.1 인프라 장애 시나리오

#### Scenario 1: Redis 장애

**상황**: Celery Broker인 Redis가 다운됨

**영향**:
- 문서 인덱싱 불가
- 비동기 작업 큐잉 실패

**복구 전략**:

```python
# backend/app/api/v1/endpoints/rag.py

@router.post("/index", status_code=202)
async def index_document(...):
    """문서 인덱싱 (Fallback 포함)"""
    
    try:
        # 1. Redis 헬스 체크
        redis_client.ping()
        
        # 2. 비동기 작업 큐잉
        task = index_document_task.delay(...)
        return {
            "status": "accepted",
            "job_id": job.job_id,
            "mode": "async"
        }
        
    except redis.ConnectionError:
        # 3. Fallback: 동기 처리 (제한적)
        logger.warning("Redis unavailable, falling back to sync processing")
        
        if file.size > 10 * 1024 * 1024:  # 10MB 이상
            raise HTTPException(
                status_code=503,
                detail="Async processing unavailable. Please try again later."
            )
        
        # 작은 파일만 동기 처리
        result = await index_document_sync(...)
        return {
            "status": "completed",
            "mode": "sync",
            "chunks_created": result.chunks_count
        }
```

**모니터링 알림**:
```python
# Redis 다운 시 즉시 알림
if not redis_client.ping():
    await send_alert("🚨 Redis is down! Indexing degraded to sync mode.")
```

#### Scenario 2: OpenAI API 타임아웃/할당량 초과

**상황**: LLM API 호출 실패

**영향**:
- 질의 응답 실패
- 사용자 경험 저하

**복구 전략**:

```python
# backend/app/services/llm_client.py

class LLMClient:
    """LLM 클라이언트 (Fallback 포함)"""
    
    async def generate_with_fallback(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> str:
        """LLM 생성 (재시도 + Fallback)"""
        
        for attempt in range(max_retries):
            try:
                # 1. 주 모델 (GPT-4)
                return await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=30.0
                )
                
            except openai.RateLimitError:
                # 2. 할당량 초과 → 대기 후 재시도
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                
            except openai.Timeout:
                # 3. 타임아웃 → Fallback 모델
                logger.warning("GPT-4 timeout, falling back to GPT-3.5")
                return await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    timeout=15.0
                )
        
        # 4. 모든 재시도 실패 → 부분 응답
        raise LLMError("LLM generation failed after retries")
```

**사용자 UI 처리**:
```typescript
// MATHESIS-LAB_FRONT/components/AIAssistant.tsx

try {
  const response = await queryRAG(request);
  setAnswer(response.answer);
} catch (error) {
  if (error.status === 429) {
    // 할당량 초과
    setError("현재 요청이 많습니다. 잠시 후 다시 시도해주세요.");
    setRetryAvailable(true);
    setRetryAfter(60); // 60초 후 재시도 가능
  } else if (error.status === 504) {
    // 타임아웃
    setError("응답 생성 시간이 초과되었습니다.");
    setPartialAnswer(error.partial_answer); // 부분 응답 표시
    setRetryAvailable(true);
  }
}
```

#### Scenario 3: 벡터 DB 검색 실패

**상황**: Qdrant 응답 없음

**복구 전략**:

```python
# backend/app/services/hybrid_search_service.py

async def search_with_fallback(
    self,
    query: str,
    filters: dict,
    top_k: int
) -> List[SearchResult]:
    """하이브리드 검색 (Fallback 포함)"""
    
    try:
        # 1. 벡터 검색 시도
        return await self._vector_search(query, filters, top_k)
        
    except VectorSearchError:
        logger.error("Vector search failed, falling back to keyword search")
        
        # 2. Fallback: 키워드 검색만 사용
        return await self._keyword_search(query, filters, top_k)
```

### 2.2 데이터 정합성 시나리오

#### Scenario 4: 문서 수정 후 즉시 질의

**상황**: 사용자가 문서를 수정하고 즉시 질의를 던짐

**문제**: 벡터 DB는 구버전, RDB는 신버전

**해결 전략**:

```python
# backend/app/services/rag_service.py

class RAGService:
    async def query(self, request: RAGQuery, user_id: str):
        """RAG 질의 (정합성 체크 포함)"""
        
        # 1. 검색
        results = await self.search_service.search(...)
        
        # 2. ⭐ 정합성 체크
        validated_results = []
        for result in results:
            # RDB에서 최신 메타데이터 조회
            db_chunk = self.db.query(RAGChunk).filter_by(
                chunk_id=result.chunk_id
            ).first()
            
            if not db_chunk:
                # 삭제된 청크 → 스킵
                logger.warning(f"Chunk {result.chunk_id} deleted, skipping")
                continue
            
            # 메타데이터 불일치 체크
            if db_chunk.content_hash != result.metadata.get("content_hash"):
                # 구버전 임베딩 → 재인덱싱 큐에 추가
                logger.warning(f"Stale embedding for {result.chunk_id}")
                await self.enqueue_reindex(result.chunk_id)
                continue
            
            validated_results.append(result)
        
        # 3. 검증된 결과로 답변 생성
        if len(validated_results) < 3:
            # 충분한 근거 없음
            return RAGResponse(
                answer="최근 문서가 업데이트되어 검색 결과가 부족합니다. 잠시 후 다시 시도해주세요.",
                sources=[],
                confidence=0.0
            )
        
        return await self._generate_answer(query, validated_results)
```

**사용자 알림**:
```typescript
// 프론트엔드에서 표시
if (response.confidence < 0.5) {
  showWarning("최근 문서가 업데이트되어 검색 품질이 낮을 수 있습니다.");
}
```

---

## 3. 평가 전략 이원화

### 3.1 CI 파이프라인 (빠른 피드백)

```yaml
# .github/workflows/ci-fast.yml

name: CI - Fast Tests

on: [pull_request]

jobs:
  fast-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    
    steps:
      - name: Unit Tests (LLM Mocked)
        run: pytest backend/tests/unit -v --no-llm
      
      - name: Metadata Validation
        run: pytest backend/tests/unit/test_metadata_validation.py
      
      - name: Rule-Based Quality Check
        run: |
          python backend/tests/quality/check_citations.py
          python backend/tests/quality/check_forbidden_words.py
```

### 3.2 CD/Nightly 파이프라인 (정량 평가)

```yaml
# .github/workflows/nightly-quality.yml

name: Nightly Quality Evaluation

on:
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시
  workflow_dispatch:  # 수동 실행 가능

jobs:
  ragas-evaluation:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    
    steps:
      - name: Run Ragas Evaluation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python backend/tests/quality/run_ragas_eval.py \
            --golden-set tests/fixtures/golden_set.json \
            --output reports/ragas-scores.json
      
      - name: Check Quality Thresholds
        run: |
          python backend/tests/quality/check_thresholds.py \
            --ragas-file reports/ragas-scores.json \
            --min-faithfulness 0.8
      
      - name: Upload to Dashboard
        run: |
          python tools/upload_metrics.py \
            --file reports/ragas-scores.json \
            --dashboard https://metrics.mathesis-lab.com
```

---

## 4. 구현 우선순위

### Phase 1: Core MVP (2주)
1. ✅ Parser Service (PDF/HWP)
2. ✅ Vector Store 연동 (Qdrant)
3. ✅ RAG Service (기본 질의응답)
4. ✅ API 엔드포인트 (동기 버전)

### Phase 2: Enterprise Features (2주)
1. ⭐ Celery + Redis 비동기 처리
2. ⭐ DB 스키마 최적화 (인덱스)
3. ⭐ 하이브리드 검색
4. ⭐ 비용 추적

### Phase 3: Production Hardening (1주)
1. ⭐ 실패 시나리오 처리
2. ⭐ 스트리밍 API
3. ⭐ WebSocket 진행 상황
4. ⭐ 모니터링 대시보드

### Phase 4: Quality & Optimization (1주)
1. ⭐ Golden Set 구축
2. ⭐ Ragas 평가 자동화
3. ⭐ 성능 최적화
4. ⭐ 부하 테스트

---

## 5. 개발 착수 전 최종 점검

### 5.1 환경 설정 체크리스트

```bash
# ✅ 1. Python 환경
python --version  # 3.11+
pip install -r requirements.txt

# ✅ 2. Redis 설치 및 실행
docker run -d -p 6379:6379 redis:latest
redis-cli ping  # PONG 응답 확인

# ✅ 3. PostgreSQL 설정
psql -U postgres -c "CREATE DATABASE mathesis_lab;"

# ✅ 4. Qdrant 설치
docker run -d -p 6333:6333 qdrant/qdrant

# ✅ 5. 환경 변수 설정
cp .env.example .env
# OPENAI_API_KEY, CELERY_BROKER_URL 등 설정

# ✅ 6. DB 마이그레이션
alembic upgrade head

# ✅ 7. Celery Worker 시작
celery -A backend.app.celery_app worker --loglevel=info
```

### 5.2 코드 스켈레톤 생성 순서

```bash
# 1. 모델 정의
backend/app/models/rag_chunk.py
backend/app/models/rag_document.py

# 2. 서비스 구현
backend/app/services/parser_service.py
backend/app/services/vector_store.py
backend/app/services/rag_service.py

# 3. API 엔드포인트
backend/app/api/v1/endpoints/rag.py

# 4. Celery 태스크
backend/app/tasks/indexing_tasks.py

# 5. 테스트
backend/tests/unit/test_parser_service.py
backend/tests/unit/test_rag_service.py
```

### 5.3 첫 번째 PR 목표

**PR #1: RAG Core MVP**
- [ ] Parser Service 구현
- [ ] Vector Store 연동
- [ ] 기본 RAG 질의 응답
- [ ] 단위 테스트 (커버리지 80%+)
- [ ] API 문서 자동 생성 (Swagger)

**성공 기준**:
```bash
# 테스트 통과
pytest backend/tests/unit -v --cov=backend/app --cov-report=html

# 로컬에서 질의 성공
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "테스트 질문"}'
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀  
**상태**: 🚀 개발 착수 준비 완료
