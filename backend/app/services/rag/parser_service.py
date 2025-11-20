"""
문서 파싱 서비스

PDF 및 HWP 문서를 구조적으로 파싱하고 청크를 생성합니다.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedChunk:
    """파싱된 청크"""
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    chunk_index: int = 0


class ParserService:
    """문서 파싱 서비스"""
    
    def __init__(self):
        self.chunk_size = 1000  # 기본 청크 크기
        self.chunk_overlap = 200  # 청크 간 오버랩
    
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
            
        Returns:
            ParsedChunk 리스트
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            ValueError: 지원하지 않는 파일 형식
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 파일 확장자에 따라 파서 선택
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return await self._parse_pdf(file_path, metadata)
        elif suffix == '.hwp':
            return await self._parse_hwp(file_path, metadata)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    async def _parse_pdf(
        self,
        file_path: Path,
        base_metadata: Dict[str, Any]
    ) -> List[ParsedChunk]:
        """PDF 파싱"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF not installed. Install: pip install PyMuPDF")
            # Fallback: 간단한 텍스트 추출
            return await self._parse_pdf_fallback(file_path, base_metadata)
        
        chunks = []
        doc = fitz.open(file_path)
        
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            
            # 성취기준 코드 패턴 감지
            achievement_codes = re.findall(r'\[(\d+[가-힣]+\d+-\d+)\]', text)
            
            if achievement_codes:
                # 성취기준 단위로 청킹
                for code in achievement_codes:
                    chunk_content = self._extract_achievement_section(text, code)
                    if chunk_content:
                        metadata = {
                            **base_metadata,
                            "document_type": "성취기준",
                            "curriculum_code": f"[{code}]",
                            "page_number": page_num
                        }
                        chunks.append(ParsedChunk(
                            content=chunk_content,
                            metadata=metadata,
                            page_number=page_num,
                            chunk_index=len(chunks)
                        ))
            else:
                # 일반 텍스트 청킹
                text_chunks = self._chunk_text(text)
                for i, chunk_text in enumerate(text_chunks):
                    metadata = {
                        **base_metadata,
                        "document_type": "일반",
                        "page_number": page_num
                    }
                    chunks.append(ParsedChunk(
                        content=chunk_text,
                        metadata=metadata,
                        page_number=page_num,
                        chunk_index=len(chunks)
                    ))
        
        doc.close()
        return chunks
    
    async def _parse_pdf_fallback(
        self,
        file_path: Path,
        base_metadata: Dict[str, Any]
    ) -> List[ParsedChunk]:
        """PDF Fallback 파서 (PyMuPDF 없을 때)"""
        # 간단한 구현: 파일을 읽고 청크로 나눔
        logger.warning("Using fallback PDF parser")
        
        # TODO: pdfplumber 또는 다른 라이브러리 사용
        chunks = []
        dummy_text = f"[Fallback] PDF content from {file_path.name}"
        
        metadata = {
            **base_metadata,
            "document_type": "일반",
            "page_number": 1
        }
        
        chunks.append(ParsedChunk(
            content=dummy_text,
            metadata=metadata,
            page_number=1,
            chunk_index=0
        ))
        
        return chunks
    
    async def _parse_hwp(
        self,
        file_path: Path,
        base_metadata: Dict[str, Any]
    ) -> List[ParsedChunk]:
        """HWP 파싱"""
        try:
            import olefile
        except ImportError:
            logger.error("olefile not installed. Install: pip install olefile")
            return await self._parse_hwp_fallback(file_path, base_metadata)
        
        # HWP 파일은 OLE 구조
        # 간단한 텍스트 추출
        chunks = []
        
        try:
            # HWP 파일 읽기 (간단한 구현)
            # 실제로는 hwp5 라이브러리 사용 권장
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 텍스트 추출 (간단한 방법)
            text = self._extract_text_from_hwp(content)
            
            # 섹션 단위로 청킹
            sections = self._split_by_sections(text)
            
            for i, (section_title, section_content) in enumerate(sections):
                metadata = {
                    **base_metadata,
                    "document_type": self._classify_section(section_title),
                    "section_title": section_title
                }
                chunks.append(ParsedChunk(
                    content=section_content,
                    metadata=metadata,
                    chunk_index=i
                ))
            
        except Exception as e:
            logger.error(f"HWP parsing error: {e}")
            return await self._parse_hwp_fallback(file_path, base_metadata)
        
        return chunks
    
    async def _parse_hwp_fallback(
        self,
        file_path: Path,
        base_metadata: Dict[str, Any]
    ) -> List[ParsedChunk]:
        """HWP Fallback 파서"""
        logger.warning("Using fallback HWP parser")
        
        chunks = []
        dummy_text = f"[Fallback] HWP content from {file_path.name}"
        
        metadata = {
            **base_metadata,
            "document_type": "일반"
        }
        
        chunks.append(ParsedChunk(
            content=dummy_text,
            metadata=metadata,
            chunk_index=0
        ))
        
        return chunks
    
    def _extract_achievement_section(self, text: str, code: str) -> str:
        """성취기준 섹션 추출"""
        # 성취기준 코드를 기준으로 섹션 추출
        pattern = rf'\[{re.escape(code)}\](.*?)(?=\[\d+[가-힣]+\d+-\d+\]|$)'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _chunk_text(self, text: str) -> List[str]:
        """텍스트를 청크로 분할"""
        chunks = []
        
        # 문장 단위로 분할
        sentences = re.split(r'[.!?]\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_text_from_hwp(self, content: bytes) -> str:
        """HWP에서 텍스트 추출 (간단한 구현)"""
        # 실제로는 hwp5 라이브러리 사용 권장
        # 여기서는 간단히 디코딩 시도
        try:
            return content.decode('utf-8', errors='ignore')
        except:
            return content.decode('cp949', errors='ignore')
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """섹션 단위로 분할"""
        # 간단한 구현: 제목 패턴으로 분할
        sections = []
        
        # 제목 패턴 (예: "1. 제목", "가. 제목")
        pattern = r'(?:^|\n)([가-힣0-9]+\.\s+[^\n]+)'
        
        parts = re.split(pattern, text)
        
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                title = parts[i].strip()
                content = parts[i + 1].strip()
                sections.append((title, content))
        
        if not sections:
            # 분할 실패 시 전체를 하나의 섹션으로
            sections.append(("전체", text))
        
        return sections
    
    def _classify_section(self, title: str) -> str:
        """섹션 제목으로 문서 유형 분류"""
        title_lower = title.lower()
        
        if '평가' in title_lower:
            return '평가계획'
        elif '수업' in title_lower or '교수' in title_lower:
            return '수업운영'
        elif '목표' in title_lower:
            return '교육목표'
        else:
            return '일반'
    
    def validate_chunk(self, chunk: ParsedChunk) -> bool:
        """청크 유효성 검증"""
        # 필수 메타데이터 확인
        required_fields = ['policy_version', 'scope_type']
        
        for field in required_fields:
            if field not in chunk.metadata:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # 내용 확인
        if not chunk.content or len(chunk.content) < 10:
            logger.warning("Chunk content too short")
            return False
        
        return True
    
    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """내용 해시 계산"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
