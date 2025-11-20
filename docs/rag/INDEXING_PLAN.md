# 수학과 교육과정 PDF → RAG 인덱싱 실행 계획

## 📊 문서 분석 결과

### 기본 정보
- **파일명**: `[별책8]+수학과+교육과정.pdf`
- **총 페이지**: 263페이지
- **교육과정**: 2022 개정 교육과정
- **과목**: 수학
- **발행**: 교육부 고시 제2022-33호

### 문서 구조
- **성취기준 코드**: `[2수01-01]`, `[2수01-02]` 등 체계적 구조
- **학년별 구성**: 초등 1~6학년, 중등 1~3학년, 고등학교
- **영역별 구성**: 수와 연산, 도형, 측정, 규칙성, 자료와 가능성 등

## 🎯 RAG 인덱싱 전략

### 1. 메타데이터 설계

```json
{
  "policy_version": "2022개정",
  "scope_type": "NATIONAL",
  "document_type": "curriculum",
  "subject": "수학",
  "grade_level": "초1~2",  // 동적으로 추출
  "domain": "수와 연산",    // 동적으로 추출
  "curriculum_code": "[2수01-01]",  // 성취기준 코드
  "page_number": 42,
  "source_file": "asset/[별책8]+수학과+교육과정.pdf"
}
```

### 2. 청킹 전략

#### 전략 A: 성취기준 단위 청킹 (권장)
- **장점**: 의미적으로 완결된 단위
- **방법**: `[2수01-01]` 패턴으로 섹션 분리
- **예상 청크 수**: ~200개 (성취기준 개수)

```python
# 성취기준 패턴으로 분할
pattern = r'\[(\d+[가-힣]+\d+-\d+)\](.*?)(?=\[|$)'
```

#### 전략 B: 페이지 단위 청킹
- **장점**: 구현 간단
- **단점**: 의미 단위 분리 안 됨
- **예상 청크 수**: ~263개

#### 전략 C: 하이브리드 청킹 (최종 선택)
- **성취기준이 있는 페이지**: 성취기준 단위로 분할
- **일반 페이지**: 고정 크기(1000자) 단위로 분할
- **예상 청크 수**: ~250개

### 3. 인덱싱 파이프라인

```
PDF 파일
    ↓
1. 파싱 (PyMuPDF)
    ↓
2. 성취기준 추출 및 섹션 분리
    ↓
3. 메타데이터 자동 추출
   - 학년: [2수01-01] → "초1~2"
   - 영역: 문맥에서 추출
    ↓
4. 청크 생성 (250개)
    ↓
5. 임베딩 생성 (Ollama)
   - 배치 크기: 10개씩
   - 예상 시간: ~5분
    ↓
6. 벡터 DB 저장 (Qdrant)
    ↓
7. RDB 메타데이터 저장 (PostgreSQL)
```

### 4. 학년 매핑 규칙

```python
GRADE_MAPPING = {
    "2": "초1~2",
    "4": "초3~4",
    "6": "초5~6",
    "9": "중1~3",
    "10": "고등학교",
    "12": "고등학교"
}

def extract_grade(code):
    """성취기준 코드에서 학년 추출"""
    # [2수01-01] → "2" → "초1~2"
    grade_num = code[0]
    return GRADE_MAPPING.get(grade_num, "기타")
```

### 5. 영역 추출 전략

```python
DOMAIN_KEYWORDS = {
    "수와 연산": ["수", "연산", "덧셈", "뺄셈", "곱셈", "나눗셈", "분수", "소수"],
    "도형": ["도형", "삼각형", "사각형", "원", "각", "선분"],
    "측정": ["측정", "길이", "들이", "무게", "시간", "넓이", "부피"],
    "규칙성": ["규칙", "패턴", "함수", "방정식", "식"],
    "자료와 가능성": ["자료", "그래프", "표", "확률", "통계"]
}

def extract_domain(content):
    """내용에서 영역 추출"""
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in content for kw in keywords):
            return domain
    return "일반"
```

## 📝 실행 스크립트

### 스크립트 1: 인덱싱 실행

```bash
#!/bin/bash
# scripts/index_math_curriculum.sh

# 1. 서버 및 인프라 확인
echo "1. 인프라 확인..."
docker ps | grep redis || docker run -d -p 6379:6379 redis:latest
docker ps | grep qdrant || docker run -d -p 6333:6333 qdrant/qdrant

# 2. Celery Worker 시작 (별도 터미널)
echo "2. Celery Worker 시작 필요 (별도 터미널에서):"
echo "   celery -A backend.app.celery_app worker --loglevel=info"

# 3. 인덱싱 API 호출
echo "3. 인덱싱 시작..."
curl -X POST http://localhost:8000/api/v1/rag/index \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@asset/[별책8]+수학과+교육과정.pdf" \
  -F "document_type=curriculum" \
  -F 'metadata={"policy_version":"2022개정","scope_type":"NATIONAL","subject":"수학"}'

echo "4. 인덱싱 작업이 시작되었습니다!"
echo "   진행 상황은 /api/v1/rag/status/{job_id}에서 확인하세요."
```

