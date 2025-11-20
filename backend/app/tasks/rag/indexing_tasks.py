"""
RAG 인덱싱 Celery Tasks
"""

from celery import Task
from pathlib import Path
from datetime import datetime
import traceback
import logging

from backend.app.celery_app import celery_app
from backend.app.db.session import SessionLocal
from backend.app.models.rag_models import RAGDocument, RAGChunk, RAGIndexingJob
from backend.app.services.rag.parser_service import ParserService
from backend.app.services.rag.embedding_service import EmbeddingService
from backend.app.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """진행 상황 업데이트를 위한 베이스 태스크"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """성공 시 콜백"""
        job_id = kwargs.get('job_id')
        logger.info(f"Task {task_id} succeeded for job {job_id}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """실패 시 콜백"""
        job_id = kwargs.get('job_id')
        logger.error(f"Task {task_id} failed for job {job_id}: {exc}")


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
    db = SessionLocal()
    
    try:
        # 1. Job 상태 업데이트: PROCESSING
        job = db.query(RAGIndexingJob).filter_by(job_id=job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        job.status = "processing"
        job.current_step = "parsing"
        job.started_at = datetime.now()
        db.commit()
        
        # 2. 문서 조회
        document = db.query(RAGDocument).filter_by(document_id=document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # 3. 문서 파싱
        parser = ParserService()
        
        # 기본 메타데이터
        base_metadata = {
            "policy_version": document.policy_version,
            "scope_type": document.scope_type,
            "institution_id": document.institution_id
        }
        
        # 비동기 함수를 동기로 실행
        import asyncio
        chunks = asyncio.run(
            parser.parse_document(
                Path(file_path),
                document.document_type,
                base_metadata
            )
        )
        
        job.chunks_total = len(chunks)
        job.current_step = "embedding"
        db.commit()
        
        # 4. 임베딩 생성 (배치 처리)
        embedding_service = EmbeddingService()
        
        embeddings = asyncio.run(
            embedding_service.embed_batch(
                [c.content for c in chunks],
                batch_size=100
            )
        )
        
        # 5. 벡터 DB 및 RDB 저장
        vector_store = VectorStore()
        
        # 컬렉션 초기화
        asyncio.run(vector_store.initialize_collection())
        
        job.current_step = "indexing"
        db.commit()
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # 진행률 업데이트
            job.chunks_processed = i + 1
            job.progress = int((job.chunks_processed / job.chunks_total) * 100)
            
            if i % 10 == 0:  # 10개마다 커밋
                db.commit()
            
            # Celery 진행 상황 업데이트
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': job.chunks_processed,
                    'total': job.chunks_total,
                    'step': 'indexing'
                }
            )
            
            # 청크 ID 생성
            import uuid
            chunk_id = str(uuid.uuid4())
            
            # 벡터 DB 저장
            asyncio.run(
                vector_store.upsert(
                    chunk_id=chunk_id,
                    embedding=embedding,
                    metadata=chunk.metadata,
                    content=chunk.content
                )
            )
            
            # RDB 저장
            content_hash = ParserService.calculate_content_hash(chunk.content)
            
            db_chunk = RAGChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk.content,
                content_hash=content_hash,
                chunk_index=chunk.chunk_index,
                metadata=chunk.metadata,
                # 자주 쿼리되는 필드 승격
                policy_version=chunk.metadata.get("policy_version"),
                scope_type=chunk.metadata.get("scope_type"),
                institution_id=chunk.metadata.get("institution_id"),
                grade_level=chunk.metadata.get("grade_level"),
                domain=chunk.metadata.get("domain"),
                subject=chunk.metadata.get("subject"),
                curriculum_code=chunk.metadata.get("curriculum_code"),
                vector_id=chunk_id
            )
            db.add(db_chunk)
        
        db.commit()
        
        # 6. Job 완료
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now()
        
        # Document 상태 업데이트
        document.status = "completed"
        document.chunks_count = len(chunks)
        document.processing_completed_at = datetime.now()
        
        db.commit()
        
        logger.info(f"Indexing completed: {document_id} ({len(chunks)} chunks)")
        
        return {
            "status": "completed",
            "chunks_created": len(chunks),
            "document_id": document_id
        }
        
    except Exception as e:
        # 에러 처리
        logger.error(f"Indexing failed: {e}")
        logger.error(traceback.format_exc())
        
        try:
            job.status = "failed"
            job.error_message = str(e)
            job.error_stack = traceback.format_exc()
            
            document.status = "failed"
            document.error_message = str(e)
            
            db.commit()
        except:
            db.rollback()
        
        # 재시도
        raise self.retry(exc=e)
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_logs():
    """오래된 로그 정리 (주기적 실행)"""
    from datetime import timedelta
    from backend.app.models.rag_models import RAGQueryLog
    
    db = SessionLocal()
    
    try:
        # 90일 이상 된 로그 삭제
        cutoff_date = datetime.now() - timedelta(days=90)
        
        deleted = db.query(RAGQueryLog).filter(
            RAGQueryLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted} old query logs")
        
        return {"deleted": deleted}
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()
