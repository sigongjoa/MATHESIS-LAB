"""
문서 파싱 서비스

PDF 및 HWP 문서를 구조적으로 파싱하고 청크를 생성합니다.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .parsers.base_parser import ParsedChunk
from .parsers.math_parser import MathParser
from .parsers.operation_plan_parser import OperationPlanParser

logger = logging.getLogger(__name__)

class ParserService:
    """문서 파싱 서비스"""
    
    def __init__(self):
        self.math_parser = MathParser()
        self.plan_parser = OperationPlanParser()
    
    async def parse_document(
        self,
        file_path: Path,
        document_type: str,
        metadata: Dict[str, Any]
    ) -> List[ParsedChunk]:
        """
        문서 파싱
        
        Args:
            file_path: 문서 파일 경로
            document_type: 문서 유형 ('curriculum', 'school_plan')
            metadata: 기본 메타데이터
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Parsing document: {file_path.name} (Type: {document_type})")
        
        # 문서 유형에 따른 파서 선택
        if document_type == 'curriculum':
            # 수학과 교육과정 (PDF)
            return await self.math_parser.parse(file_path, metadata)
        
        elif document_type == 'school_plan':
            # 학교 운영 계획 (HWP -> PDF)
            return await self.plan_parser.parse(file_path, metadata)
            
        else:
            # 기본 파서 (기존 로직 유지 또는 Fallback)
            logger.warning(f"Unknown document type '{document_type}', using default PDF parser")
            return await self.math_parser.parse(file_path, metadata)

    def validate_chunk(self, chunk: ParsedChunk) -> bool:
        """청크 유효성 검증"""
        if not chunk.content:
            return False
        return True
