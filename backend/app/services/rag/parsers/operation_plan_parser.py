import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from .base_parser import BaseParser, ParsedChunk

logger = logging.getLogger(__name__)

class OperationPlanParser(BaseParser):
    """
    교수학습 및 평가 운영 계획 파서
    
    Target: 2025학년도 2학기 3학년 교과별 교수학습 및 평가 운영 계획(수정).hwp
    Strategy: 
    1. HWP -> PDF 변환 (외부 툴 사용 가정)
    2. PDF에서 표(Table) 구조 인식
    3. 행(Row) 단위 청킹: [단원] - [성취기준] - [평가방법] - [시기]
    """
    
    async def parse(self, file_path: Path, base_metadata: Dict[str, Any]) -> List[ParsedChunk]:
        # 1. 파일 형식 확인
        if file_path.suffix.lower() == '.hwp':
            # TODO: 실환경에서는 HWP -> PDF 변환 로직 호출
            # 여기서는 변환되었다고 가정하고, 혹은 텍스트 추출이 되었다고 가정
            logger.warning("HWP file detected. Assuming text extraction or conversion is handled.")
            return self._parse_hwp_text(file_path, base_metadata)
        
        # PDF인 경우
        try:
            import fitz
            doc = fitz.open(file_path)
            # PDF 파싱 로직 (표 처리)
            # ...
            doc.close()
            return [] 
        except ImportError:
            return []

    def _parse_hwp_text(self, file_path: Path, base_metadata: Dict[str, Any]) -> List[ParsedChunk]:
        """
        HWP 파일에서 텍스트를 추출하여 파싱 (olefile 사용)
        """
        chunks = []
        try:
            import olefile
            import zlib
            
            if not olefile.isOleFile(file_path):
                logger.error(f"Not a valid OLE file: {file_path}")
                return []

            ole = olefile.OleFileIO(file_path)
            dirs = ole.listdir()
            
            # BodyText 섹션 찾기 (Section0, Section1, ...)
            body_sections = [d for d in dirs if d[0] == "BodyText"]
            full_text = ""
            
            for section in body_sections:
                stream = ole.openstream(section)
                data = stream.read()
                
                # HWP 5.0은 zlib 압축 사용
                try:
                    decompressed_data = zlib.decompress(data, -15)
                except Exception:
                    # 압축되지 않았거나 다른 방식일 경우
                    decompressed_data = data
                
                # 텍스트 추출 (UTF-16LE)
                # HWP 텍스트는 2바이트 유니코드로 저장됨. 제어 문자 등은 필터링 필요.
                # 간단한 구현: UTF-16LE로 디코딩 후 읽을 수 있는 문자만 추출
                text = decompressed_data.decode('utf-16-le', errors='ignore')
                
                # 정제: 특수문자 및 제어문자 제거
                # 한글, 영문, 숫자, 기본 구두점만 남기기
                # text = re.sub(r'[^가-힣a-zA-Z0-9\s\.\,\-\[\]\(\)]', ' ', text)
                full_text += text + "\n"

            ole.close()
            
            if not full_text.strip():
                logger.warning("Failed to extract text from HWP or empty file.")
                return []

            # 추출된 텍스트를 기반으로 청킹
            # HWP 바이너리 추출 텍스트는 구조가 깨져있을 수 있으므로,
            # 키워드 기반으로 대략적인 구조를 복원하거나 단순 분할
            
            # 1. 단원/성취기준 패턴 찾기
            # 예: "1. 수와 연산" 또는 "[4수01-01]"
            
            # 간단히 500자 단위로 청킹하되, 메타데이터 주입
            text_len = len(full_text)
            chunk_size = 500
            
            for i in range(0, text_len, chunk_size):
                chunk_content = full_text[i:i+chunk_size]
                
                # 내용에서 키워드 추출 시도
                unit_match = re.search(r'\d+\.\s+[가-힣]+', chunk_content)
                unit = unit_match.group(0) if unit_match else "Unknown"
                
                metadata = {
                    **base_metadata,
                    "source_file": file_path.name,
                    "extracted_unit_hint": unit
                }
                
                chunks.append(ParsedChunk(
                    content=chunk_content.strip(),
                    metadata=metadata,
                    chunk_index=len(chunks)
                ))
                
            logger.info(f"Extracted {len(chunks)} chunks from HWP binary stream.")
            return chunks

        except Exception as e:
            logger.error(f"Error parsing HWP file: {e}")
            # Fallback to mock data if extraction fails completely
            return self._get_mock_data(file_path, base_metadata)

    def _get_mock_data(self, file_path: Path, base_metadata: Dict[str, Any]) -> List[ParsedChunk]:
        """테스트용 Mock 데이터 (실패 시 Fallback)"""
        dummy_rows = [
            ("1. 수와 연산", "[4수01-01] 10000 이상의 큰 수...", "지필평가", "3월"),
            ("2. 도형", "[4수02-03] 삼각형의 세 각의 크기...", "관찰평가", "4월"),
        ]
        chunks = []
        for i, (unit, standard, method, date) in enumerate(dummy_rows):
            content = f"단원: {unit}\n성취기준: {standard}\n평가방법: {method}\n시기: {date}"
            metadata = {**base_metadata, "unit": unit, "source_file": file_path.name, "is_mock": True}
            chunks.append(ParsedChunk(content=content, metadata=metadata, chunk_index=i))
        return chunks
