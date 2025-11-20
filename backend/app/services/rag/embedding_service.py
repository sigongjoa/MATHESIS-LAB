"""
임베딩 서비스

OpenAI API를 사용하여 텍스트를 벡터로 변환합니다.
"""

from typing import List, Optional
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingService:
    """임베딩 서비스"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-large"):
        """
        Args:
            api_key: OpenAI API 키
            model: 임베딩 모델
        """
        self.api_key = api_key
        self.model = model
        self.dimension = 3072  # text-embedding-3-large
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
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
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            
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
        배치 임베딩 (비용 최적화)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            임베딩 벡터 리스트
        """
        if not self.client:
            return [self._mock_embedding() for _ in texts]
        
        embeddings = []
        
        try:
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
    
    @lru_cache(maxsize=1000)
    def embed_cached(self, text: str) -> tuple:
        """
        캐싱된 임베딩 (자주 사용되는 질의용)
        
        Note: lru_cache는 동기 함수만 지원하므로 tuple로 반환
        """
        if not self.client:
            return tuple(self._mock_embedding())
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            return tuple(embedding)
            
        except Exception as e:
            logger.error(f"Cached embedding failed: {e}")
            return tuple(self._mock_embedding())
    
    def _mock_embedding(self) -> List[float]:
        """Mock 임베딩 (테스트용)"""
        import random
        random.seed(42)
        return [random.random() for _ in range(self.dimension)]
    
    def calculate_tokens(self, text: str) -> int:
        """
        토큰 수 계산 (비용 추정용)
        
        간단한 추정: 1 token ≈ 4 characters (영어 기준)
        한국어는 더 많을 수 있음
        """
        return len(text) // 3  # 한국어 기준 보수적 추정
    
    def estimate_cost(self, texts: List[str]) -> float:
        """
        비용 추정
        
        text-embedding-3-large: $0.00013 per 1K tokens
        """
        total_tokens = sum(self.calculate_tokens(text) for text in texts)
        cost_per_1k_tokens = 0.00013
        
        return (total_tokens / 1000) * cost_per_1k_tokens


class MockEmbeddingService(EmbeddingService):
    """Mock 임베딩 서비스 (테스트용)"""
    
    def __init__(self):
        """Mock 초기화"""
        self.api_key = None
        self.model = "mock-embedding"
        self.dimension = 3072
        self.client = None
    
    async def embed(self, text: str) -> List[float]:
        """Mock 임베딩"""
        return self._mock_embedding()
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Mock 배치 임베딩"""
        return [self._mock_embedding() for _ in texts]
