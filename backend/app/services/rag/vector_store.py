"""
벡터 저장소 서비스

Qdrant와의 통신 및 벡터 검색을 담당합니다.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과"""
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """벡터 저장소 래퍼"""
    
    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None):
        """
        Args:
            url: Qdrant 서버 URL
            api_key: API 키 (선택)
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = "rag_chunks"
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Qdrant 클라이언트 초기화"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Docker 서버 대신 로컬 디스크 저장소 사용 (Embedded Mode)
            # url 파라미터가 있으면 서버 모드, path 파라미터가 있으면 로컬 모드
            
            # 우선순위: 
            # 1. 명시적인 URL이 있고 localhost가 아니면 서버 모드 (Cloud 등)
            # 2. 그 외에는 로컬 디스크 모드 (Docker 불필요)
            
            if self.url and "localhost" not in self.url and "127.0.0.1" not in self.url:
                self.client = QdrantClient(url=self.url, api_key=self.api_key)
                logger.info(f"Qdrant client initialized (Server Mode): {self.url}")
            else:
                # 로컬 저장소 경로 설정
                storage_path = "./qdrant_local_storage"
                self.client = QdrantClient(path=storage_path)
                logger.info(f"Qdrant client initialized (Local Disk Mode): {storage_path}")
            
        except ImportError:
            logger.warning("qdrant-client not installed. Using mock vector store.")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            self.client = None
    
    async def initialize_collection(self):
        """컬렉션 초기화"""
        if not self.client:
            logger.warning("Qdrant client not available")
            return
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            # 컬렉션 존재 확인
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # 컬렉션 생성
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # Ollama nomic-embed-text dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection created: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    async def upsert(
        self,
        chunk_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        content: str
    ):
        """
        벡터 삽입/업데이트
        
        Args:
            chunk_id: 청크 ID
            embedding: 임베딩 벡터
            metadata: 메타데이터
            content: 원본 내용
        """
        if not self.client:
            logger.warning("Qdrant client not available, skipping upsert")
            return
        
        try:
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "content": content,
                    **metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Upserted chunk: {chunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to upsert chunk {chunk_id}: {e}")
            raise
    
    async def upsert_batch(
        self,
        chunks: List[tuple]  # [(chunk_id, embedding, metadata, content), ...]
    ):
        """배치 삽입"""
        if not self.client:
            logger.warning("Qdrant client not available, skipping batch upsert")
            return
        
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for chunk_id, embedding, metadata, content in chunks:
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "content": content,
                        **metadata
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Batch upserted {len(points)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to batch upsert: {e}")
            raise
    
    async def search(
        self,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        벡터 검색
        
        Args:
            query_vector: 질의 벡터
            filters: 메타데이터 필터
            top_k: 결과 수
            
        Returns:
            SearchResult 리스트
        """
        if not self.client:
            logger.warning("Qdrant client not available, returning empty results")
            return []
        
        try:
            # 메타데이터 필터 구성
            qdrant_filter = self._build_filter(filters) if filters else None
            
            # Debug: Check client methods
            # logger.info(f"Client type: {type(self.client)}")
            # logger.info(f"Client dir: {dir(self.client)}")
            
            # 'search' 메서드가 없는 경우를 대비해 query_points 사용
            # QdrantClient v1.10+ 에서는 query_points가 더 안정적일 수 있음
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=top_k
            )
            
            results = response.points
            
            search_results = []
            for r in results:
                search_results.append(SearchResult(
                    chunk_id=str(r.id),
                    content=r.payload.get("content", ""),
                    score=r.score,
                    metadata=r.payload
                ))
            
            logger.info(f"Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def _build_filter(self, filters: Dict[str, Any]):
        """메타데이터 필터 구성"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            conditions = []
            for key, value in filters.items():
                if value is not None:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
            
            if conditions:
                return Filter(must=conditions)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to build filter: {e}")
            return None
    
    async def delete(self, chunk_id: str):
        """청크 삭제"""
        if not self.client:
            return
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[chunk_id]
            )
            logger.debug(f"Deleted chunk: {chunk_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete chunk {chunk_id}: {e}")
            raise
    
    async def delete_by_metadata(self, filters: Dict[str, Any]):
        """메타데이터로 청크 삭제"""
        if not self.client:
            return
        
        try:
            qdrant_filter = self._build_filter(filters)
            
            if qdrant_filter:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=qdrant_filter
                )
                logger.info(f"Deleted chunks with filters: {filters}")
                
        except Exception as e:
            logger.error(f"Failed to delete by metadata: {e}")
            raise


class MockVectorStore(VectorStore):
    """Mock 벡터 저장소 (테스트용)"""
    
    def __init__(self):
        """Mock 초기화"""
        self.url = "mock://"
        self.api_key = None
        self.collection_name = "mock_collection"
        self.client = None
        self.storage = {}  # In-memory storage
    
    async def initialize_collection(self):
        """Mock 컬렉션 초기화"""
        logger.info("Mock collection initialized")
    
    async def upsert(self, chunk_id: str, embedding: List[float], metadata: Dict[str, Any], content: str):
        """Mock upsert"""
        self.storage[chunk_id] = {
            "embedding": embedding,
            "metadata": metadata,
            "content": content
        }
        logger.debug(f"Mock upserted: {chunk_id}")
    
    async def search(
        self,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """Mock 검색"""
        # 간단한 랜덤 결과 반환
        results = []
        for chunk_id, data in list(self.storage.items())[:top_k]:
            results.append(SearchResult(
                chunk_id=chunk_id,
                content=data["content"],
                score=0.85,
                metadata=data["metadata"]
            ))
        
        logger.info(f"Mock search returned {len(results)} results")
        return results
