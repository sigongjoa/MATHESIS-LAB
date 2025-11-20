# RAG 시스템 엔터프라이즈 운영 설계서

## 📋 목차
1. [비동기 처리 아키텍처](#1-비동기-처리-아키텍처)
2. [DB 스키마 최적화](#2-db-스키마-최적화)
3. [하이브리드 검색 전략](#3-하이브리드-검색-전략)
4. [스트리밍 API 설계](#4-스트리밍-api-설계)
5. [비용 관리 및 모니터링](#5-비용-관리-및-모니터링)
6. [데이터 동기화 전략](#6-데이터-동기화-전략)
7. [자동화된 품질 평가](#7-자동화된-품질-평가)

---

## 1. 비동기 처리 아키텍처

### 1.1 Task Queue 설계 (Celery + Redis)

#### 아키텍처

```
┌─────────────┐
│  Frontend   │
└──────┬──────┘
       │ POST /rag/index
       ▼
┌─────────────┐
│  FastAPI    │
│  (API)      │
└──────┬──────┘
       │ 1. Create Job
       │ 2. Enqueue Task
       ▼
┌─────────────┐      ┌─────────────┐
│   Redis     │◄─────┤   Celery    │
│  (Broker)   │      │   Worker    │
└─────────────┘      └──────┬──────┘
                            │
                            │ 3. Process
                            ▼
                     ┌─────────────┐
                     │  Parser     │
                     │  Embedding  │
                     │  Vector DB  │
                     └─────────────┘
```

#### 구현

```python
# backend/app/celery_app.py

from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "rag_tasks",
    broker=settings.CELERY_BROKER_URL,  # redis://localhost:6379/0
    backend=settings.CELERY_RESULT_BACKEND  # redis://localhost:6379/1
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1시간
    task_soft_time_limit=3300,  # 55분
)
```

```python
# backend/app/tasks/indexing_tasks.py

from celery import Task
from backend.app.celery_app import celery_app
from backend.app.services.parser_service import ParserService
from backend.app.services.vector_store import VectorStore
from backend.app.models.rag_chunk import RAGDocument, RAGIndexingJob
from sqlalchemy.orm import Session

class CallbackTask(Task):
    """진행 상황 업데이트를 위한 베이스 태스크"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """성공 시 콜백"""
        job_id = kwargs.get('job_id')
        # DB 업데이트
        
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """실패 시 콜백"""
        job_id = kwargs.get('job_id')
        # 에러 로깅

@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60
)
def index_document_task(
    self,
    document_id: str,
    file_path: str,
    job_id: str
):
    """
    문서 인덱싱 비동기 태스크
    
    Args:
        document_id: 문서 ID
        file_path: 파일 경로
        job_id: 작업 ID
    """
    from backend.app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # 1. Job 상태 업데이트: PROCESSING
        job = db.query(RAGIndexingJob).filter_by(job_id=job_id).first()
        job.status = "processing"
        job.current_step = "parsing"
        db.commit()
        
        # 2. 문서 파싱
        parser = ParserService()
        chunks = await parser.parse_document(Path(file_path), "curriculum")
        
        job.chunks_total = len(chunks)
        job.current_step = "embedding"
        db.commit()
        
        # 3. 임베딩 생성 (배치 처리)
        embeddings = []
        batch_size = 100
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            batch_embeddings = await embedding_service.embed_batch(
                [c.content for c in batch]
            )
            embeddings.extend(batch_embeddings)
            
            # 진행률 업데이트
            job.chunks_processed = i + len(batch)
            job.progress = int((job.chunks_processed / job.chunks_total) * 100)
            db.commit()
            
            # Celery 진행 상황 업데이트
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': job.chunks_processed,
                    'total': job.chunks_total,
                    'step': 'embedding'
                }
            )
        
        job.current_step = "indexing"
        db.commit()
        
        # 4. 벡터 DB 저장
        vector_store = VectorStore()
        for chunk, embedding in zip(chunks, embeddings):
            await vector_store.upsert(
                chunk.chunk_id,
                embedding,
                chunk.metadata,
                chunk.content
            )
            
            # DB에 청크 메타데이터 저장
            db_chunk = RAGChunk(
                chunk_id=chunk.chunk_id,
                document_id=document_id,
                content=chunk.content,
                metadata=chunk.metadata,
                # 최적화: 자주 쿼리되는 필드 승격
                policy_version=chunk.metadata.get("policy_version"),
                scope_type=chunk.metadata.get("scope_type"),
                institution_id=chunk.metadata.get("institution_id"),
                grade_level=chunk.metadata.get("grade_level"),
                domain=chunk.metadata.get("domain")
            )
            db.add(db_chunk)
        
        db.commit()
        
        # 5. Job 완료
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now()
        db.commit()
        
        return {
            "status": "completed",
            "chunks_created": len(chunks)
        }
        
    except Exception as e:
        # 에러 처리
        job.status = "failed"
        job.error_message = str(e)
        job.error_stack = traceback.format_exc()
        db.commit()
        
        # 재시도
        raise self.retry(exc=e)
        
    finally:
        db.close()
```

#### API 엔드포인트 수정

```python
# backend/app/api/v1/endpoints/rag.py

from backend.app.tasks.indexing_tasks import index_document_task

@router.post("/index", status_code=202)
async def index_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    metadata: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    문서 인덱싱 (비동기)
    
    Returns:
        202 Accepted - Job ID 반환
    """
    # 1. 파일 저장
    file_path = await save_uploaded_file(file)
    
    # 2. Document 레코드 생성
    document = RAGDocument(
        file_path=str(file_path),
        file_name=file.filename,
        document_type=document_type,
        status="pending",
        **json.loads(metadata)
    )
    db.add(document)
    db.commit()
    
    # 3. Job 생성
    job = RAGIndexingJob(
        document_id=document.document_id,
        status="pending"
    )
    db.add(job)
    db.commit()
    
    # 4. Celery 태스크 실행
    task = index_document_task.delay(
        document_id=document.document_id,
        file_path=str(file_path),
        job_id=job.job_id
    )
    
    return {
        "status": "accepted",
        "job_id": job.job_id,
        "task_id": task.id,
        "estimated_time_seconds": 120
    }
```

### 1.2 WebSocket 실시간 진행 상황 알림

```python
# backend/app/api/v1/endpoints/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[job_id] = websocket
    
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
    
    async def send_progress(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            await self.active_connections[job_id].send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/indexing/{job_id}")
async def websocket_indexing_progress(
    websocket: WebSocket,
    job_id: str,
    db: Session = Depends(get_db)
):
    """인덱싱 진행 상황 WebSocket"""
    await manager.connect(job_id, websocket)
    
    try:
        while True:
            # DB에서 최신 상태 조회
            job = db.query(RAGIndexingJob).filter_by(job_id=job_id).first()
            
            await manager.send_progress(job_id, {
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "chunks_processed": job.chunks_processed,
                "chunks_total": job.chunks_total
            })
            
            if job.status in ["completed", "failed"]:
                break
            
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        manager.disconnect(job_id)
```

---

## 2. DB 스키마 최적화

### 2.1 개선된 rag_chunks 테이블

```sql
CREATE TABLE rag_chunks (
    chunk_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    document_id VARCHAR(36) NOT NULL,
    
    -- 청크 내용
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    chunk_index INTEGER NOT NULL,
    
    -- ⭐ 메타데이터 (JSON) - 덜 중요한 필드만
    metadata JSON NOT NULL,
    
    -- ⭐ 자주 쿼리되는 필드를 컬럼으로 승격 (JSON에서 꺼냄)
    policy_version VARCHAR(20) NOT NULL,
    scope_type VARCHAR(20) NOT NULL,
    institution_id VARCHAR(100),
    grade_level VARCHAR(20),
    domain VARCHAR(50),
    subject VARCHAR(50),
    curriculum_code VARCHAR(50),
    
    -- 임베딩 정보
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    embedding_dimension INTEGER NOT NULL DEFAULT 3072,
    vector_id VARCHAR(100),
    
    -- 레거시 시스템 연동
    curriculum_id VARCHAR(36),
    node_id VARCHAR(36),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 외래 키
    FOREIGN KEY (document_id) REFERENCES rag_documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (curriculum_id) REFERENCES curriculums(curriculum_id) ON DELETE SET NULL,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE SET NULL,
    
    -- ⭐ 최적화된 인덱스
    INDEX idx_document_id (document_id),
    INDEX idx_curriculum_id (curriculum_id),
    INDEX idx_node_id (node_id),
    INDEX idx_content_hash (content_hash),
    
    -- ⭐ 복합 인덱스 (자주 사용되는 필터 조합)
    INDEX idx_filter_national (policy_version, scope_type, grade_level, domain),
    INDEX idx_filter_school (policy_version, scope_type, institution_id),
    INDEX idx_curriculum_code (curriculum_code),
    
    -- 복합 인덱스
    UNIQUE INDEX idx_document_chunk (document_id, chunk_index)
);
```

### 2.2 Full-Text Search 인덱스

```sql
-- MySQL Full-Text Search
ALTER TABLE rag_chunks ADD FULLTEXT INDEX idx_content_fulltext (content);

-- 사용 예시
SELECT * FROM rag_chunks
WHERE MATCH(content) AGAINST('최대공약수 소인수분해' IN NATURAL LANGUAGE MODE)
AND policy_version = '2022개정'
LIMIT 10;
```

---

## 3. 하이브리드 검색 전략

### 3.1 검색 파이프라인

```python
# backend/app/services/hybrid_search_service.py

from typing import List
from dataclasses import dataclass

@dataclass
class SearchResult:
    chunk_id: str
    content: str
    score: float
    metadata: dict
    search_type: str  # 'vector', 'keyword', 'hybrid'

class HybridSearchService:
    """하이브리드 검색 서비스"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        db: Session
    ):
        self.vector_store = vector_store
        self.db = db
    
    async def search(
        self,
        query: str,
        filters: dict,
        top_k: int = 5,
        search_mode: str = "hybrid"  # 'vector', 'keyword', 'hybrid'
    ) -> List[SearchResult]:
        """
        하이브리드 검색
        
        Args:
            query: 검색 질의
            filters: 메타데이터 필터
            top_k: 결과 수
            search_mode: 검색 모드
        """
        if search_mode == "vector":
            return await self._vector_search(query, filters, top_k)
        elif search_mode == "keyword":
            return await self._keyword_search(query, filters, top_k)
        else:  # hybrid
            return await self._hybrid_search(query, filters, top_k)
    
    async def _vector_search(
        self,
        query: str,
        filters: dict,
        top_k: int
    ) -> List[SearchResult]:
        """벡터 검색 (의미적 유사도)"""
        # 1. 질의 임베딩
        embedding = await embedding_service.embed(query)
        
        # 2. Qdrant 검색
        results = await self.vector_store.search(
            query_vector=embedding,
            filters=filters,
            top_k=top_k
        )
        
        return [
            SearchResult(
                chunk_id=r.chunk_id,
                content=r.content,
                score=r.score,
                metadata=r.metadata,
                search_type="vector"
            )
            for r in results
        ]
    
    async def _keyword_search(
        self,
        query: str,
        filters: dict,
        top_k: int
    ) -> List[SearchResult]:
        """키워드 검색 (Full-Text Search)"""
        from sqlalchemy import text, and_
        
        # 필터 조건 구성
        filter_conditions = []
        if filters.get("policy_version"):
            filter_conditions.append(
                RAGChunk.policy_version == filters["policy_version"]
            )
        if filters.get("scope_type"):
            filter_conditions.append(
                RAGChunk.scope_type == filters["scope_type"]
            )
        if filters.get("institution_id"):
            filter_conditions.append(
                RAGChunk.institution_id == filters["institution_id"]
            )
        
        # Full-Text Search
        results = self.db.query(RAGChunk).filter(
            and_(
                text(f"MATCH(content) AGAINST(:query IN NATURAL LANGUAGE MODE)"),
                *filter_conditions
            )
        ).params(query=query).limit(top_k).all()
        
        return [
            SearchResult(
                chunk_id=r.chunk_id,
                content=r.content,
                score=0.5,  # Full-text는 점수 계산 다름
                metadata=r.metadata,
                search_type="keyword"
            )
            for r in results
        ]
    
    async def _hybrid_search(
        self,
        query: str,
        filters: dict,
        top_k: int
    ) -> List[SearchResult]:
        """
        하이브리드 검색 (Reciprocal Rank Fusion)
        
        1. 벡터 검색 결과
        2. 키워드 검색 결과
        3. RRF로 재순위화
        """
        # 1. 두 검색 병렬 실행
        vector_results, keyword_results = await asyncio.gather(
            self._vector_search(query, filters, top_k * 2),
            self._keyword_search(query, filters, top_k * 2)
        )
        
        # 2. Reciprocal Rank Fusion
        rrf_scores = {}
        k = 60  # RRF 상수
        
        for rank, result in enumerate(vector_results, start=1):
            rrf_scores[result.chunk_id] = rrf_scores.get(result.chunk_id, 0) + 1 / (k + rank)
        
        for rank, result in enumerate(keyword_results, start=1):
            rrf_scores[result.chunk_id] = rrf_scores.get(result.chunk_id, 0) + 1 / (k + rank)
        
        # 3. 점수 기준 정렬
        all_results = {r.chunk_id: r for r in vector_results + keyword_results}
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # 4. Top-K 반환
        final_results = []
        for chunk_id in sorted_ids[:top_k]:
            result = all_results[chunk_id]
            result.score = rrf_scores[chunk_id]
            result.search_type = "hybrid"
            final_results.append(result)
        
        return final_results
```

---

## 4. 스트리밍 API 설계

### 4.1 Server-Sent Events (SSE) 엔드포인트

```python
# backend/app/api/v1/endpoints/rag.py

from fastapi.responses import StreamingResponse
import json

@router.post("/query/stream")
async def query_rag_stream(
    request: RAGQuery,
    current_user: User = Depends(get_current_user)
):
    """
    RAG 질의 (스트리밍)
    
    Returns:
        text/event-stream
    """
    async def event_generator():
        """SSE 이벤트 생성기"""
        query_id = str(uuid.uuid4())
        
        try:
            # 1. 시작 이벤트
            yield f"data: {json.dumps({'type': 'start', 'query_id': query_id})}\n\n"
            
            # 2. 검색 단계
            yield f"data: {json.dumps({'type': 'status', 'step': 'searching'})}\n\n"
            
            embedding = await embedding_service.embed(request.query)
            results = await vector_store.search(embedding, request.filters, request.top_k)
            
            # 3. 출처 전송
            for result in results:
                yield f"data: {json.dumps({
                    'type': 'source',
                    'chunk_id': result.chunk_id,
                    'score': result.score,
                    'metadata': result.metadata
                })}\n\n"
            
            # 4. 생성 단계
            yield f"data: {json.dumps({'type': 'status', 'step': 'generating'})}\n\n"
            
            # 5. LLM 스트리밍 호출
            prompt = rag_service._build_prompt(request.query, results)
            
            async for chunk in llm_client.stream_generate(prompt):
                yield f"data: {json.dumps({
                    'type': 'token',
                    'content': chunk
                })}\n\n"
            
            # 6. 완료 이벤트
            yield f"data: {json.dumps({
                'type': 'done',
                'query_id': query_id,
                'confidence': 0.89
            })}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({
                'type': 'error',
                'message': str(e)
            })}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

### 4.2 프론트엔드 SSE 클라이언트

```typescript
// MATHESIS-LAB_FRONT/services/ragService.ts

export const queryRAGStream = async (
  request: RAGQueryRequest,
  onToken: (token: string) => void,
  onSource: (source: RAGSource) => void,
  onComplete: (queryId: string) => void,
  onError: (error: string) => void
) => {
  const response = await fetch('/api/v1/rag/query/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request)
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        switch (data.type) {
          case 'token':
            onToken(data.content);
            break;
          case 'source':
            onSource(data);
            break;
          case 'done':
            onComplete(data.query_id);
            break;
          case 'error':
            onError(data.message);
            break;
        }
      }
    }
  }
};
```

---

## 5. 비용 관리 및 모니터링

### 5.1 개선된 rag_query_logs 테이블

```sql
CREATE TABLE rag_query_logs (
    log_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    query_id VARCHAR(36) NOT NULL UNIQUE,
    
    -- 사용자 정보
    user_id VARCHAR(36) NOT NULL,
    
    -- 질의 정보
    query_text TEXT NOT NULL,
    filters JSON,
    top_k INTEGER NOT NULL DEFAULT 5,
    
    -- 응답 정보
    answer TEXT NOT NULL,
    sources JSON NOT NULL,
    confidence FLOAT,
    
    -- ⭐ 비용 추적
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd DECIMAL(10, 6) NOT NULL DEFAULT 0.000000,
    
    -- ⭐ 성능 메트릭
    processing_time_ms INTEGER NOT NULL,
    embedding_time_ms INTEGER,
    search_time_ms INTEGER,
    llm_time_ms INTEGER,
    
    -- ⭐ 품질 메트릭
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    feedback_type VARCHAR(20),
    
    -- 타임스탬프
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 외래 키
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- 인덱스
    INDEX idx_user_id (user_id),
    INDEX idx_query_id (query_id),
    INDEX idx_created_at (created_at),
    INDEX idx_cost (estimated_cost_usd),
    
    -- 전문 검색 인덱스
    FULLTEXT INDEX idx_query_text (query_text)
);
```

### 5.2 비용 추적 로직

```python
# backend/app/services/cost_tracker.py

class CostTracker:
    """LLM 비용 추적"""
    
    # OpenAI 가격 (2025년 기준)
    PRICING = {
        "text-embedding-3-large": {
            "input": 0.00013 / 1000  # per token
        },
        "gpt-4-turbo": {
            "input": 0.01 / 1000,
            "output": 0.03 / 1000
        }
    }
    
    @staticmethod
    def calculate_cost(
        model: str,
        prompt_tokens: int,
        completion_tokens: int = 0
    ) -> float:
        """비용 계산"""
        pricing = CostTracker.PRICING.get(model, {})
        
        input_cost = prompt_tokens * pricing.get("input", 0)
        output_cost = completion_tokens * pricing.get("output", 0)
        
        return input_cost + output_cost
    
    @staticmethod
    async def log_usage(
        db: Session,
        query_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ):
        """사용량 로깅"""
        cost = CostTracker.calculate_cost(model, prompt_tokens, completion_tokens)
        
        log = db.query(RAGQueryLog).filter_by(query_id=query_id).first()
        log.prompt_tokens = prompt_tokens
        log.completion_tokens = completion_tokens
        log.total_tokens = prompt_tokens + completion_tokens
        log.estimated_cost_usd = cost
        db.commit()
```

### 5.3 비용 알림 시스템

```python
# backend/app/services/cost_alert_service.py

class CostAlertService:
    """비용 알림 서비스"""
    
    DAILY_BUDGET_USD = 100.0
    HOURLY_BUDGET_USD = 10.0
    
    @staticmethod
    async def check_budget(db: Session):
        """예산 초과 확인"""
        from datetime import datetime, timedelta
        
        # 오늘 비용
        today = datetime.now().date()
        daily_cost = db.query(
            func.sum(RAGQueryLog.estimated_cost_usd)
        ).filter(
            func.date(RAGQueryLog.created_at) == today
        ).scalar() or 0.0
        
        if daily_cost >= CostAlertService.DAILY_BUDGET_USD:
            await send_alert(
                f"⚠️ Daily budget exceeded: ${daily_cost:.2f}"
            )
            return False
        
        # 최근 1시간 비용
        one_hour_ago = datetime.now() - timedelta(hours=1)
        hourly_cost = db.query(
            func.sum(RAGQueryLog.estimated_cost_usd)
        ).filter(
            RAGQueryLog.created_at >= one_hour_ago
        ).scalar() or 0.0
        
        if hourly_cost >= CostAlertService.HOURLY_BUDGET_USD:
            await send_alert(
                f"⚠️ Hourly budget exceeded: ${hourly_cost:.2f}"
            )
            return False
        
        return True
```

---

## 6. 데이터 동기화 전략

### 6.1 Change Data Capture (CDC) 트리거

```sql
-- 원본 curriculum 삭제 시 RAG 청크도 무효화
DELIMITER $$

CREATE TRIGGER sync_curriculum_delete
AFTER DELETE ON curriculums
FOR EACH ROW
BEGIN
    -- 1. 관련 청크를 soft delete
    UPDATE rag_chunks
    SET metadata = JSON_SET(metadata, '$.deleted', TRUE),
        updated_at = NOW()
    WHERE curriculum_id = OLD.curriculum_id;
    
    -- 2. 벡터 DB 삭제 작업 큐에 추가
    INSERT INTO rag_sync_queue (
        action,
        entity_type,
        entity_id,
        created_at
    ) VALUES (
        'delete_vectors',
        'curriculum',
        OLD.curriculum_id,
        NOW()
    );
END$$

-- 원본 curriculum 수정 시 재인덱싱 필요 표시
CREATE TRIGGER sync_curriculum_update
AFTER UPDATE ON curriculums
FOR EACH ROW
BEGIN
    IF OLD.title != NEW.title OR OLD.description != NEW.description THEN
        INSERT INTO rag_sync_queue (
            action,
            entity_type,
            entity_id,
            created_at
        ) VALUES (
            'reindex',
            'curriculum',
            NEW.curriculum_id,
            NOW()
        );
    END IF;
END$$

DELIMITER ;
```

### 6.2 동기화 큐 처리 워커

```python
# backend/app/tasks/sync_tasks.py

@celery_app.task
def process_sync_queue():
    """동기화 큐 처리"""
    from backend.app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # 대기 중인 동기화 작업 조회
        pending_syncs = db.query(RAGSyncQueue).filter_by(
            status="pending"
        ).limit(100).all()
        
        for sync in pending_syncs:
            try:
                if sync.action == "delete_vectors":
                    # 벡터 DB에서 삭제
                    await vector_store.delete_by_metadata({
                        "curriculum_id": sync.entity_id
                    })
                
                elif sync.action == "reindex":
                    # 재인덱싱 작업 생성
                    # ...
                
                sync.status = "completed"
                sync.completed_at = datetime.now()
                
            except Exception as e:
                sync.status = "failed"
                sync.error_message = str(e)
            
            db.commit()
            
    finally:
        db.close()
```

---

## 7. 자동화된 품질 평가

### 7.1 CI/CD 통합 품질 테스트

```yaml
# .github/workflows/rag-quality-check.yml

name: RAG Quality Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ragas arize-phoenix
      
      - name: Run Golden Set Tests
        run: |
          pytest backend/tests/quality/test_golden_set.py \
            --junitxml=reports/golden-set-results.xml \
            --html=reports/golden-set-report.html
      
      - name: Run Ragas Evaluation
        run: |
          python backend/tests/quality/run_ragas_eval.py \
            --output reports/ragas-scores.json
      
      - name: Check Quality Thresholds
        run: |
          python backend/tests/quality/check_thresholds.py \
            --ragas-file reports/ragas-scores.json \
            --min-faithfulness 0.8 \
            --min-answer-relevancy 0.7 \
            --min-context-recall 0.7
      
      - name: Upload Quality Report
        uses: actions/upload-artifact@v2
        with:
          name: quality-reports
          path: reports/
      
      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const scores = JSON.parse(fs.readFileSync('reports/ragas-scores.json'));
            
            const comment = `
            ## 📊 RAG Quality Check Results
            
            | Metric | Score | Threshold | Status |
            |--------|-------|-----------|--------|
            | Faithfulness | ${scores.faithfulness.toFixed(2)} | 0.80 | ${scores.faithfulness >= 0.8 ? '✅' : '❌'} |
            | Answer Relevancy | ${scores.answer_relevancy.toFixed(2)} | 0.70 | ${scores.answer_relevancy >= 0.7 ? '✅' : '❌'} |
            | Context Recall | ${scores.context_recall.toFixed(2)} | 0.70 | ${scores.context_recall >= 0.7 ? '✅' : '❌'} |
            `;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### 7.2 자동화된 품질 평가 스크립트

```python
# backend/tests/quality/run_ragas_eval.py

import argparse
import json
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from backend.app.services.rag_service import RAGService

async def run_evaluation(golden_set_path: str, output_path: str):
    """Ragas 평가 실행"""
    
    # Golden Set 로드
    with open(golden_set_path) as f:
        golden_set = json.load(f)
    
    # RAG 시스템으로 답변 생성
    rag_service = RAGService(...)
    
    test_dataset = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }
    
    for test_case in golden_set:
        # 질의 실행
        response = await rag_service.query(
            RAGQuery(query=test_case["query"]),
            user_id="test_user"
        )
        
        test_dataset["question"].append(test_case["query"])
        test_dataset["answer"].append(response.answer)
        test_dataset["contexts"].append([s.content for s in response.sources])
        test_dataset["ground_truth"].append(test_case["expected_answer"])
    
    # Ragas 평가
    result = evaluate(
        test_dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision]
    )
    
    # 결과 저장
    with open(output_path, 'w') as f:
        json.dump({
            "faithfulness": float(result["faithfulness"]),
            "answer_relevancy": float(result["answer_relevancy"]),
            "context_recall": float(result["context_recall"]),
            "context_precision": float(result["context_precision"]),
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"✅ Evaluation completed. Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden-set", default="tests/fixtures/golden_set.json")
    parser.add_argument("--output", default="reports/ragas-scores.json")
    args = parser.parse_args()
    
    asyncio.run(run_evaluation(args.golden_set, args.output))
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀  
**검토자**: Enterprise Architecture Team
