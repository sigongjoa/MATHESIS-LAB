"""
Parser Service 단위 테스트
"""

import pytest
from pathlib import Path
from backend.app.services.rag.parser_service import ParserService, ParsedChunk


@pytest.fixture
def parser_service():
    """Parser 서비스 픽스처"""
    return ParserService()


@pytest.fixture
def sample_metadata():
    """샘플 메타데이터"""
    return {
        "policy_version": "2022개정",
        "scope_type": "NATIONAL"
    }


class TestParserService:
    """Parser Service 테스트"""
    
    def test_chunk_text(self, parser_service):
        """텍스트 청킹 테스트"""
        text = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다."
        chunks = parser_service._chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)
    
    def test_calculate_content_hash(self):
        """내용 해시 계산 테스트"""
        content = "테스트 내용"
        hash1 = ParserService.calculate_content_hash(content)
        hash2 = ParserService.calculate_content_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256
    
    def test_validate_chunk_success(self, parser_service, sample_metadata):
        """청크 검증 성공"""
        chunk = ParsedChunk(
            content="테스트 내용입니다. 충분히 긴 내용입니다.",
            metadata=sample_metadata,
            chunk_index=0
        )
        
        assert parser_service.validate_chunk(chunk) is True
    
    def test_validate_chunk_missing_metadata(self, parser_service):
        """필수 메타데이터 누락 시 검증 실패"""
        chunk = ParsedChunk(
            content="테스트 내용",
            metadata={"policy_version": "2022개정"},  # scope_type 누락
            chunk_index=0
        )
        
        assert parser_service.validate_chunk(chunk) is False
    
    def test_validate_chunk_short_content(self, parser_service, sample_metadata):
        """내용이 너무 짧으면 검증 실패"""
        chunk = ParsedChunk(
            content="짧음",
            metadata=sample_metadata,
            chunk_index=0
        )
        
        assert parser_service.validate_chunk(chunk) is False
    
    def test_extract_achievement_section(self, parser_service):
        """성취기준 섹션 추출 테스트"""
        text = "[9수01-01] 소인수분해의 뜻을 알고, 자연수를 소인수분해할 수 있다. [9수01-02] 최대공약수와 최소공배수를 구할 수 있다."
        
        section = parser_service._extract_achievement_section(text, "9수01-01")
        
        assert "소인수분해" in section
        assert "[9수01-02]" not in section  # 다음 섹션은 포함되지 않음
    
    def test_classify_section(self, parser_service):
        """섹션 분류 테스트"""
        assert parser_service._classify_section("1. 평가 계획") == "평가계획"
        assert parser_service._classify_section("2. 수업 운영") == "수업운영"
        assert parser_service._classify_section("3. 교수학습 방법") == "수업운영"
        assert parser_service._classify_section("4. 기타") == "일반"


@pytest.mark.asyncio
class TestParserServiceAsync:
    """Parser Service 비동기 테스트"""
    
    async def test_parse_unsupported_format(self, parser_service, sample_metadata):
        """지원하지 않는 파일 형식"""
        fake_path = Path("test.txt")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            await parser_service.parse_document(fake_path, "curriculum", sample_metadata)
    
    async def test_parse_nonexistent_file(self, parser_service, sample_metadata):
        """존재하지 않는 파일"""
        fake_path = Path("nonexistent.pdf")
        
        with pytest.raises(FileNotFoundError):
            await parser_service.parse_document(fake_path, "curriculum", sample_metadata)