### 스크립트 2: 직접 인덱싱 (테스트용)

```python
#!/usr/bin/env python3
# scripts/index_math_direct.py

import asyncio
from pathlib import Path
from backend.app.services.rag.parser_service import ParserService
from backend.app.services.rag.embedding_service import EmbeddingService
from backend.app.services.rag.vector_store import VectorStore

async def index_math_curriculum():
    """수학과 교육과정 직접 인덱싱"""
    
    # 1. 서비스 초기화
    parser = ParserService()
    embedding_service = EmbeddingService(use_ollama=True)
    vector_store = VectorStore()
    
    await vector_store.initialize_collection()
    
    # 2. 파일 파싱
    pdf_path = Path("asset/[별책8]+수학과+교육과정.pdf")
    metadata = {
        "policy_version": "2022개정",
        "scope_type": "NATIONAL",
        "subject": "수학"
    }
    
    print("📄 파싱 시작...")
    chunks = await parser.parse_document(pdf_path, "curriculum", metadata)
    print(f"✅ {len(chunks)}개 청크 생성 완료")
    
    # 3. 임베딩 생성
    print("🔢 임베딩 생성 중...")
    embeddings = await embedding_service.embed_batch(
        [c.content for c in chunks],
        batch_size=10
    )
    print(f"✅ {len(embeddings)}개 임베딩 생성 완료")
    
    # 4. 벡터 DB 저장
    print("💾 벡터 DB 저장 중...")
    batch_data = []
    for chunk, embedding in zip(chunks, embeddings):
        batch_data.append((
            f"math_chunk_{chunk.chunk_index}",
            embedding,
            chunk.metadata,
            chunk.content
        ))
    
    await vector_store.upsert_batch(batch_data)
    print(f"✅ {len(batch_data)}개 청크 저장 완료")
    
    print("\n🎉 인덱싱 완료!")
    print(f"   - 총 청크 수: {len(chunks)}")
    print(f"   - 벡터 차원: {len(embeddings[0])}")

if __name__ == "__main__":
    asyncio.run(index_math_curriculum())
```

## 🔍 검증 계획

### 1. 인덱싱 후 확인 사항

```bash
# Qdrant 컬렉션 확인
curl http://localhost:6333/collections/rag_chunks

# 청크 수 확인
curl http://localhost:6333/collections/rag_chunks/points/count
```

### 2. 샘플 질의 테스트

```python
# 테스트 질의
test_queries = [
    "초등학교 5~6학년에서 최대공약수는 소인수분해로 다루나요?",
    "중학교 1~3학년 함수 영역의 성취기준은 무엇인가요?",
    "초등학교 3~4학년 곱셈 구구단 성취기준을 알려주세요"
]
```

### 3. 품질 검증

- ✅ 성취기준 코드가 올바르게 추출되었는지
- ✅ 학년 정보가 정확한지
- ✅ 영역 분류가 적절한지
- ✅ 검색 결과가 관련성 있는지

## 📊 예상 결과

### 인덱싱 통계
- **총 청크 수**: ~250개
- **평균 청크 크기**: ~500자
- **임베딩 시간**: ~5분 (Ollama)
- **저장 용량**: ~200MB (벡터 + 메타데이터)

### 검색 성능
- **응답 시간**: < 2초
- **Top-K 검색**: 5개 청크
- **정확도**: 성취기준 기반 검색 90%+

## 🚀 실행 순서

1. **인프라 준비** (1분)
   ```bash
   docker run -d -p 6379:6379 redis:latest
   docker run -d -p 6333:6333 qdrant/qdrant
   ```

2. **Celery Worker 시작** (별도 터미널)
   ```bash
   celery -A backend.app.celery_app worker --loglevel=info
   ```

3. **서버 시작**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

4. **인덱싱 실행** (5분)
   ```bash
   python scripts/index_math_direct.py
   ```

5. **검증**
   ```bash
   # Swagger UI에서 테스트
   # http://localhost:8000/docs
   # POST /api/v1/rag/query
   ```

## 💡 최적화 팁

1. **배치 크기 조정**: Ollama 성능에 따라 10 → 20으로 증가 가능
2. **청킹 전략**: 성취기준이 명확하지 않은 페이지는 스킵
3. **메타데이터 보강**: 수동으로 영역 정보 추가 가능
4. **캐싱**: 자주 검색되는 질의는 캐싱

---

**준비 완료!** 이제 실제로 인덱싱을 실행할 준비가 되었습니다! 🚀
