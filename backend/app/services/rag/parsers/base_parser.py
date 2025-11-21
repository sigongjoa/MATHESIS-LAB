from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ParsedChunk:
    """파싱된 청크 데이터 클래스"""
    content: str
    metadata: Dict[str, Any]
    page_number: int = 0
    chunk_index: int = 0

class BaseParser(ABC):
    """기본 파서 추상 클래스"""
    
    @abstractmethod
    async def parse(self, file_path: Path, metadata: Dict[str, Any]) -> List[ParsedChunk]:
        """문서를 파싱하여 청크 리스트를 반환"""
        pass
