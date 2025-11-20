"""
Embedding Service 테스트
"""

import pytest
from backend.app.services.rag.embedding_service import EmbeddingService, MockEmbeddingService


@pytest.fixture
def mock_embedding_service():
    """Mock Embedding Service 픽스처"""
    return MockEmbeddingService()


@pytest.fixture
def embedding_service():
    """Embedding Service 픽스처 (Ollama 사용)"""
    return EmbeddingService(use_ollama=True)


class TestMockEmbeddingService:
    """Mock Embedding Service 테스트"""
    
    @pytest.mark.asyncio
    async def test_embed(self, mock_embedding_service):
        """단일 임베딩 테스트"""
        text = "테스트 텍스트"
        embedding = await mock_embedding_service.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768  # Mock dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_embed_batch(self, mock_embedding_service):
        """배치 임베딩 테스트"""
        texts = ["텍스트 1", "텍스트 2", "텍스트 3"]
        embeddings = await mock_embedding_service.embed_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_embed_empty_text(self, mock_embedding_service):
        """빈 텍스트 임베딩 테스트"""
        embedding = await mock_embedding_service.embed("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
    
    @pytest.mark.asyncio
    async def test_embed_long_text(self, mock_embedding_service):
        """긴 텍스트 임베딩 테스트"""
        long_text = "테스트 " * 1000
        embedding = await mock_embedding_service.embed(long_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768


class TestEmbeddingService:
    """Embedding Service 테스트"""
    
    def test_initialization_ollama(self):
        """Ollama 초기화 테스트"""
        service = EmbeddingService(use_ollama=True)
        
        assert service.use_ollama is True
        assert service.dimension == 768
    
    def test_initialization_openai(self):
        """OpenAI 초기화 테스트"""
        service = EmbeddingService(
            api_key="test_key",
            use_ollama=False
        )
        
        # API 키가 있어도 실제 연결은 안 되므로 client는 None일 수 있음
        assert service.use_ollama is False
        assert service.dimension == 3072
    
    @pytest.mark.asyncio
    async def test_embed_with_ollama(self, embedding_service):
        """Ollama 임베딩 테스트"""
        text = "테스트 텍스트"
        embedding = await embedding_service.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
    
    @pytest.mark.asyncio
    async def test_embed_batch_with_ollama(self, embedding_service):
        """Ollama 배치 임베딩 테스트"""
        texts = ["텍스트 1", "텍스트 2"]
        embeddings = await embedding_service.embed_batch(texts, batch_size=10)
        
        assert len(embeddings) == 2
        assert all(isinstance(emb, list) for emb in embeddings)
    
    def test_mock_embedding_consistency(self, mock_embedding_service):
        """Mock 임베딩 일관성 테스트"""
        emb1 = mock_embedding_service._mock_embedding()
        emb2 = mock_embedding_service._mock_embedding()
        
        # 같은 seed를 사용하므로 같은 결과
        assert emb1 == emb2


class TestEmbeddingServiceEdgeCases:
    """Embedding Service 엣지 케이스 테스트"""
    
    @pytest.mark.asyncio
    async def test_embed_special_characters(self, mock_embedding_service):
        """특수 문자 임베딩 테스트"""
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        embedding = await mock_embedding_service.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
    
    @pytest.mark.asyncio
    async def test_embed_korean_text(self, mock_embedding_service):
        """한국어 텍스트 임베딩 테스트"""
        text = "안녕하세요. 이것은 한국어 테스트입니다."
        embedding = await mock_embedding_service.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
    
    @pytest.mark.asyncio
    async def test_embed_mixed_language(self, mock_embedding_service):
        """혼합 언어 임베딩 테스트"""
        text = "Hello 안녕 こんにちは 你好"
        embedding = await mock_embedding_service.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
    
    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self, mock_embedding_service):
        """빈 리스트 배치 임베딩 테스트"""
        embeddings = await mock_embedding_service.embed_batch([])
        
        assert embeddings == []
    
    @pytest.mark.asyncio
    async def test_embed_batch_large(self, mock_embedding_service):
        """대량 배치 임베딩 테스트"""
        texts = [f"텍스트 {i}" for i in range(100)]
        embeddings = await mock_embedding_service.embed_batch(texts, batch_size=10)
        
        assert len(embeddings) == 100
        assert all(len(emb) == 768 for emb in embeddings)
