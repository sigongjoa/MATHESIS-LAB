"""
RAG API Pydantic 스키마

이 파일이 API 명세의 Source of Truth입니다.
API_SPEC.md는 참고용이며, 실제 API는 이 코드에서 자동 생성됩니다 (Swagger).
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ScopeType(str, Enum):
    """문서 범위 유형"""
    NATIONAL = "NATIONAL"
    SCHOOL = "SCHOOL"


class DocumentType(str, Enum):
    """문서 유형"""
    CURRICULUM = "curriculum"
    SCHOOL_PLAN = "school_plan"


class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackType(str, Enum):
    """피드백 유형"""
    HELPFUL = "helpful"
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    IRRELEVANT = "irrelevant"


# ============================================================================
# Request Schemas
# ============================================================================

class RAGQueryFilters(BaseModel):
    """RAG 질의 필터"""
    policy_version: Optional[str] = Field(None, description="교육과정 버전 (예: '2022개정')")
    scope_type: Optional[ScopeType] = Field(None, description="문서 범위")
    institution_id: Optional[str] = Field(None, description="학교 ID")
    grade_level: Optional[str] = Field(None, description="학년 (예: '초5~6')")
    domain: Optional[str] = Field(None, description="영역 (예: '수와 연산')")
    curriculum_id: Optional[str] = Field(None, description="커리큘럼 ID")
    node_id: Optional[str] = Field(None, description="노드 ID")
    
    class Config:
        schema_extra = {
            "example": {
                "policy_version": "2022개정",
                "scope_type": "NATIONAL",
                "grade_level": "초5~6",
                "domain": "수와 연산"
            }
        }


class RAGQueryRequest(BaseModel):
    """RAG 질의 요청"""
    query: str = Field(..., min_length=1, max_length=1000, description="사용자 질문")
    filters: Optional[RAGQueryFilters] = Field(None, description="메타데이터 필터")
    top_k: int = Field(5, ge=1, le=20, description="검색할 청크 수")
    include_sources: bool = Field(True, description="출처 포함 여부")
    stream: bool = Field(False, description="스트리밍 응답 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "초등학교 5~6학년 수학에서 최대공약수는 소인수분해로 다루나요?",
                "filters": {
                    "policy_version": "2022개정",
                    "scope_type": "NATIONAL",
                    "grade_level": "초5~6"
                },
                "top_k": 5,
                "include_sources": True,
                "stream": False
            }
        }


class IndexDocumentRequest(BaseModel):
    """문서 인덱싱 요청 (메타데이터)"""
    document_type: DocumentType = Field(..., description="문서 유형")
    policy_version: str = Field(..., description="교육과정 버전")
    scope_type: ScopeType = Field(..., description="문서 범위")
    institution_id: Optional[str] = Field(None, description="학교 ID (SCHOOL인 경우 필수)")
    
    @validator('institution_id')
    def validate_institution_id(cls, v, values):
        """SCHOOL인 경우 institution_id 필수"""
        if values.get('scope_type') == ScopeType.SCHOOL and not v:
            raise ValueError('institution_id is required for SCHOOL scope')
        return v


class FeedbackRequest(BaseModel):
    """피드백 요청"""
    query_id: str = Field(..., description="질의 ID")
    rating: int = Field(..., ge=1, le=5, description="평점 (1~5)")
    feedback_type: Optional[FeedbackType] = Field(None, description="피드백 유형")
    comment: Optional[str] = Field(None, max_length=500, description="추가 코멘트")


# ============================================================================
# Response Schemas
# ============================================================================

class RAGSource(BaseModel):
    """검색된 출처"""
    chunk_id: str = Field(..., description="청크 고유 ID")
    content: str = Field(..., description="청크 내용")
    score: float = Field(..., ge=0, le=1, description="유사도 점수")
    metadata: Dict[str, Any] = Field(..., description="메타데이터")
    
    class Config:
        schema_extra = {
            "example": {
                "chunk_id": "chunk_123",
                "content": "최대공약수와 최소공배수는 약수와 배수를 나열하여...",
                "score": 0.89,
                "metadata": {
                    "policy_version": "2022개정",
                    "curriculum_code": "[6수01-05]",
                    "page_number": 42
                }
            }
        }


class RAGQueryResponse(BaseModel):
    """RAG 질의 응답"""
    answer: str = Field(..., description="생성된 답변 (인용 포함)")
    sources: List[RAGSource] = Field(..., description="검색된 출처 목록")
    confidence: float = Field(..., ge=0, le=1, description="답변 신뢰도")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")
    query_id: str = Field(..., description="질의 고유 ID")
    
    class Config:
        schema_extra = {
            "example": {
                "answer": "아닙니다. <출처: chunk_123> 소인수분해로 다루지 않습니다.",
                "sources": [
                    {
                        "chunk_id": "chunk_123",
                        "content": "최대공약수와 최소공배수는...",
                        "score": 0.89,
                        "metadata": {"policy_version": "2022개정"}
                    }
                ],
                "confidence": 0.89,
                "processing_time_ms": 2341,
                "query_id": "q_550e8400-e29b-41d4-a716-446655440000"
            }
        }


class IndexingJobResponse(BaseModel):
    """인덱싱 작업 응답"""
    status: Literal["accepted", "processing", "completed", "failed"]
    job_id: str = Field(..., description="작업 ID")
    task_id: Optional[str] = Field(None, description="Celery 태스크 ID")
    estimated_time_seconds: Optional[int] = Field(None, description="예상 소요 시간")
    chunks_created: Optional[int] = Field(None, description="생성된 청크 수")
    message: Optional[str] = Field(None, description="메시지")


class IndexingJobStatus(BaseModel):
    """인덱싱 작업 상태"""
    job_id: str
    status: JobStatus
    progress: int = Field(..., ge=0, le=100, description="진행률 (%)")
    current_step: Optional[str] = Field(None, description="현재 단계")
    chunks_processed: int = Field(0, description="처리된 청크 수")
    chunks_total: int = Field(0, description="전체 청크 수")
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


class FeedbackResponse(BaseModel):
    """피드백 응답"""
    status: Literal["recorded"]
    feedback_id: str


class AnalyticsResponse(BaseModel):
    """사용 통계 응답"""
    period: Dict[str, str]
    total_queries: int
    avg_response_time_ms: int
    avg_confidence: float
    top_queries: List[Dict[str, Any]]
    feedback_summary: Dict[str, Any]


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """에러 응답"""
    detail: str = Field(..., description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")
    error_id: Optional[str] = Field(None, description="에러 추적 ID")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": "Query processing timeout",
                "error_code": "TIMEOUT_ERROR",
                "error_id": "err_123456"
            }
        }


# ============================================================================
# Streaming Event Schemas
# ============================================================================

class StreamEvent(BaseModel):
    """스트리밍 이벤트 (SSE)"""
    type: Literal["start", "source", "token", "citation", "done", "error"]
    data: Dict[str, Any]


class StreamStartEvent(BaseModel):
    """스트리밍 시작 이벤트"""
    type: Literal["start"] = "start"
    query_id: str


class StreamSourceEvent(BaseModel):
    """출처 이벤트"""
    type: Literal["source"] = "source"
    chunk_id: str
    score: float
    metadata: Dict[str, Any]


class StreamTokenEvent(BaseModel):
    """토큰 이벤트"""
    type: Literal["token"] = "token"
    content: str


class StreamDoneEvent(BaseModel):
    """완료 이벤트"""
    type: Literal["done"] = "done"
    query_id: str
    confidence: float
    processing_time_ms: int


class StreamErrorEvent(BaseModel):
    """에러 이벤트"""
    type: Literal["error"] = "error"
    message: str
    error_code: Optional[str] = None
