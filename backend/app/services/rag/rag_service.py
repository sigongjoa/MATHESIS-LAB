"""
RAG 서비스

질의 응답의 핵심 로직을 담당합니다.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
import uuid
import logging
from sqlalchemy.orm import Session

from backend.app.services.rag.vector_store import VectorStore, SearchResult
from backend.app.services.rag.embedding_service import EmbeddingService
from backend.app.models.rag_models import RAGQueryLog

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """RAG 응답"""
    answer: str
    sources: List[SearchResult]
    confidence: float
    processing_time_ms: int
    query_id: str


class RAGService:
    """RAG 서비스"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        db: Session
    ):
        """
        Args:
            vector_store: 벡터 저장소
            embedding_service: 임베딩 서비스
            db: 데이터베이스 세션
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.db = db
    
    async def query(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        user_id: Optional[str] = None
    ) -> RAGResponse:
        """
        RAG 질의 처리
        
        Args:
            query_text: 사용자 질문
            filters: 메타데이터 필터
            top_k: 검색할 청크 수
            user_id: 사용자 ID
            
        Returns:
            RAG 응답
        """
        start_time = time.time()
        query_id = f"q_{uuid.uuid4()}"
        
        try:
            # 1. 질의 임베딩
            embedding_start = time.time()
            query_embedding = await self.embedding_service.embed(query_text)
            embedding_time = int((time.time() - embedding_start) * 1000)
            
            # 2. 벡터 검색
            search_start = time.time()
            search_results = await self.vector_store.search(
                query_vector=query_embedding,
                filters=filters,
                top_k=top_k
            )
            search_time = int((time.time() - search_start) * 1000)
            
            # 3. 재순위화 (선택적)
            reranked_results = await self._rerank(query_text, search_results)
            
            # 4. LLM 프롬프트 구성
            prompt = self._build_prompt(query_text, reranked_results)
            
            # 5. 답변 생성
            llm_start = time.time()
            answer = await self._generate_answer(prompt)
            llm_time = int((time.time() - llm_start) * 1000)
            
            # 6. 인용 추가
            answer_with_citations = self._add_citations(answer, reranked_results)
            
            # 7. 신뢰도 계산
            confidence = self._calculate_confidence(reranked_results)
            
            # 8. 처리 시간 계산
            processing_time = int((time.time() - start_time) * 1000)
            
            # 9. 로그 저장
            if user_id:
                await self._log_query(
                    query_id=query_id,
                    user_id=user_id,
                    query_text=query_text,
                    answer=answer_with_citations,
                    sources=reranked_results,
                    confidence=confidence,
                    processing_time_ms=processing_time,
                    embedding_time_ms=embedding_time,
                    search_time_ms=search_time,
                    llm_time_ms=llm_time
                )
            
            return RAGResponse(
                answer=answer_with_citations,
                sources=reranked_results,
                confidence=confidence,
                processing_time_ms=processing_time,
                query_id=query_id
            )
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            
            # 에러 로그
            if user_id:
                await self._log_error(query_id, user_id, query_text, str(e))
            
            raise
    
    async def _rerank(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        재순위화 (선택적)
        
        현재는 간단히 점수 기준 정렬만 수행
        향후 Cross-Encoder 모델 추가 가능
        """
        # 점수 기준 내림차순 정렬
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Reranked {len(sorted_results)} results")
        return sorted_results
    
    def _build_prompt(
        self,
        query: str,
        sources: List[SearchResult]
    ) -> str:
        """
        LLM 프롬프트 구성
        
        Chain-of-Thought 프롬프팅 적용
        """
        # 출처 포맷팅
        sources_text = ""
        for i, source in enumerate(sources, start=1):
            sources_text += f"\n[출처 {i}] (ID: {source.chunk_id}, 점수: {source.score:.2f})\n"
            sources_text += f"{source.content}\n"
            
            # 메타데이터 추가
            if source.metadata.get("curriculum_code"):
                sources_text += f"성취기준: {source.metadata['curriculum_code']}\n"
            if source.metadata.get("page_number"):
                sources_text += f"페이지: {source.metadata['page_number']}\n"
        
        prompt = f"""당신은 교육과정 전문가입니다. 다음 근거를 바탕으로 질문에 답변하세요.

**중요 규칙:**
1. 제공된 근거에만 기반하여 답변하세요
2. 모든 사실에 대해 <출처: [chunk_id]> 형식으로 인용하세요
3. 근거가 불충분하면 "제공된 문서에는 해당 정보가 없습니다"라고 답하세요
4. 추측하거나 근거 없는 정보를 제공하지 마세요

**근거:**
{sources_text}

**질문:** {query}

**답변:**"""
        
        return prompt
    
    async def _generate_answer(self, prompt: str) -> str:
        """
        LLM 답변 생성 (Ollama 사용)
        """
        try:
            from backend.app.services.rag.ollama_service import OllamaLLMService
            
            # Ollama 클라이언트 생성
            llm = OllamaLLMService()
            
            # 답변 생성
            answer = await llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            await llm.close()
            
            logger.info(f"Generated answer with Ollama ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            
            # Fallback to mock
            logger.warning("Using mock LLM response")
            return "[Mock] 질문에 대한 답변입니다. <출처: mock_chunk_id>"
    
    def _add_citations(
        self,
        answer: str,
        sources: List[SearchResult]
    ) -> str:
        """
        인용 추가
        
        답변에 출처 정보를 명확히 표시
        """
        # 이미 인용이 포함되어 있으면 그대로 반환
        if "<출처:" in answer:
            return answer
        
        # 인용이 없으면 마지막에 추가
        if sources:
            citations = "\n\n**참고 자료:**\n"
            for source in sources[:3]:  # 상위 3개만
                citations += f"- {source.chunk_id}"
                if source.metadata.get("curriculum_code"):
                    citations += f" ({source.metadata['curriculum_code']})"
                citations += f" (유사도: {source.score:.2f})\n"
            
            return answer + citations
        
        return answer
    
    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """
        신뢰도 계산
        
        검색 결과의 점수를 기반으로 신뢰도 산출
        """
        if not results:
            return 0.0
        
        # 상위 결과들의 평균 점수
        top_scores = [r.score for r in results[:3]]
        avg_score = sum(top_scores) / len(top_scores)
        
        # 결과 수에 따른 가중치
        count_weight = min(len(results) / 5, 1.0)
        
        confidence = avg_score * count_weight
        
        return round(confidence, 2)
    
    async def _log_query(
        self,
        query_id: str,
        user_id: str,
        query_text: str,
        answer: str,
        sources: List[SearchResult],
        confidence: float,
        processing_time_ms: int,
        embedding_time_ms: int,
        search_time_ms: int,
        llm_time_ms: int
    ):
        """질의 로그 저장"""
        try:
            # 출처를 JSON으로 변환
            sources_json = [
                {
                    "chunk_id": s.chunk_id,
                    "score": s.score,
                    "metadata": s.metadata
                }
                for s in sources
            ]
            
            log = RAGQueryLog(
                query_id=query_id,
                user_id=user_id,
                query_text=query_text,
                answer=answer,
                sources=sources_json,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                embedding_time_ms=embedding_time_ms,
                search_time_ms=search_time_ms,
                llm_time_ms=llm_time_ms,
                # 토큰 수는 나중에 업데이트
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                estimated_cost_usd=0.0
            )
            
            self.db.add(log)
            self.db.commit()
            
            logger.info(f"Query logged: {query_id}")
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            self.db.rollback()
    
    async def _log_error(
        self,
        query_id: str,
        user_id: str,
        query_text: str,
        error_message: str
    ):
        """에러 로그 저장"""
        try:
            log = RAGQueryLog(
                query_id=query_id,
                user_id=user_id,
                query_text=query_text,
                answer=f"[ERROR] {error_message}",
                sources=[],
                confidence=0.0,
                processing_time_ms=0
            )
            
            self.db.add(log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
            self.db.rollback()
