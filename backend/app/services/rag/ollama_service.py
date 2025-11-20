"""
LLM 서비스 (Ollama 연동)

로컬 Ollama를 사용하여 답변을 생성합니다.
"""

from typing import List, Optional, AsyncIterator
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class OllamaLLMService:
    """Ollama LLM 서비스"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2:latest"
    ):
        """
        Args:
            base_url: Ollama 서버 URL
            model: 사용할 모델
        """
        self.base_url = base_url
        self.model = model
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """HTTP 클라이언트 초기화"""
        try:
            import httpx
            self.client = httpx.AsyncClient(timeout=120.0)
            logger.info(f"Ollama client initialized: {self.base_url}, model: {self.model}")
        except ImportError:
            logger.warning("httpx not installed. Install: pip install httpx")
            self.client = None
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        답변 생성
        
        Args:
            prompt: 프롬프트
            temperature: 온도 (0.0 ~ 1.0)
            max_tokens: 최대 토큰 수
            
        Returns:
            생성된 답변
        """
        if not self.client:
            logger.warning("Using mock LLM response")
            return self._mock_generate(prompt)
        
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            logger.info(f"Generating with Ollama model: {self.model}")
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "")
            
            logger.info(f"Generated {len(answer)} characters")
            
            return answer
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            # Fallback to mock
            return self._mock_generate(prompt)
    
    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """
        스트리밍 답변 생성
        
        Args:
            prompt: 프롬프트
            temperature: 온도
            max_tokens: 최대 토큰 수
            
        Yields:
            생성된 토큰
        """
        if not self.client:
            yield self._mock_generate(prompt)
            return
        
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            logger.info(f"Streaming with Ollama model: {self.model}")
            
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue
            
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield self._mock_generate(prompt)
    
    async def embed(self, text: str) -> List[float]:
        """
        텍스트 임베딩 (Ollama embeddings API)
        
        Note: Ollama는 일부 모델에서만 임베딩 지원
        """
        if not self.client:
            return self._mock_embedding()
        
        try:
            url = f"{self.base_url}/api/embeddings"
            
            payload = {
                "model": self.model,
                "prompt": text
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                logger.warning("No embedding returned, using mock")
                return self._mock_embedding()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            return self._mock_embedding()
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock 답변 생성"""
        return f"[Mock Ollama Response] 질문에 대한 답변입니다. 프롬프트 길이: {len(prompt)}"
    
    def _mock_embedding(self) -> List[float]:
        """Mock 임베딩"""
        import random
        random.seed(42)
        return [random.random() for _ in range(768)]  # llama2 dimension
    
    async def close(self):
        """클라이언트 종료"""
        if self.client:
            await self.client.aclose()


class OllamaEmbeddingService:
    """Ollama 임베딩 서비스 (임베딩 전용 모델 사용)"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text:latest"  # 임베딩 전용 모델
    ):
        """
        Args:
            base_url: Ollama 서버 URL
            model: 임베딩 모델
        """
        self.base_url = base_url
        self.model = model
        self.dimension = 768  # nomic-embed-text dimension
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """HTTP 클라이언트 초기화"""
        try:
            import httpx
            self.client = httpx.AsyncClient(timeout=60.0)
            logger.info(f"Ollama embedding client initialized: {self.model}")
        except ImportError:
            logger.warning("httpx not installed")
            self.client = None
    
    async def embed(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        if not self.client:
            return self._mock_embedding()
        
        try:
            url = f"{self.base_url}/api/embeddings"
            
            payload = {
                "model": self.model,
                "prompt": text
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            embedding = result.get("embedding", [])
            
            if not embedding:
                logger.warning("No embedding returned, using mock")
                return self._mock_embedding()
            
            logger.debug(f"Generated embedding for text (length: {len(text)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            return self._mock_embedding()
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """배치 임베딩"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Ollama는 배치를 지원하지 않으므로 순차 처리
            for text in batch:
                embedding = await self.embed(text)
                embeddings.append(embedding)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
        
        return embeddings
    
    def _mock_embedding(self) -> List[float]:
        """Mock 임베딩"""
        import random
        random.seed(42)
        return [random.random() for _ in range(self.dimension)]
    
    async def close(self):
        """클라이언트 종료"""
        if self.client:
            await self.client.aclose()
