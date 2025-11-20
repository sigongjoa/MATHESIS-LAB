# RAG 시스템 테스트 계획서

## 📋 목차
1. [테스트 전략](#1-테스트-전략)
2. [단위 테스트 (pytest)](#2-단위-테스트-pytest)
3. [통합 테스트](#3-통합-테스트)
4. [E2E 테스트](#4-e2e-테스트)
5. [성능 테스트](#5-성능-테스트)
6. [RAG 품질 테스트](#6-rag-품질-테스트)

---

## 1. 테스트 전략

### 1.1 테스트 피라미드

```
        ╱╲
       ╱E2E╲         10% - 사용자 시나리오
      ╱──────╲
     ╱ 통합   ╲       20% - 컴포넌트 간 상호작용
    ╱──────────╲
   ╱   단위     ╲     70% - 개별 함수/클래스
  ╱──────────────╲
```

### 1.2 테스트 범위

| 계층 | 테스트 유형 | 도구 | 목표 커버리지 |
|------|-----------|------|-------------|
| **Backend** | 단위 테스트 | pytest | 80%+ |
| **Backend** | 통합 테스트 | pytest | 60%+ |
| **Frontend** | 단위 테스트 | Jest, React Testing Library | 70%+ |
| **E2E** | 시나리오 테스트 | Playwright | 핵심 플로우 100% |
| **RAG** | 품질 테스트 | Ragas, Custom | Golden Set 100% |

---

## 2. 단위 테스트 (pytest)

### 2.1 Parser Service 테스트

```python
# backend/tests/unit/test_parser_service.py

import pytest
from pathlib import Path
from backend.app.services.parser_service import ParserService, ParseError
from backend.app.services.parser_service import ParsedChunk

@pytest.fixture
def parser_service():
    """Parser 서비스 픽스처"""
    return ParserService()

@pytest.fixture
def sample_pdf_path():
    """샘플 PDF 파일 경로"""
    return Path("tests/fixtures/sample_curriculum.pdf")

class TestParserService:
    """Parser Service 단위 테스트"""
    
    def test_parse_pdf_success(self, parser_service, sample_pdf_path):
        """PDF 파싱 성공 케이스"""
        # Given
        assert sample_pdf_path.exists()
        
        # When
        chunks = parser_service.parse_document(
            sample_pdf_path,
            document_type="curriculum"
        )
        
        # Then
        assert len(chunks) > 0
        assert all(isinstance(c, ParsedChunk) for c in chunks)
        assert all(c.content for c in chunks)
        assert all(c.metadata for c in chunks)
    
    def test_parse_pdf_with_achievement_code(self, parser_service, sample_pdf_path):
        """성취기준 코드 추출 테스트"""
        # When
        chunks = parser_service.parse_document(sample_pdf_path, "curriculum")
        
        # Then
        achievement_chunks = [
            c for c in chunks 
            if c.metadata.get("curriculum_code")
        ]
        assert len(achievement_chunks) > 0
        
        # 성취기준 코드 형식 검증
        for chunk in achievement_chunks:
            code = chunk.metadata["curriculum_code"]
            assert code.startswith("[")
            assert code.endswith("]")
            # 예: [9수01-01]
            import re
            assert re.match(r'\[\d+[가-힣]+\d+-\d+\]', code)
    
    def test_parse_nonexistent_file(self, parser_service):
        """존재하지 않는 파일 파싱 실패"""
        # Given
        fake_path = Path("nonexistent.pdf")
        
        # When/Then
        with pytest.raises(FileNotFoundError):
            parser_service.parse_document(fake_path, "curriculum")
    
    def test_extract_metadata_national(self, parser_service, sample_pdf_path):
        """국가 교육과정 메타데이터 추출"""
        # When
        chunks = parser_service.parse_document(sample_pdf_path, "curriculum")
        
        # Then
        for chunk in chunks:
            metadata = chunk.metadata
            assert "policy_version" in metadata
            assert metadata["scope_type"] == "NATIONAL"
            assert "document_type" in metadata
    
    def test_validate_chunk_success(self, parser_service):
        """청크 검증 성공"""
        # Given
        valid_chunk = ParsedChunk(
            content="테스트 내용",
            metadata={
                "policy_version": "2022개정",
                "scope_type": "NATIONAL",
                "document_type": "성취기준"
            },
            page_number=1
        )
        
        # When/Then
        assert parser_service.validate_chunk(valid_chunk) is True
    
    def test_validate_chunk_missing_metadata(self, parser_service):
        """필수 메타데이터 누락 시 검증 실패"""
        # Given
        invalid_chunk = ParsedChunk(
            content="테스트 내용",
            metadata={
                "policy_version": "2022개정"
                # scope_type 누락
            }
        )
        
        # When/Then
        assert parser_service.validate_chunk(invalid_chunk) is False

@pytest.mark.asyncio
class TestParserServiceAsync:
    """비동기 파싱 테스트"""
    
    async def test_parse_document_async(self, parser_service, sample_pdf_path):
        """비동기 파싱"""
        chunks = await parser_service.parse_document(
            sample_pdf_path,
            "curriculum"
        )
        assert len(chunks) > 0
```

### 2.2 RAG Service 테스트 (LLM Mock)

```python
# backend/tests/unit/test_rag_service.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.app.services.rag_service import RAGService, RAGQuery
from backend.app.services.vector_store import VectorStore, SearchResult

@pytest.fixture
def mock_vector_store():
    """Vector Store Mock"""
    mock = Mock(spec=VectorStore)
    mock.search = AsyncMock(return_value=[
        SearchResult(
            chunk_id="chunk_123",
            content="최대공약수와 최소공배수는 약수와 배수를 나열하여...",
            score=0.89,
            metadata={
                "policy_version": "2022개정",
                "curriculum_code": "[6수01-05]",
                "page_number": 42
            }
        )
    ])
    return mock

@pytest.fixture
def mock_llm_client():
    """LLM Client Mock"""
    mock = Mock()
    mock.generate = AsyncMock(return_value="아닙니다. 소인수분해로 다루지 않습니다.")
    return mock

@pytest.fixture
def rag_service(mock_vector_store, mock_llm_client, db_session):
    """RAG Service 픽스처"""
    return RAGService(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        db=db_session
    )

@pytest.mark.asyncio
class TestRAGService:
    """RAG Service 단위 테스트"""
    
    async def test_query_success(self, rag_service):
        """RAG 질의 성공"""
        # Given
        request = RAGQuery(
            query="최대공약수는 소인수분해로 다루나요?",
            filters={"policy_version": "2022개정"},
            top_k=5
        )
        
        # When
        response = await rag_service.query(request, user_id="user_123")
        
        # Then
        assert response.answer
        assert len(response.sources) > 0
        assert response.confidence > 0
        assert response.processing_time_ms > 0
        assert response.query_id
    
    async def test_query_with_filters(self, rag_service, mock_vector_store):
        """필터링된 질의"""
        # Given
        request = RAGQuery(
            query="테스트",
            filters={
                "policy_version": "2022개정",
                "scope_type": "NATIONAL",
                "grade_level": "초5~6"
            }
        )
        
        # When
        await rag_service.query(request, user_id="user_123")
        
        # Then
        # Vector store가 올바른 필터로 호출되었는지 확인
        mock_vector_store.search.assert_called_once()
        call_args = mock_vector_store.search.call_args
        assert call_args[1]["filters"] == request.filters
    
    async def test_build_prompt_with_sources(self, rag_service):
        """프롬프트 구성 테스트"""
        # Given
        query = "최대공약수는?"
        sources = [
            SearchResult(
                chunk_id="chunk_1",
                content="내용 1",
                score=0.9,
                metadata={}
            ),
            SearchResult(
                chunk_id="chunk_2",
                content="내용 2",
                score=0.8,
                metadata={}
            )
        ]
        
        # When
        prompt = rag_service._build_prompt(query, sources)
        
        # Then
        assert "최대공약수는?" in prompt
        assert "내용 1" in prompt
        assert "내용 2" in prompt
        assert "근거" in prompt or "출처" in prompt
    
    async def test_add_citations(self, rag_service):
        """인용 추가 테스트"""
        # Given
        answer = "아닙니다. 소인수분해로 다루지 않습니다."
        sources = [
            SearchResult(
                chunk_id="chunk_123",
                content="...",
                score=0.89,
                metadata={"page_number": 42}
            )
        ]
        
        # When
        answer_with_citations = rag_service._add_citations(answer, sources)
        
        # Then
        assert "<출처:" in answer_with_citations or "chunk_123" in answer_with_citations
    
    async def test_query_timeout(self, rag_service, mock_vector_store):
        """타임아웃 처리"""
        # Given
        import asyncio
        mock_vector_store.search = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        request = RAGQuery(query="테스트")
        
        # When/Then
        with pytest.raises(asyncio.TimeoutError):
            await rag_service.query(request, user_id="user_123")
```

### 2.3 Vector Store 테스트

```python
# backend/tests/unit/test_vector_store.py

import pytest
from backend.app.services.vector_store import VectorStore

@pytest.fixture
def vector_store():
    """Vector Store 픽스처 (테스트용 인메모리)"""
    # 실제 Qdrant 대신 Mock 사용
    from unittest.mock import Mock
    mock_client = Mock()
    store = VectorStore(url="memory://", api_key=None)
    store.client = mock_client
    return store

class TestVectorStore:
    """Vector Store 단위 테스트"""
    
    @pytest.mark.asyncio
    async def test_upsert_chunk(self, vector_store):
        """청크 삽입 테스트"""
        # Given
        chunk_id = "chunk_123"
        embedding = [0.1] * 3072
        metadata = {"policy_version": "2022개정"}
        content = "테스트 내용"
        
        # When
        await vector_store.upsert(chunk_id, embedding, metadata, content)
        
        # Then
        vector_store.client.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, vector_store):
        """필터링된 검색"""
        # Given
        query_vector = [0.1] * 3072
        filters = {"policy_version": "2022개정"}
        
        # When
        results = await vector_store.search(query_vector, filters, top_k=5)
        
        # Then
        vector_store.client.search.assert_called_once()
        call_args = vector_store.client.search.call_args
        assert call_args[1]["query_filter"] is not None
```

---

## 3. 통합 테스트

### 3.1 End-to-End 파이프라인 테스트

```python
# backend/tests/integration/test_rag_pipeline.py

import pytest
from pathlib import Path
from backend.app.services.parser_service import ParserService
from backend.app.services.rag_service import RAGService, RAGQuery
from backend.app.services.vector_store import VectorStore

@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGPipeline:
    """RAG 전체 파이프라인 통합 테스트"""
    
    async def test_full_indexing_and_query_pipeline(
        self,
        parser_service,
        vector_store,
        rag_service,
        sample_pdf_path
    ):
        """문서 인덱싱 → 질의 → 응답 전체 플로우"""
        # 1. 문서 파싱
        chunks = await parser_service.parse_document(
            sample_pdf_path,
            "curriculum"
        )
        assert len(chunks) > 0
        
        # 2. 임베딩 생성 및 인덱싱
        for chunk in chunks:
            embedding = await embedding_service.embed(chunk.content)
            await vector_store.upsert(
                chunk.chunk_id,
                embedding,
                chunk.metadata,
                chunk.content
            )
        
        # 3. 질의 실행
        request = RAGQuery(
            query="최대공약수는 소인수분해로 다루나요?",
            filters={"policy_version": "2022개정"}
        )
        response = await rag_service.query(request, user_id="test_user")
        
        # 4. 응답 검증
        assert response.answer
        assert len(response.sources) > 0
        assert response.confidence > 0
        
        # 5. 인용 검증
        assert "<출처:" in response.answer
```

### 3.2 데이터베이스 통합 테스트

```python
# backend/tests/integration/test_rag_repository.py

import pytest
from backend.app.models.rag_chunk import RAGChunk
from backend.app.repositories.rag_repository import RAGRepository

@pytest.mark.integration
class TestRAGRepository:
    """RAG Repository 통합 테스트"""
    
    def test_create_and_retrieve_chunk(self, db_session):
        """청크 생성 및 조회"""
        # Given
        repo = RAGRepository(db_session)
        chunk_data = {
            "content": "테스트 내용",
            "metadata": {"policy_version": "2022개정"},
            "document_id": "doc_123"
        }
        
        # When
        chunk = repo.create_chunk(chunk_data)
        db_session.commit()
        
        # Then
        retrieved = repo.get_chunk(chunk.chunk_id)
        assert retrieved is not None
        assert retrieved.content == "테스트 내용"
    
    def test_query_chunks_by_metadata(self, db_session):
        """메타데이터로 청크 조회"""
        # Given
        repo = RAGRepository(db_session)
        # 테스트 데이터 생성...
        
        # When
        chunks = repo.find_by_metadata({
            "policy_version": "2022개정",
            "scope_type": "NATIONAL"
        })
        
        # Then
        assert len(chunks) > 0
        assert all(
            c.metadata["policy_version"] == "2022개정"
            for c in chunks
        )
```

---

## 4. E2E 테스트

### 4.1 Playwright E2E 테스트

```typescript
// MATHESIS-LAB_FRONT/tests/e2e/rag-query.spec.ts

import { test, expect } from '@playwright/test';

test.describe('RAG Query Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 로그인
    await page.goto('http://localhost:3001');
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password');
    await page.click('#login-button');
    await expect(page).toHaveURL(/.*curriculum/);
  });

  test('사용자가 RAG 질의를 하고 답변을 받는다', async ({ page }) => {
    // Given: AI Assistant 열기
    await page.click('#ai-assistant-button');
    await expect(page.locator('#rag-chat-panel')).toBeVisible();

    // When: 질문 입력
    const query = '초등학교 5~6학년 수학에서 최대공약수는 소인수분해로 다루나요?';
    await page.fill('#rag-query-input', query);
    await page.click('#rag-submit-button');

    // Then: 답변 표시 대기
    await expect(page.locator('#rag-answer')).toBeVisible({ timeout: 10000 });
    
    // 답변 내용 검증
    const answer = await page.locator('#rag-answer').textContent();
    expect(answer).toContain('아닙니다');
    expect(answer).toContain('소인수분해');

    // 출처 표시 검증
    const sources = page.locator('.rag-source-item');
    await expect(sources).toHaveCount(expect.any(Number));
    
    // 첫 번째 출처 확인
    const firstSource = sources.first();
    await expect(firstSource).toContainText('출처:');
    await expect(firstSource).toContainText('페이지');
  });

  test('필터를 적용하여 질의한다', async ({ page }) => {
    // Given
    await page.click('#ai-assistant-button');
    await page.click('#rag-filter-button');

    // When: 필터 설정
    await page.selectOption('#filter-policy-version', '2022개정');
    await page.selectOption('#filter-grade-level', '초5~6');
    await page.fill('#rag-query-input', '최대공약수');
    await page.click('#rag-submit-button');

    // Then
    await expect(page.locator('#rag-answer')).toBeVisible();
    
    // 출처의 메타데이터 확인
    await page.click('.rag-source-item:first-child .source-metadata-toggle');
    await expect(page.locator('.source-metadata')).toContainText('2022개정');
    await expect(page.locator('.source-metadata')).toContainText('초5~6');
  });

  test('답변에 피드백을 제공한다', async ({ page }) => {
    // Given: 질의 및 답변 받기
    await page.click('#ai-assistant-button');
    await page.fill('#rag-query-input', '테스트 질문');
    await page.click('#rag-submit-button');
    await expect(page.locator('#rag-answer')).toBeVisible();

    // When: 피드백 제공
    await page.click('#feedback-helpful-button');
    await page.fill('#feedback-comment', '정확한 답변이었습니다');
    await page.click('#feedback-submit-button');

    // Then
    await expect(page.locator('#feedback-success-message')).toBeVisible();
    await expect(page.locator('#feedback-success-message')).toContainText('감사합니다');
  });
});
```

### 4.2 문서 인덱싱 E2E 테스트

```typescript
// MATHESIS-LAB_FRONT/tests/e2e/document-indexing.spec.ts

import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Document Indexing Flow', () => {
  test('관리자가 새 교육과정 문서를 업로드하고 인덱싱한다', async ({ page }) => {
    // Given: 관리자 로그인
    await page.goto('http://localhost:3001/admin');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'admin_password');
    await page.click('#login-button');

    // RAG 관리 페이지로 이동
    await page.click('#rag-management-menu');
    await expect(page).toHaveURL(/.*rag\/management/);

    // When: 문서 업로드
    const filePath = path.join(__dirname, '../fixtures/sample_curriculum.pdf');
    await page.setInputFiles('#document-upload-input', filePath);
    
    // 메타데이터 입력
    await page.selectOption('#document-type', 'curriculum');
    await page.selectOption('#policy-version', '2022개정');
    await page.selectOption('#scope-type', 'NATIONAL');
    
    // 업로드 시작
    await page.click('#upload-start-button');

    // Then: 진행 상태 표시
    await expect(page.locator('#indexing-progress-bar')).toBeVisible();
    
    // 완료 대기 (최대 2분)
    await expect(page.locator('#indexing-status')).toContainText('완료', { timeout: 120000 });
    
    // 청크 수 확인
    const chunksCount = await page.locator('#chunks-count').textContent();
    expect(parseInt(chunksCount!)).toBeGreaterThan(0);
  });
});
```

---

## 5. 성능 테스트

### 5.1 부하 테스트 (Locust)

```python
# backend/tests/performance/locustfile.py

from locust import HttpUser, task, between
import json

class RAGUser(HttpUser):
    """RAG 시스템 부하 테스트"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """테스트 시작 시 로그인"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def query_rag(self):
        """RAG 질의 (가장 빈번한 작업)"""
        self.client.post(
            "/api/v1/rag/query",
            headers=self.headers,
            json={
                "query": "최대공약수는 소인수분해로 다루나요?",
                "filters": {"policy_version": "2022개정"},
                "top_k": 5
            },
            name="/rag/query"
        )
    
    @task(1)
    def search_chunks(self):
        """청크 검색"""
        self.client.get(
            "/api/v1/rag/search?query=최대공약수&top_k=5",
            headers=self.headers,
            name="/rag/search"
        )
```

**실행:**
```bash
locust -f backend/tests/performance/locustfile.py --host=http://localhost:8000
```

**목표:**
- P95 응답 시간: < 3초
- 동시 사용자: 100명
- 에러율: < 1%

---

## 6. RAG 품질 테스트

### 6.1 Golden Set 테스트

```python
# backend/tests/quality/test_golden_set.py

import pytest
from backend.app.services.rag_service import RAGService, RAGQuery

# Golden Set 정의
GOLDEN_SET = [
    {
        "query": "초등학교 5~6학년 수학에서 최대공약수는 소인수분해로 다루나요?",
        "expected_answer_contains": ["아닙니다", "소인수분해", "다루지 않"],
        "expected_sources_min": 1,
        "filters": {"policy_version": "2022개정", "grade_level": "초5~6"},
        "min_confidence": 0.7
    },
    {
        "query": "중학교 1~3학년에서 일차함수와 일차방정식의 관계는?",
        "expected_answer_contains": ["일차함수", "일차방정식", "관계"],
        "expected_sources_min": 2,
        "filters": {"policy_version": "2022개정", "grade_level": "중1~3"},
        "min_confidence": 0.7
    },
    # ... 더 많은 테스트 케이스
]

@pytest.mark.quality
@pytest.mark.asyncio
class TestGoldenSet:
    """Golden Set 품질 테스트"""
    
    @pytest.mark.parametrize("test_case", GOLDEN_SET)
    async def test_golden_set_query(self, rag_service, test_case):
        """Golden Set 각 케이스 테스트"""
        # Given
        request = RAGQuery(
            query=test_case["query"],
            filters=test_case.get("filters", {}),
            top_k=5
        )
        
        # When
        response = await rag_service.query(request, user_id="test_user")
        
        # Then
        # 1. 답변에 기대 키워드 포함 확인
        for keyword in test_case["expected_answer_contains"]:
            assert keyword in response.answer, \
                f"Expected keyword '{keyword}' not found in answer"
        
        # 2. 최소 출처 수 확인
        assert len(response.sources) >= test_case["expected_sources_min"], \
            f"Expected at least {test_case['expected_sources_min']} sources"
        
        # 3. 신뢰도 확인
        assert response.confidence >= test_case["min_confidence"], \
            f"Confidence {response.confidence} below threshold {test_case['min_confidence']}"
        
        # 4. 인용 포함 확인
        assert "<출처:" in response.answer, "No citations found in answer"
```

### 6.2 Ragas 평가

```python
# backend/tests/quality/test_ragas_evaluation.py

import pytest
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

@pytest.mark.quality
@pytest.mark.asyncio
async def test_ragas_evaluation(rag_service):
    """Ragas를 사용한 RAG 품질 평가"""
    # Given: 테스트 데이터셋
    test_dataset = {
        "question": ["최대공약수는 소인수분해로 다루나요?"],
        "answer": [],
        "contexts": [],
        "ground_truth": ["아닙니다. 약수와 배수를 나열하여 찾는 방법으로 다룹니다."]
    }
    
    # When: RAG 질의
    request = RAGQuery(query=test_dataset["question"][0])
    response = await rag_service.query(request, user_id="test_user")
    
    test_dataset["answer"].append(response.answer)
    test_dataset["contexts"].append([s.content for s in response.sources])
    
    # Then: Ragas 평가
    result = evaluate(
        test_dataset,
        metrics=[faithfulness, answer_relevancy, context_recall]
    )
    
    # 평가 기준
    assert result["faithfulness"] >= 0.8, "Faithfulness too low"
    assert result["answer_relevancy"] >= 0.7, "Answer relevancy too low"
    assert result["context_recall"] >= 0.7, "Context recall too low"
```

---

## 7. 테스트 실행

### 7.1 전체 테스트 실행

```bash
# 백엔드 단위 테스트
pytest backend/tests/unit -v --cov=backend/app --cov-report=html

# 백엔드 통합 테스트
pytest backend/tests/integration -v -m integration

# 품질 테스트
pytest backend/tests/quality -v -m quality

# 프론트엔드 테스트
cd MATHESIS-LAB_FRONT
npm test

# E2E 테스트
npx playwright test

# 성능 테스트
locust -f backend/tests/performance/locustfile.py
```

### 7.2 CI/CD 통합

```yaml
# .github/workflows/rag-tests.yml

name: RAG Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run unit tests
        run: pytest backend/tests/unit -v --cov=backend/app
      - name: Upload coverage
        uses: codecov/codecov-action@v2

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Run integration tests
        run: pytest backend/tests/integration -v -m integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npx playwright test
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀
