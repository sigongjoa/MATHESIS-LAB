#!/usr/bin/env python3
"""
수학과 교육과정 PDF 직접 인덱싱 스크립트

실행 방법:
    python scripts/index_math_direct.py
"""

import asyncio
import sys
from pathlib import Path
import re

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.rag.parser_service import ParserService
from backend.app.services.rag.embedding_service import EmbeddingService
from backend.app.services.rag.vector_store import VectorStore


# 학년 매핑
GRADE_MAPPING = {
    "2": "초1~2",
    "4": "초3~4",
    "6": "초5~6",
    "9": "중1~3",
    "10": "고등학교",
    "12": "고등학교"
}

# 영역 키워드
DOMAIN_KEYWORDS = {
    "수와 연산": ["수", "연산", "덧셈", "뺄셈", "곱셈", "나눗셈", "분수", "소수", "자연수"],
    "도형": ["도형", "삼각형", "사각형", "원", "각", "선분", "평면도형", "입체도형"],
    "측정": ["측정", "길이", "들이", "무게", "시간", "넓이", "부피"],
    "규칙성": ["규칙", "패턴", "함수", "방정식", "식", "대수"],
    "자료와 가능성": ["자료", "그래프", "표", "확률", "통계", "경우의 수"]
}


def extract_grade_from_code(code: str) -> str:
    """성취기준 코드에서 학년 추출"""
    if not code:
        return "기타"
    
    # [2수01-01] → "2"
    grade_num = code[1] if len(code) > 1 else ""
    return GRADE_MAPPING.get(grade_num, "기타")


def extract_domain_from_content(content: str) -> str:
    """내용에서 영역 추출"""
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in content for kw in keywords):
            return domain
    return "일반"


async def index_math_curriculum():
    """수학과 교육과정 직접 인덱싱"""
    
    print("=" * 70)
    print("수학과 교육과정 PDF → RAG 인덱싱")
    print("=" * 70)
    print()
    
    # 1. 서비스 초기화
    print("1️⃣  서비스 초기화 중...")
    parser = ParserService()
    embedding_service = EmbeddingService(use_ollama=True)
    vector_store = VectorStore()
    
    await vector_store.initialize_collection()
    print("   ✅ 서비스 초기화 완료")
    print()
    
    # 2. 파일 파싱
    pdf_path = Path("asset/[별책8]+수학과+교육과정.pdf")
    
    if not pdf_path.exists():
        print(f"   ❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    metadata = {
        "policy_version": "2022개정",
        "scope_type": "NATIONAL",
        "subject": "수학",
        "document_type": "성취기준"
    }
    
    print(f"2️⃣  PDF 파싱 중... ({pdf_path.name})")
    chunks = await parser.parse_document(pdf_path, "curriculum", metadata)
    print(f"   ✅ {len(chunks)}개 청크 생성 완료")
    print()
    
    # 3. 메타데이터 보강
    print("3️⃣  메타데이터 보강 중...")
    for chunk in chunks:
        # 성취기준 코드에서 학년 추출
        curriculum_code = chunk.metadata.get("curriculum_code", "")
        if curriculum_code:
            grade = extract_grade_from_code(curriculum_code)
            chunk.metadata["grade_level"] = grade
        
        # 내용에서 영역 추출
        domain = extract_domain_from_content(chunk.content)
        chunk.metadata["domain"] = domain
    
    print(f"   ✅ 메타데이터 보강 완료")
    print()
    
    # 4. 샘플 청크 출력
    print("4️⃣  샘플 청크 (처음 3개):")
    print("-" * 70)
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n[청크 {i}]")
        print(f"  내용: {chunk.content[:100]}...")
        print(f"  메타데이터: {chunk.metadata}")
    print("-" * 70)
    print()
    
    # 5. 임베딩 생성
    print("5️⃣  임베딩 생성 중... (Ollama 사용)")
    print(f"   배치 크기: 10개씩")
    
    embeddings = await embedding_service.embed_batch(
        [c.content for c in chunks],
        batch_size=10
    )
    print(f"   ✅ {len(embeddings)}개 임베딩 생성 완료")
    print(f"   벡터 차원: {len(embeddings[0])}")
    print()
    
    # 6. 벡터 DB 저장
    print("6️⃣  벡터 DB 저장 중...")
    batch_data = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"math_2022_{i:04d}"
        batch_data.append((
            chunk_id,
            embedding,
            chunk.metadata,
            chunk.content
        ))
    
    await vector_store.upsert_batch(batch_data)
    print(f"   ✅ {len(batch_data)}개 청크 저장 완료")
    print()
    
    # 7. 통계 출력
    print("=" * 70)
    print("📊 인덱싱 통계")
    print("=" * 70)
    print(f"총 청크 수: {len(chunks)}")
    print(f"벡터 차원: {len(embeddings[0])}")
    print(f"평균 청크 크기: {sum(len(c.content) for c in chunks) // len(chunks)} 문자")
    
    # 학년별 통계
    grade_stats = {}
    for chunk in chunks:
        grade = chunk.metadata.get("grade_level", "기타")
        grade_stats[grade] = grade_stats.get(grade, 0) + 1
    
    print(f"\n학년별 청크 수:")
    for grade, count in sorted(grade_stats.items()):
        print(f"  {grade}: {count}개")
    
    # 영역별 통계
    domain_stats = {}
    for chunk in chunks:
        domain = chunk.metadata.get("domain", "일반")
        domain_stats[domain] = domain_stats.get(domain, 0) + 1
    
    print(f"\n영역별 청크 수:")
    for domain, count in sorted(domain_stats.items()):
        print(f"  {domain}: {count}개")
    
    print()
    print("=" * 70)
    print("🎉 인덱싱 완료!")
    print("=" * 70)
    print()
    print("다음 단계:")
    print("  1. 서버 실행: uvicorn backend.app.main:app --reload")
    print("  2. Swagger UI: http://localhost:8000/docs")
    print("  3. 테스트 질의: POST /api/v1/rag/query")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(index_math_curriculum())
    except KeyboardInterrupt:
        print("\n\n중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
