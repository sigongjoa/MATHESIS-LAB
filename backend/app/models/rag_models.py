"""
RAG 시스템 데이터 모델

이 파일이 DB 스키마의 Source of Truth입니다.
DB_SCHEMA.md는 참고용이며, 실제 스키마는 이 코드에서 관리됩니다.
"""

from sqlalchemy import Column, String, Text, Integer, Float, JSON, TIMESTAMP, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.base_class import Base
import uuid


class RAGDocument(Base):
    """RAG 문서 메타데이터"""
    __tablename__ = "rag_documents"
    
    # 기본 필드
    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String(500), nullable=False, unique=True)
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    
    # 문서 분류
    document_type = Column(String(50), nullable=False, index=True)  # 'curriculum', 'school_plan'
    policy_version = Column(String(20), nullable=False, index=True)  # '2022개정'
    scope_type = Column(String(20), nullable=False, index=True)  # 'NATIONAL', 'SCHOOL'
    institution_id = Column(String(100), nullable=True)  # 학교 ID
    
    # 인덱싱 상태
    status = Column(String(20), nullable=False, default='pending', index=True)
    chunks_count = Column(Integer, default=0)
    processing_started_at = Column(TIMESTAMP, nullable=True)
    processing_completed_at = Column(TIMESTAMP, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 관계
    chunks = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")
    indexing_jobs = relationship("RAGIndexingJob", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(Base):
    """RAG 청크 데이터 (최적화된 스키마)"""
    __tablename__ = "rag_chunks"
    
    # 기본 필드
    chunk_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("rag_documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 청크 내용
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    
    # 메타데이터 (JSON) - 덜 중요한 필드만
    metadata = Column(JSON, nullable=False)
    
    # ⭐ 자주 쿼리되는 필드를 컬럼으로 승격 (ENTERPRISE_OPERATIONS.md 반영)
    policy_version = Column(String(20), nullable=False)
    scope_type = Column(String(20), nullable=False)
    institution_id = Column(String(100), nullable=True)
    grade_level = Column(String(20), nullable=True)
    domain = Column(String(50), nullable=True)
    subject = Column(String(50), nullable=True)
    curriculum_code = Column(String(50), nullable=True, index=True)
    
    # 임베딩 정보
    embedding_model = Column(String(100), nullable=False, default='text-embedding-3-large')
    embedding_dimension = Column(Integer, nullable=False, default=3072)
    vector_id = Column(String(100), nullable=True)  # Qdrant point ID
    
    # 레거시 시스템 연동
    curriculum_id = Column(String(36), ForeignKey("curriculums.curriculum_id", ondelete="SET NULL"), nullable=True, index=True)
    node_id = Column(String(36), ForeignKey("nodes.node_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 타임스탬프
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # 관계
    document = relationship("RAGDocument", back_populates="chunks")
    
    # ⭐ 복합 인덱스 (자주 사용되는 필터 조합)
    __table_args__ = (
        Index('idx_filter_national', 'policy_version', 'scope_type', 'grade_level', 'domain'),
        Index('idx_filter_school', 'policy_version', 'scope_type', 'institution_id'),
        Index('idx_document_chunk', 'document_id', 'chunk_index', unique=True),
    )


class RAGQueryLog(Base):
    """RAG 질의 로그 (비용 추적 포함)"""
    __tablename__ = "rag_query_logs"
    
    # 기본 필드
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(String(36), nullable=False, unique=True, index=True)
    
    # 사용자 정보
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 질의 정보
    query_text = Column(Text, nullable=False)
    filters = Column(JSON, nullable=True)
    top_k = Column(Integer, nullable=False, default=5)
    
    # 응답 정보
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    
    # ⭐ 비용 추적 (ENTERPRISE_OPERATIONS.md 반영)
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Float, nullable=False, default=0.0, index=True)
    
    # 성능 메트릭
    processing_time_ms = Column(Integer, nullable=False)
    embedding_time_ms = Column(Integer, nullable=True)
    search_time_ms = Column(Integer, nullable=True)
    llm_time_ms = Column(Integer, nullable=True)
    
    # 품질 메트릭
    user_rating = Column(Integer, nullable=True)
    feedback_type = Column(String(20), nullable=True)
    
    # 타임스탬프
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)


class RAGIndexingJob(Base):
    """RAG 인덱싱 작업 추적"""
    __tablename__ = "rag_indexing_jobs"
    
    # 기본 필드
    job_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("rag_documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 작업 상태
    status = Column(String(20), nullable=False, default='pending', index=True)
    progress = Column(Integer, nullable=False, default=0)
    current_step = Column(String(50), nullable=True)
    
    # 진행 상황
    chunks_processed = Column(Integer, default=0)
    chunks_total = Column(Integer, default=0)
    
    # 타임스탬프
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    estimated_completion = Column(TIMESTAMP, nullable=True)
    
    # 에러 정보
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)
    
    # 관계
    document = relationship("RAGDocument", back_populates="indexing_jobs")


class RAGSyncQueue(Base):
    """데이터 동기화 큐 (CDC)"""
    __tablename__ = "rag_sync_queue"
    
    # 기본 필드
    sync_id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(50), nullable=False)  # 'delete_vectors', 'reindex'
    entity_type = Column(String(50), nullable=False)  # 'curriculum', 'node'
    entity_id = Column(String(36), nullable=False, index=True)
    
    # 상태
    status = Column(String(20), nullable=False, default='pending', index=True)
    error_message = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
