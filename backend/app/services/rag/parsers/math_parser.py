import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser, ParsedChunk

logger = logging.getLogger(__name__)

class MathParser(BaseParser):
    """
    수학과 교육과정 PDF 파서
    
    Spec: docs/rag/MATH_CURRICULUM_PARSING_SPEC.md
    """
    
    def __init__(self):
        self.school_level_pattern = re.compile(r'^(초등학교|중학교|고등학교)\s+교육과정')
        self.grade_cluster_pattern = re.compile(r'(\d)[~∼](\d)학년군')
        # [2수01-01] or [12수학Ⅰ01-01]
        self.code_pattern = re.compile(r'\[([0-9]+[가-힣a-zA-Z0-9]+-[0-9]+)\]')
        
        # Context state
        self.current_school_level = "Unknown"
        self.current_grade_cluster = "Unknown"
        self.current_domain = "Unknown"

    async def parse(self, file_path: Path, base_metadata: Dict[str, Any]) -> List[ParsedChunk]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF (fitz) is not installed.")
            return []

        doc = fitz.open(file_path)
        chunks = []
        
        # 전체 텍스트를 순회하며 Context 파악 및 청킹
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            lines = text.split('\n')
            
            # 페이지 단위로 일반 섹션(총론 등) 감지
            # 간단한 로직: 성취기준 코드가 없는 페이지이고, 주요 헤더가 포함된 경우
            has_code = self.code_pattern.search(text)
            if not has_code:
                # 주요 헤더 감지 (예: 1. 성격, 2. 목표)
                header_match = re.search(r'^\d+\.\s+(성격|목표|방향|구성)', text, re.MULTILINE)
                if header_match:
                    section_title = header_match.group(0)
                    metadata = {
                        **base_metadata,
                        "school_level": self.current_school_level,
                        "grade_cluster": self.current_grade_cluster,
                        "domain": "총론/일반",
                        "section_title": section_title,
                        "source_file": file_path.name
                    }
                    chunks.append(ParsedChunk(
                        content=text.strip(), # 페이지 전체를 하나의 청크로 (일반 섹션은 보통 페이지 단위 의미)
                        metadata=metadata,
                        page_number=page_num,
                        chunk_index=len(chunks)
                    ))
                    continue # 코드가 없으므로 다음 페이지로

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 1. Context Update
                self._update_context(line)
                
                # 2. Code Detection & Chunking
                codes = self.code_pattern.findall(line)
                if codes:
                    for code in codes:
                        # 해당 코드가 포함된 섹션(문맥) 추출
                        # 여기서는 간단히 해당 라인과 주변 텍스트를 청크로 간주하거나
                        # 더 정교하게 "다음 코드가 나올 때까지"를 캡처해야 함.
                        # 현재 구현은 "Line-based"로 시작하고, 향후 "Section-based"로 고도화
                        
                        # TODO: 실제 구현에서는 이 라인부터 다음 코드 전까지의 텍스트를 긁어모아야 함.
                        # 이번 스텝에서는 "Code Detection"과 "Metadata Injection"에 집중.
                        
                        chunk_content = self._extract_content_for_code(text, code)
                        
                        metadata = {
                            **base_metadata,
                            "school_level": self.current_school_level,
                            "grade_cluster": self.current_grade_cluster,
                            "domain": self.current_domain,
                            "achievement_code": f"[{code}]",
                            "source_file": file_path.name
                        }
                        
                        chunks.append(ParsedChunk(
                            content=chunk_content,
                            metadata=metadata,
                            page_number=page_num,
                            chunk_index=len(chunks)
                        ))
        
        doc.close()
        logger.info(f"Parsed {len(chunks)} chunks from {file_path.name}")
        return chunks

    def _update_context(self, line: str):
        """현재 라인을 분석하여 Context(학교급, 학년군, 영역) 업데이트"""
        # 학교급
        if match := self.school_level_pattern.match(line):
            self.current_school_level = match.group(1)
            
        # 학년군
        if match := self.grade_cluster_pattern.search(line):
            self.current_grade_cluster = match.group(0)
            
        # 영역 (단순화된 로직: 숫자. 영역명 패턴)
        # 예: "1. 수와 연산"
        if re.match(r'^\d+\.\s+[가-힣]+', line):
            # "1. 수와 연산" -> "수와 연산"
            parts = line.split('.', 1)
            if len(parts) > 1:
                self.current_domain = parts[1].strip()

    def _extract_content_for_code(self, page_text: str, code: str) -> str:
        """
        페이지 텍스트에서 해당 코드의 설명 부분을 추출
        간단한 구현: 코드부터 다음 코드 전까지, 혹은 문단 끝까지
        """
        escaped_code = re.escape(code)
        # 코드 뒤의 텍스트 캡처
        pattern = rf'\[{escaped_code}\](.*?)(?=\[|$)'
        match = re.search(pattern, page_text, re.DOTALL)
        if match:
            return f"[{code}] {match.group(1).strip()}"
        return f"[{code}] (내용 추출 실패)"
