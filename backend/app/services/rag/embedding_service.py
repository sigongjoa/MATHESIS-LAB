"""
임베딩 서비스

OpenAI 또는 Ollama를 사용하여 텍스트를 벡터로 변환합니다.
"""

from typing import List, Optional
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """임베딩 서비스 (OpenAI 또는 Ollama)"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-large",
        use_ollama: bool = True  # Ollama 우선 사용
    ):
        """
        Args:
            api_key: OpenAI API 키
            model: 임베딩 모델
            use_ollama: Ollama 사용 여부
        """
        self.api_key = api_key
        self.model = model
        self.use_ollama = use_ollama
        self.dimension = 768 if use_ollama else 3072  # Ollama: 768, OpenAI: 3072
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """클라이언트 초기화"""
        if self.use_ollama:
            try:
                from backend.app.services.rag.ollama_service import OllamaEmbeddingService
                self.client = OllamaEmbeddingService()
                logger.info("Ollama embedding client initialized")
            except Exception as e:
                logger.warning(f"Ollama initialization failed: {e}, falling back to OpenAI")
                self.use_ollama = False
        
        if not self.use_ollama:
            try:
                import openai
                
                if self.api_key:
                    self.client = openai.OpenAI(api_key=self.api_key)
                    logger.info(f"OpenAI client initialized with model: {self.model}")
                else:
                    logger.warning("No API key provided. Using mock embeddings.")
                    self.client = None
                    
            except ImportError:
                logger.warning("openai package not installed. Using mock embeddings.")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        단일 텍스트 임베딩 (Alias for embed)
        """
        return await self.embed(text)

    async def embed(self, text: str) -> List[float]:
        """
        단일 텍스트 임베딩
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터
        """
        if not self.client:
            return self._mock_embedding()
        
        try:
            if self.use_ollama:
                # Ollama 임베딩
                embedding = await self.client.embed(text)
                logger.debug(f"Generated Ollama embedding for text (length: {len(text)})")
                return embedding
            else:
                # OpenAI 임베딩
                response = await asyncio.to_thread(
                    self.client.embeddings.create,
                    model=self.model,
                    input=text
                )
                
                embedding = response.data[0].embedding
                logger.debug(f"Generated OpenAI embedding for text (length: {len(text)})")
                return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Fallback to mock
            return self._mock_embedding()
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        배치 임베딩
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        if not self.client:
            return [self._mock_embedding() for _ in texts]
        
        try:
            if self.use_ollama:
                # Ollama 배치 임베딩
                embeddings = await self.client.embed_batch(texts, batch_size=10)
                return embeddings
            else:
                # OpenAI 배치 임베딩
                embeddings = []
                
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    
                    response = await asyncio.to_thread(
                        self.client.embeddings.create,
                        model=self.model,
                        input=batch
                    )
                    
                    batch_embeddings = [data.embedding for data in response.data]
                    embeddings.extend(batch_embeddings)
                    
                    logger.info(f"Generated {len(batch_embeddings)} embeddings (batch {i//batch_size + 1})")
                
                return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            # Fallback to mock
            return [self._mock_embedding() for _ in texts]
    
    def _mock_embedding(self) -> List[float]:
        """Mock 임베딩 (테스트용)"""
        import random
        random.seed(42)
        return [random.random() for _ in range(self.dimension)]


class MockEmbeddingService(EmbeddingService):
    """Mock 임베딩 서비스 (테스트용)"""
    
    def __init__(self):
        """Mock 초기화"""
        self.api_key = None
        self.model = "mock-embedding"
        self.dimension = 768
        self.client = None
        self.use_ollama = False
    
    async def embed(self, text: str) -> List[float]:
        """Mock 임베딩"""
        return self._mock_embedding()
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Mock 배치 임베딩"""
        return [self._mock_embedding() for _ in texts]
