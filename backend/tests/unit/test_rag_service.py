"""
RAG Service 통합 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from backend.app.services.rag.rag_service import RAGService
from backend.app.services.rag.vector_store import MockVectorStore, SearchResult
from backend.app.services.rag.embedding_service import MockEmbeddingService


@pytest.fixture
def mock_db():
    """Mock 데이터베이스 세션"""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db


@pytest.fixture
def mock_vector_store():
    """Mock 벡터 저장소"""
    return MockVectorStore()


@pytest.fixture
def mock_embedding_service():
    """Mock 임베딩 서비스"""
    return MockEmbeddingService()


@pytest.fixture
def rag_service(mock_vector_store, mock_embedding_service, mock_db):
    """RAG 서비스 픽스처"""
    return RAGService(
        vector_store=mock_vector_store,
        embedding_service=mock_embedding_service,
        db=mock_db
    )


class TestRAGService:
    """RAG Service 테스트"""
    
    @pytest.mark.asyncio
    async def test_query_basic(self, rag_service):
        """기본 질의 테스트"""
        response = await rag_service.query(
            query_text="테스트 질문",
            filters={"policy_version": "2022개정"},
            top_k=5,
            user_id="test_user"
        )
        
        assert response is not None
        assert response.answer is not None
        assert isinstance(response.answer, str)
        assert response.query_id is not None
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_query_with_sources(self, rag_service, mock_vector_store):
        """출처가 포함된 질의 테스트"""
        # Mock 검색 결과 설정
        mock_vector_store.storage = {
            "chunk_1": {
                "embedding": [0.1] * 768,
                "metadata": {"policy_version": "2022개정"},
                "content": "테스트 내용 1"
            },
            "chunk_2": {
                "embedding": [0.2] * 768,
                "metadata": {"policy_version": "2022개정"},
                "content": "테스트 내용 2"
            }
        }
        
        response = await rag_service.query(
            query_text="테스트 질문",
            filters={"policy_version": "2022개정"},
            top_k=5,
            user_id="test_user"
        )
        
        assert len(response.sources) > 0
        assert all(isinstance(s, SearchResult) for s in response.sources)
    
    @pytest.mark.asyncio
    async def test_query_confidence_calculation(self, rag_service):
        """신뢰도 계산 테스트"""
        response = await rag_service.query(
            query_text="테스트 질문",
            top_k=5,
            user_id="test_user"
        )
        
        assert 0.0 <= response.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_rerank(self, rag_service):
        """재순위화 테스트"""
        results = [
            SearchResult("chunk_1", "내용1", 0.5, {}),
            SearchResult("chunk_2", "내용2", 0.9, {}),
            SearchResult("chunk_3", "내용3", 0.7, {})
        ]
        
        reranked = await rag_service._rerank("질문", results)
        
        # 점수 기준 내림차순 정렬 확인
        assert reranked[0].score >= reranked[1].score
        assert reranked[1].score >= reranked[2].score
    
    def test_build_prompt(self, rag_service):
        """프롬프트 구성 테스트"""
        sources = [
            SearchResult(
                "chunk_1",
                "최대공약수는 약수를 나열하여 구합니다.",
                0.9,
                {"curriculum_code": "[6수01-05]", "page_number": 42}
            )
        ]
        
        prompt = rag_service._build_prompt("최대공약수 구하는 방법", sources)
        
        assert "최대공약수 구하는 방법" in prompt
        assert "최대공약수는 약수를 나열하여 구합니다" in prompt
        assert "[6수01-05]" in prompt
        assert "페이지: 42" in prompt
    
    def test_add_citations(self, rag_service):
        """인용 추가 테스트"""
        answer = "최대공약수는 약수를 나열하여 구합니다."
        sources = [
            SearchResult("chunk_1", "내용", 0.9, {"curriculum_code": "[6수01-05]"})
        ]
        
        answer_with_citations = rag_service._add_citations(answer, sources)
        
        # 인용이 추가되었는지 확인
        assert "chunk_1" in answer_with_citations or "참고 자료" in answer_with_citations
    
    def test_calculate_confidence_with_results(self, rag_service):
        """검색 결과가 있을 때 신뢰도 계산"""
        results = [
            SearchResult("chunk_1", "내용", 0.9, {}),
            SearchResult("chunk_2", "내용", 0.8, {}),
            SearchResult("chunk_3", "내용", 0.7, {})
        ]
        
        confidence = rag_service._calculate_confidence(results)
        
        assert confidence > 0.0
        assert confidence <= 1.0
    
    def test_calculate_confidence_no_results(self, rag_service):
        """검색 결과가 없을 때 신뢰도"""
        confidence = rag_service._calculate_confidence([])
        
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_query_error_handling(self, rag_service, mock_embedding_service):
        """에러 처리 테스트"""
        # 임베딩 실패 시뮬레이션
        mock_embedding_service.embed = AsyncMock(side_effect=Exception("Embedding failed"))
        
        with pytest.raises(Exception):
            await rag_service.query(
                query_text="테스트 질문",
                user_id="test_user"
            )


class TestRAGServiceIntegration:
    """RAG Service 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, rag_service, mock_vector_store):
        """전체 파이프라인 테스트"""
        # 1. 데이터 준비
        mock_vector_store.storage = {
            "chunk_1": {
                "embedding": [0.1] * 768,
                "metadata": {
                    "policy_version": "2022개정",
                    "curriculum_code": "[6수01-05]"
                },
                "content": "최대공약수와 최소공배수는 약수와 배수를 나열하여 구합니다."
            }
        }
        
        # 2. 질의 실행
        response = await rag_service.query(
            query_text="최대공약수는 어떻게 구하나요?",
            filters={"policy_version": "2022개정"},
            top_k=5,
            user_id="test_user"
        )
        
        # 3. 검증
        assert response.answer is not None
        assert len(response.sources) > 0
        assert response.confidence > 0.0
        assert response.processing_time_ms > 0
        assert response.query_id is not None
    
    @pytest.mark.asyncio
    async def test_query_with_filters(self, rag_service):
        """필터 적용 질의 테스트"""
        filters = {
            "policy_version": "2022개정",
            "scope_type": "NATIONAL",
            "grade_level": "초5~6"
        }
        
        response = await rag_service.query(
            query_text="테스트 질문",
            filters=filters,
            top_k=3,
            user_id="test_user"
        )
        
        assert response is not None
        assert response.query_id is not None
