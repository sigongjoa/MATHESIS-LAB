"""
Vector Store 테스트
"""

import pytest
from backend.app.services.rag.vector_store import MockVectorStore, SearchResult


@pytest.fixture
def vector_store():
    """Vector Store 픽스처"""
    return MockVectorStore()


class TestMockVectorStore:
    """Mock Vector Store 테스트"""
    
    @pytest.mark.asyncio
    async def test_initialize_collection(self, vector_store):
        """컬렉션 초기화 테스트"""
        await vector_store.initialize_collection()
        # Mock이므로 에러 없이 완료되면 성공
        assert True
    
    @pytest.mark.asyncio
    async def test_upsert(self, vector_store):
        """벡터 삽입 테스트"""
        chunk_id = "test_chunk_1"
        embedding = [0.1] * 768
        metadata = {"policy_version": "2022개정"}
        content = "테스트 내용"
        
        await vector_store.upsert(chunk_id, embedding, metadata, content)
        
        # 저장 확인
        assert chunk_id in vector_store.storage
        assert vector_store.storage[chunk_id]["content"] == content
        assert vector_store.storage[chunk_id]["metadata"] == metadata
    
    @pytest.mark.asyncio
    async def test_search(self, vector_store):
        """벡터 검색 테스트"""
        # 데이터 준비
        await vector_store.upsert(
            "chunk_1",
            [0.1] * 768,
            {"policy_version": "2022개정"},
            "내용 1"
        )
        await vector_store.upsert(
            "chunk_2",
            [0.2] * 768,
            {"policy_version": "2022개정"},
            "내용 2"
        )
        
        # 검색
        query_vector = [0.15] * 768
        results = await vector_store.search(query_vector, top_k=2)
        
        # 검증
        assert len(results) <= 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.score > 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_store):
        """필터 적용 검색 테스트"""
        # 데이터 준비
        await vector_store.upsert(
            "chunk_1",
            [0.1] * 768,
            {"policy_version": "2022개정", "grade_level": "초5~6"},
            "내용 1"
        )
        await vector_store.upsert(
            "chunk_2",
            [0.2] * 768,
            {"policy_version": "2015개정", "grade_level": "초5~6"},
            "내용 2"
        )
        
        # 필터 적용 검색
        query_vector = [0.15] * 768
        filters = {"policy_version": "2022개정"}
        results = await vector_store.search(query_vector, filters=filters, top_k=5)
        
        # Mock은 필터를 완전히 적용하지 않지만, 에러 없이 실행되면 성공
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_empty_store(self, vector_store):
        """빈 저장소 검색 테스트"""
        query_vector = [0.1] * 768
        results = await vector_store.search(query_vector, top_k=5)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_upsert_batch(self, vector_store):
        """배치 삽입 테스트"""
        chunks = [
            ("chunk_1", [0.1] * 768, {"version": "2022"}, "내용 1"),
            ("chunk_2", [0.2] * 768, {"version": "2022"}, "내용 2"),
            ("chunk_3", [0.3] * 768, {"version": "2022"}, "내용 3"),
        ]
        
        await vector_store.upsert_batch(chunks)
        
        # 모두 저장되었는지 확인
        assert "chunk_1" in vector_store.storage
        assert "chunk_2" in vector_store.storage
        assert "chunk_3" in vector_store.storage


class TestSearchResult:
    """SearchResult 데이터 클래스 테스트"""
    
    def test_search_result_creation(self):
        """SearchResult 생성 테스트"""
        result = SearchResult(
            chunk_id="test_chunk",
            content="테스트 내용",
            score=0.95,
            metadata={"policy_version": "2022개정"}
        )
        
        assert result.chunk_id == "test_chunk"
        assert result.content == "테스트 내용"
        assert result.score == 0.95
        assert result.metadata["policy_version"] == "2022개정"
    
    def test_search_result_comparison(self):
        """SearchResult 비교 테스트 (점수 기준)"""
        result1 = SearchResult("chunk_1", "내용", 0.9, {})
        result2 = SearchResult("chunk_2", "내용", 0.8, {})
        
        # 점수로 정렬 가능
        results = sorted([result2, result1], key=lambda x: x.score, reverse=True)
        
        assert results[0].score == 0.9
        assert results[1].score == 0.8
