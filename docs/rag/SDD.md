# RAG 시스템 상세 설계서 (SDD)

## 📋 목차
1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 상세](#2-아키텍처-상세)
3. [컴포넌트 설계](#3-컴포넌트-설계)
4. [데이터 흐름](#4-데이터-흐름)
5. [예외 처리 전략](#5-예외-처리-전략)
6. [레거시 통합](#6-레거시-통합)
7. [성능 요구사항](#7-성능-요구사항)

---

## 1. 시스템 개요

### 1.1 목적
기존 MATHESIS LAB 시스템에 RAG(Retrieval-Augmented Generation) 기능을 통합하여, 교육과정 문서 기반 질의응답 및 분석 기능 제공

### 1.2 범위
- **In-Scope**: 문서 파싱, 벡터 검색, LLM 기반 답변 생성, 근거 인용
- **Out-of-Scope**: 실시간 협업, 음성 인터페이스, 자동 번역

### 1.3 기술 스택

| 계층 | 기술 | 버전 | 이유 |
|------|------|------|------|
| **Backend** | FastAPI | 0.104+ | 비동기 지원, Pydantic 통합 |
| **ORM** | SQLAlchemy | 2.0+ | 기존 시스템과 일관성 |
| **Vector DB** | Qdrant | 1.7+ | 메타데이터 필터링, 오픈소스 |
| **Embedding** | OpenAI text-embedding-3-large | - | 한국어 성능 우수 |
| **LLM** | OpenAI GPT-4 Turbo | - | 추론 능력, 한국어 지원 |
| **Parser** | PyMuPDF, python-hwp | - | PDF/HWP 지원 |
| **Testing** | pytest, pytest-asyncio | - | 비동기 테스트 지원 |

---

## 2. 아키텍처 상세

### 2.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + TypeScript)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ NodeGraph    │  │ AIAssistant  │  │ RAGChat      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │ REST API         │ REST API         │ WebSocket (선택)
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Layer (v1/endpoints/)               │   │
│  │  /rag/query  /rag/index  /rag/status  /rag/feedback │   │
│  └────────┬──────────────────────────┬──────────────────┘   │
│           │                          │                      │
│  ┌────────▼──────────┐      ┌────────▼──────────┐          │
│  │  RAG Service      │      │  Parser Service   │          │
│  │  - Query          │      │  - PDF Parser     │          │
│  │  - Retrieval      │      │  - HWP Parser     │          │
│  │  - Generation     │      │  - Metadata Ext.  │          │
│  └────────┬──────────┘      └────────┬──────────┘          │
│           │                          │                      │
│  ┌────────▼──────────────────────────▼──────────┐          │
│  │           Data Access Layer                  │          │
│  │  - PostgreSQL (Metadata, Logs)               │          │
│  │  - Qdrant (Vector Embeddings)                │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
          │                          │
          ▼                          ▼
┌─────────────────┐        ┌─────────────────┐
│   PostgreSQL    │        │     Qdrant      │
│   (기존 DB)     │        │  (Vector Store) │
└─────────────────┘        └─────────────────┘
```

### 2.2 레이어별 책임

| 레이어 | 책임 | 주요 클래스/파일 |
|--------|------|-----------------|
| **API Layer** | HTTP 요청 처리, 인증, 입력 검증 | `backend/app/api/v1/endpoints/rag.py` |
| **Service Layer** | 비즈니스 로직, 트랜잭션 관리 | `backend/app/services/rag_service.py` |
| **Repository Layer** | 데이터 접근, 쿼리 최적화 | `backend/app/repositories/rag_repository.py` |
| **Model Layer** | 데이터 모델, 스키마 정의 | `backend/app/models/rag_chunk.py` |

---

## 3. 컴포넌트 설계

### 3.1 Parser Service

#### 책임
- PDF/HWP 문서를 구조적으로 파싱
- 메타데이터 자동 추출
- 청크 생성 및 검증

#### 인터페이스

```python
# backend/app/services/parser_service.py

from typing import List, Dict, Any
from pathlib import Path
from pydantic import BaseModel

class ParsedChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int]
    
class ParserService:
    """문서 파싱 서비스"""
    
    async def parse_document(
        self, 
        file_path: Path,
        document_type: str  # "curriculum" or "school_plan"
    ) -> List[ParsedChunk]:
        """
        문서를 파싱하여 청크 리스트 반환
        
        Args:
            file_path: 문서 파일 경로
            document_type: 문서 유형
            
        Returns:
            ParsedChunk 리스트
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            ParseError: 파싱 실패
            ValidationError: 메타데이터 검증 실패
        """
        pass
    
    async def extract_metadata(
        self,
        file_path: Path,
        content: str
    ) -> Dict[str, Any]:
        """
        문서에서 메타데이터 추출
        
        Returns:
            METADATA_SCHEMA.md에 정의된 형식의 메타데이터
        """
        pass
    
    def validate_chunk(self, chunk: ParsedChunk) -> bool:
        """청크 유효성 검증"""
        pass
```

#### 구현 세부사항

**PDF 파싱 (PyMuPDF)**
```python
import fitz  # PyMuPDF
import re

async def _parse_pdf(self, file_path: Path) -> List[ParsedChunk]:
    """PDF 파싱 구현"""
    chunks = []
    doc = fitz.open(file_path)
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        
        # 성취기준 코드 패턴 감지
        achievement_codes = re.findall(r'\[(\d+[가-힣]+\d+-\d+)\]', text)
        
        if achievement_codes:
            # 성취기준 단위로 청킹
            for code in achievement_codes:
                chunk_content = self._extract_achievement_section(text, code)
                metadata = {
                    "curriculum_code": f"[{code}]",
                    "page_number": page_num,
                    "document_type": "성취기준"
                }
                chunks.append(ParsedChunk(
                    content=chunk_content,
                    metadata=metadata,
                    page_number=page_num
                ))
        else:
            # 일반 텍스트 청킹 (1000자 단위)
            for i in range(0, len(text), 1000):
                chunk_content = text[i:i+1000]
                metadata = {
                    "page_number": page_num,
                    "document_type": "일반"
                }
                chunks.append(ParsedChunk(
                    content=chunk_content,
                    metadata=metadata,
                    page_number=page_num
                ))
    
    return chunks
```

**HWP 파싱 (python-hwp)**
```python
from hwp5 import hwp5txt

async def _parse_hwp(self, file_path: Path) -> List[ParsedChunk]:
    """HWP 파싱 구현"""
    # HWP를 텍스트로 변환
    text = hwp5txt(str(file_path))
    
    # 학교 계획 문서는 섹션 단위로 청킹
    sections = self._split_by_sections(text)
    
    chunks = []
    for section_title, section_content in sections:
        metadata = {
            "document_type": self._classify_section(section_title),
            "section_title": section_title
        }
        chunks.append(ParsedChunk(
            content=section_content,
            metadata=metadata
        ))
    
    return chunks
```

### 3.2 RAG Service

#### 책임
- 사용자 질의 처리
- 벡터 검색 실행
- LLM 답변 생성
- 근거 인용 관리

#### 인터페이스

```python
# backend/app/services/rag_service.py

from typing import List, Optional
from pydantic import BaseModel

class RAGQuery(BaseModel):
    """RAG 질의 요청"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = 5
    include_sources: bool = True

class RAGSource(BaseModel):
    """검색된 소스"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    page_number: Optional[int]

class RAGResponse(BaseModel):
    """RAG 응답"""
    answer: str
    sources: List[RAGSource]
    confidence: float
    processing_time_ms: int

class RAGService:
    """RAG 서비스"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: LLMClient,
        db: Session
    ):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.db = db
    
    async def query(self, request: RAGQuery, user_id: str) -> RAGResponse:
        """
        RAG 질의 처리
        
        1. 질의 임베딩
        2. 벡터 검색 (메타데이터 필터링)
        3. 재순위화 (Re-ranking)
        4. LLM 프롬프트 구성
        5. 답변 생성
        6. 인용 추가
        7. 로그 저장
        
        Args:
            request: RAG 질의 요청
            user_id: 사용자 ID
            
        Returns:
            RAG 응답
            
        Raises:
            VectorSearchError: 검색 실패
            LLMError: LLM 호출 실패
            ValidationError: 응답 검증 실패
        """
        start_time = time.time()
        
        try:
            # 1. 질의 임베딩
            query_embedding = await self._embed_query(request.query)
            
            # 2. 벡터 검색
            search_results = await self._search_vectors(
                query_embedding,
                filters=request.filters,
                top_k=request.top_k
            )
            
            # 3. 재순위화
            reranked_results = await self._rerank(request.query, search_results)
            
            # 4. LLM 프롬프트 구성
            prompt = self._build_prompt(request.query, reranked_results)
            
            # 5. 답변 생성
            answer = await self._generate_answer(prompt)
            
            # 6. 인용 추가
            answer_with_citations = self._add_citations(answer, reranked_results)
            
            # 7. 로그 저장
            await self._log_query(user_id, request, answer_with_citations)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return RAGResponse(
                answer=answer_with_citations,
                sources=[self._to_source(r) for r in reranked_results],
                confidence=self._calculate_confidence(reranked_results),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            await self._log_error(user_id, request, str(e))
            raise
    
    async def _embed_query(self, query: str) -> List[float]:
        """질의 임베딩"""
        pass
    
    async def _search_vectors(
        self,
        embedding: List[float],
        filters: Optional[Dict],
        top_k: int
    ) -> List[SearchResult]:
        """벡터 검색"""
        pass
    
    async def _rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """재순위화"""
        pass
    
    def _build_prompt(
        self,
        query: str,
        sources: List[SearchResult]
    ) -> str:
        """LLM 프롬프트 구성"""
        return f"""당신은 교육과정 전문가입니다. 다음 근거를 바탕으로 질문에 답변하세요.

**중요 규칙:**
1. 제공된 근거에만 기반하여 답변하세요
2. 모든 사실에 대해 <출처: [chunk_id]> 형식으로 인용하세요
3. 근거가 불충분하면 "제공된 문서에는 해당 정보가 없습니다"라고 답하세요

**근거:**
{self._format_sources(sources)}

**질문:** {query}

**답변:**"""
    
    async def _generate_answer(self, prompt: str) -> str:
        """LLM 답변 생성"""
        pass
    
    def _add_citations(self, answer: str, sources: List[SearchResult]) -> str:
        """인용 추가"""
        pass
```

### 3.3 Vector Store Wrapper

#### 책임
- Qdrant와의 통신
- 메타데이터 필터링
- 벡터 CRUD 작업

#### 인터페이스

```python
# backend/app/services/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter

class VectorStore:
    """벡터 저장소 래퍼"""
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_name = "rag_chunks"
    
    async def initialize(self):
        """컬렉션 초기화"""
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=3072,  # text-embedding-3-large dimension
                distance=Distance.COSINE
            )
        )
    
    async def upsert(
        self,
        chunk_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        content: str
    ):
        """벡터 삽입/업데이트"""
        point = PointStruct(
            id=chunk_id,
            vector=embedding,
            payload={
                "content": content,
                **metadata
            }
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
    
    async def search(
        self,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """벡터 검색"""
        # 메타데이터 필터 구성
        qdrant_filter = self._build_filter(filters) if filters else None
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k
        )
        
        return [
            SearchResult(
                chunk_id=str(r.id),
                content=r.payload["content"],
                score=r.score,
                metadata=r.payload
            )
            for r in results
        ]
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """메타데이터 필터 구성"""
        from qdrant_client.models import FieldCondition, MatchValue
        
        conditions = []
        for key, value in filters.items():
            conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
            )
        
        return Filter(must=conditions)
```

---

## 4. 데이터 흐름

### 4.1 문서 인덱싱 플로우

```
[사용자] → [POST /api/v1/rag/index]
    ↓
[API Layer] 파일 업로드 검증
    ↓
[Parser Service] 문서 파싱
    ├─ PDF/HWP 읽기
    ├─ 구조 분석
    ├─ 청크 생성
    └─ 메타데이터 추출
    ↓
[Embedding Service] 임베딩 생성
    └─ OpenAI API 호출
    ↓
[Vector Store] 벡터 저장
    └─ Qdrant에 upsert
    ↓
[PostgreSQL] 메타데이터 저장
    └─ rag_chunks 테이블에 INSERT
    ↓
[Response] {"status": "indexed", "chunks_count": 42}
```

### 4.2 질의 응답 플로우

```
[사용자] → [POST /api/v1/rag/query]
    ↓
[API Layer] 요청 검증
    ↓
[RAG Service] 질의 처리
    ├─ [1] 질의 임베딩
    │   └─ OpenAI Embedding API
    ├─ [2] 벡터 검색
    │   └─ Qdrant 검색 (메타데이터 필터링)
    ├─ [3] 재순위화 (선택)
    │   └─ Cross-Encoder 모델
    ├─ [4] 프롬프트 구성
    │   └─ 근거 + 질문 조합
    ├─ [5] LLM 호출
    │   └─ OpenAI GPT-4 API
    └─ [6] 인용 추가
        └─ <출처: ...> 태그 삽입
    ↓
[PostgreSQL] 로그 저장
    └─ rag_query_logs 테이블에 INSERT
    ↓
[Response] {"answer": "...", "sources": [...]}
```

### 4.3 트랜잭션 처리

```python
# 인덱싱 트랜잭션
async def index_document(file_path: Path, db: Session):
    try:
        # 1. 파싱 (외부 의존성 없음)
        chunks = await parser_service.parse_document(file_path)
        
        # 2. DB 트랜잭션 시작
        async with db.begin():
            # 2-1. 메타데이터 저장
            for chunk in chunks:
                db_chunk = RAGChunk(**chunk.dict())
                db.add(db_chunk)
            
            # 2-2. 임베딩 생성 (외부 API)
            embeddings = await embedding_service.embed_batch(
                [c.content for c in chunks]
            )
            
            # 2-3. 벡터 저장 (외부 DB)
            await vector_store.upsert_batch(chunks, embeddings)
            
            # 모든 작업 성공 시 커밋
            await db.commit()
            
    except Exception as e:
        # 롤백
        await db.rollback()
        # 벡터 DB 정리 (보상 트랜잭션)
        await vector_store.delete_batch([c.chunk_id for c in chunks])
        raise
```

---

## 5. 예외 처리 전략

### 5.1 예외 계층 구조

```python
# backend/app/exceptions/rag_exceptions.py

class RAGException(Exception):
    """RAG 시스템 기본 예외"""
    pass

class ParseError(RAGException):
    """파싱 실패"""
    pass

class ValidationError(RAGException):
    """검증 실패"""
    pass

class VectorSearchError(RAGException):
    """벡터 검색 실패"""
    pass

class LLMError(RAGException):
    """LLM 호출 실패"""
    pass

class QuotaExceededError(LLMError):
    """API 할당량 초과"""
    pass
```

### 5.2 재시도 로직

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class RAGService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(VectorSearchError)
    )
    async def _search_vectors(self, ...):
        """벡터 검색 (재시도 포함)"""
        try:
            return await self.vector_store.search(...)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorSearchError(str(e))
```

### 5.3 타임아웃 처리

```python
import asyncio

async def query_with_timeout(request: RAGQuery) -> RAGResponse:
    """타임아웃이 있는 질의"""
    try:
        return await asyncio.wait_for(
            rag_service.query(request),
            timeout=30.0  # 30초
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query processing timeout"
        )
```

---

## 6. 레거시 통합

### 6.1 기존 시스템과의 연동 지점

| 기존 컴포넌트 | 연동 방식 | 데이터 흐름 |
|-------------|----------|-----------|
| **Curriculum Model** | Foreign Key | `rag_chunks.curriculum_id → curriculums.curriculum_id` |
| **Node Model** | Foreign Key | `rag_chunks.node_id → nodes.node_id` (선택) |
| **NodeGraph.tsx** | REST API | `GET /api/v1/rag/related-nodes?node_id=xxx` |
| **AIAssistant.tsx** | REST API | `POST /api/v1/rag/query` |

### 6.2 데이터 모델 확장

```python
# backend/app/models/rag_chunk.py

from sqlalchemy import Column, String, Text, JSON, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base
import uuid

class RAGChunk(Base):
    __tablename__ = "rag_chunks"
    
    # 기본 필드
    chunk_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False)
    
    # 임베딩 정보
    embedding_model = Column(String(100), default="text-embedding-3-large")
    embedding_dimension = Column(Integer, default=3072)
    
    # 레거시 연동
    curriculum_id = Column(String(36), ForeignKey("curriculums.curriculum_id"), nullable=True)
    node_id = Column(String(36), ForeignKey("nodes.node_id"), nullable=True)
    
    # 관계
    curriculum = relationship("Curriculum", back_populates="rag_chunks")
    node = relationship("Node", back_populates="rag_chunks")
    
    # 타임스탬프
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 6.3 프론트엔드 통합

```typescript
// MATHESIS-LAB_FRONT/services/ragService.ts

export interface RAGQueryRequest {
  query: string;
  filters?: {
    curriculum_id?: string;
    node_id?: string;
    policy_version?: string;
    scope_type?: 'NATIONAL' | 'SCHOOL';
  };
  top_k?: number;
}

export interface RAGSource {
  chunk_id: string;
  content: string;
  score: number;
  metadata: Record<string, any>;
}

export interface RAGQueryResponse {
  answer: string;
  sources: RAGSource[];
  confidence: number;
  processing_time_ms: number;
}

export const queryRAG = async (request: RAGQueryRequest): Promise<RAGQueryResponse> => {
  const response = await fetch('/api/v1/rag/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(request)
  });
  
  if (!response.ok) {
    throw new Error('RAG query failed');
  }
  
  return response.json();
};
```

---

## 7. 성능 요구사항

### 7.1 응답 시간

| 작업 | 목표 | 최대 허용 |
|------|------|----------|
| 질의 응답 (P95) | < 3초 | < 5초 |
| 문서 인덱싱 (100페이지) | < 2분 | < 5분 |
| 벡터 검색 | < 500ms | < 1초 |

### 7.2 처리량

- **동시 질의**: 10 QPS (Queries Per Second)
- **일일 질의**: 최대 10,000건
- **인덱싱**: 시간당 100개 문서

### 7.3 최적화 전략

```python
# 1. 임베딩 배치 처리
async def embed_batch(texts: List[str], batch_size: int = 100):
    """배치 임베딩으로 API 호출 최소화"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = await openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        embeddings.extend([e.embedding for e in batch_embeddings.data])
    return embeddings

# 2. 캐싱
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding_cached(text: str) -> List[float]:
    """자주 사용되는 질의 임베딩 캐싱"""
    return openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    ).data[0].embedding
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀  
**검토자**: [검토 필요]
