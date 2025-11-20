"""
RAG API 엔드포인트

이 파일이 API의 Source of Truth입니다.
FastAPI가 자동으로 Swagger UI를 생성합니다: http://localhost:8000/docs
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from backend.app.schemas.rag_schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    IndexingJobResponse,
    IndexingJobStatus,
    FeedbackRequest,
    FeedbackResponse,
    AnalyticsResponse,
    ErrorResponse
)
from backend.app.db.session import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.models.user import User

# TODO: 서비스 임포트 (구현 후)
# from backend.app.services.rag.rag_service import RAGService
# from backend.app.tasks.rag.indexing_tasks import index_document_task

router = APIRouter(prefix="/rag", tags=["RAG"])


# ============================================================================
# 질의 응답
# ============================================================================

@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG 질의",
    description="사용자 질문에 대해 RAG 기반 답변을 생성합니다.",
    responses={
        200: {"description": "성공", "model": RAGQueryResponse},
        400: {"description": "잘못된 요청", "model": ErrorResponse},
        429: {"description": "요청 제한 초과", "model": ErrorResponse},
        504: {"description": "타임아웃", "model": ErrorResponse}
    }
)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG 질의 응답
    
    **처리 단계:**
    1. 질의 임베딩
    2. 벡터 검색 (메타데이터 필터링)
    3. 재순위화 (Re-ranking)
    4. LLM 프롬프트 구성
    5. 답변 생성
    6. 인용 추가
    7. 로그 저장
    
    **예시:**
    ```json
    {
      "query": "초등학교 5~6학년 수학에서 최대공약수는 소인수분해로 다루나요?",
      "filters": {
        "policy_version": "2022개정",
        "grade_level": "초5~6"
      }
    }
    ```
    """
    # TODO: 실제 구현
    # rag_service = RAGService(db)
    # response = await rag_service.query(request, current_user.user_id)
    # return response
    
    # 임시 응답 (스켈레톤)
    return RAGQueryResponse(
        answer="[구현 예정] 질의: " + request.query,
        sources=[],
        confidence=0.0,
        processing_time_ms=0,
        query_id="temp_query_id"
    )


@router.post(
    "/query/stream",
    summary="RAG 질의 (스트리밍)",
    description="Server-Sent Events를 통한 스트리밍 응답",
    responses={
        200: {"description": "text/event-stream"}
    }
)
async def query_rag_stream(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG 질의 (스트리밍)
    
    **SSE 이벤트 타입:**
    - `start`: 시작
    - `source`: 출처 정보
    - `token`: 생성된 토큰
    - `citation`: 인용
    - `done`: 완료
    - `error`: 에러
    """
    async def event_generator():
        """SSE 이벤트 생성기"""
        # TODO: 실제 구현
        yield f"data: {json.dumps({'type': 'start', 'query_id': 'temp_id'})}\n\n"
        yield f"data: {json.dumps({'type': 'token', 'content': '[구현 예정]'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'confidence': 0.0})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# 문서 인덱싱
# ============================================================================

@router.post(
    "/index",
    response_model=IndexingJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="문서 인덱싱",
    description="새로운 문서를 파싱하고 벡터 DB에 인덱싱합니다 (비동기).",
    responses={
        202: {"description": "작업 시작됨", "model": IndexingJobResponse},
        400: {"description": "잘못된 요청", "model": ErrorResponse},
        503: {"description": "서비스 일시 중단", "model": ErrorResponse}
    }
)
async def index_document(
    file: UploadFile = File(..., description="PDF 또는 HWP 파일 (최대 50MB)"),
    document_type: str = Form(..., description="문서 유형 (curriculum/school_plan)"),
    metadata: str = Form(..., description="문서 메타데이터 (JSON)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    문서 인덱싱 (비동기)
    
    **처리 단계:**
    1. 파일 저장
    2. Document 레코드 생성
    3. Job 생성
    4. Celery 태스크 실행
    5. Job ID 반환
    
    **Fallback 전략:**
    - Redis 장애 시: 10MB 이하 파일만 동기 처리
    """
    # TODO: 실제 구현
    # 1. 파일 저장
    # 2. Document 생성
    # 3. Job 생성
    # 4. Celery 태스크 실행
    
    return IndexingJobResponse(
        status="accepted",
        job_id="temp_job_id",
        estimated_time_seconds=120,
        message="Document indexing started (구현 예정)"
    )


@router.get(
    "/status/{job_id}",
    response_model=IndexingJobStatus,
    summary="인덱싱 상태 확인",
    description="인덱싱 작업의 진행 상태를 확인합니다."
)
async def get_indexing_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """인덱싱 작업 상태 조회"""
    # TODO: 실제 구현
    return IndexingJobStatus(
        job_id=job_id,
        status="processing",
        progress=50,
        current_step="embedding_generation",
        chunks_processed=25,
        chunks_total=50
    )


# ============================================================================
# 검색 (디버깅용)
# ============================================================================

@router.get(
    "/search",
    summary="청크 검색 (디버깅용)",
    description="벡터 검색만 수행하고 LLM 생성 없이 결과를 반환합니다."
)
async def search_chunks(
    query: str,
    top_k: int = 5,
    policy_version: Optional[str] = None,
    scope_type: Optional[str] = None,
    grade_level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """청크 검색 (디버깅용)"""
    # TODO: 실제 구현
    return {
        "results": [],
        "total": 0,
        "query_embedding_time_ms": 0
    }


# ============================================================================
# 피드백
# ============================================================================

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="답변 피드백",
    description="사용자가 답변에 대한 피드백을 제공합니다."
)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """답변 피드백 제출"""
    # TODO: 실제 구현
    return FeedbackResponse(
        status="recorded",
        feedback_id="temp_feedback_id"
    )


# ============================================================================
# 분석
# ============================================================================

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="사용 통계",
    description="RAG 시스템의 사용 통계를 조회합니다."
)
async def get_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용 통계 조회"""
    # TODO: 실제 구현
    return AnalyticsResponse(
        period={"start": start_date or "2025-11-01", "end": end_date or "2025-11-20"},
        total_queries=0,
        avg_response_time_ms=0,
        avg_confidence=0.0,
        top_queries=[],
        feedback_summary={}
    )
