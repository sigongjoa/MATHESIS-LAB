# RAG API 명세서

OpenAPI 3.0 스타일의 상세 API 명세서입니다.

## 📋 목차
1. [기본 정보](#1-기본-정보)
2. [인증](#2-인증)
3. [엔드포인트](#3-엔드포인트)
4. [데이터 모델](#4-데이터-모델)
5. [에러 코드](#5-에러-코드)

---

## 1. 기본 정보

- **Base URL**: `http://localhost:8000/api/v1/rag`
- **Content-Type**: `application/json`
- **인증 방식**: JWT Bearer Token (기존 시스템과 동일)

---

## 2. 인증

모든 엔드포인트는 인증이 필요합니다.

```http
Authorization: Bearer <JWT_TOKEN>
```

---

## 3. 엔드포인트

### 3.1 POST /query - RAG 질의

사용자 질문에 대해 RAG 기반 답변을 생성합니다.

#### Request

```http
POST /api/v1/rag/query
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "query": "초등학교 5~6학년 수학에서 최대공약수는 소인수분해로 다루는지 알려줘",
  "filters": {
    "policy_version": "2022개정",
    "scope_type": "NATIONAL",
    "grade_level": "초5~6",
    "domain": "수와 연산"
  },
  "top_k": 5,
  "include_sources": true,
  "stream": false
}
```

**필드 설명:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query` | string | ✓ | 사용자 질문 (최대 1000자) |
| `filters` | object | ✗ | 메타데이터 필터 |
| `filters.policy_version` | string | ✗ | 교육과정 버전 (예: "2022개정") |
| `filters.scope_type` | enum | ✗ | "NATIONAL" 또는 "SCHOOL" |
| `filters.institution_id` | string | ✗ | 학교 ID (scope_type이 SCHOOL인 경우) |
| `filters.grade_level` | string | ✗ | 학년 (예: "초5~6", "중1~3") |
| `filters.domain` | string | ✗ | 영역 (예: "수와 연산") |
| `filters.curriculum_id` | string | ✗ | 커리큘럼 ID (기존 시스템 연동) |
| `filters.node_id` | string | ✗ | 노드 ID (기존 시스템 연동) |
| `top_k` | integer | ✗ | 검색할 청크 수 (기본값: 5, 최대: 20) |
| `include_sources` | boolean | ✗ | 출처 포함 여부 (기본값: true) |
| `stream` | boolean | ✗ | 스트리밍 응답 여부 (기본값: false) |

#### Response (200 OK)

```json
{
  "answer": "아닙니다. 초등학교 5~6학년에서는 최대공약수를 소인수분해로 다루지 않습니다. <출처: chunk_123> 약수와 배수를 나열하여 공통된 약수와 배수를 찾는 방법으로 그 의미를 이해하게 하며, 소인수의 곱으로 나타내어 구하는 방법은 다루지 않습니다. <출처: chunk_123>",
  "sources": [
    {
      "chunk_id": "chunk_123",
      "content": "최대공약수와 최소공배수는 약수와 배수를 나열하여 공통된 약수와 배수를 찾는 방법으로 그 의미를 이해하게 하며, 소인수의 곱으로 나타내어 구하는 방법은 다루지 않는다.",
      "score": 0.89,
      "metadata": {
        "policy_version": "2022개정",
        "scope_type": "NATIONAL",
        "document_type": "성취기준",
        "curriculum_code": "[6수01-05]",
        "grade_level": "초5~6",
        "domain": "수와 연산",
        "page_number": 42,
        "source_file": "assets/curriculum/2022/[별책 8] 수학과 교육과정.pdf"
      }
    }
  ],
  "confidence": 0.89,
  "processing_time_ms": 2341,
  "query_id": "q_550e8400-e29b-41d4-a716-446655440000"
}
```

**필드 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `answer` | string | 생성된 답변 (인용 포함) |
| `sources` | array | 검색된 출처 목록 |
| `sources[].chunk_id` | string | 청크 고유 ID |
| `sources[].content` | string | 청크 내용 |
| `sources[].score` | float | 유사도 점수 (0~1) |
| `sources[].metadata` | object | 메타데이터 |
| `confidence` | float | 답변 신뢰도 (0~1) |
| `processing_time_ms` | integer | 처리 시간 (밀리초) |
| `query_id` | string | 질의 고유 ID (로그 추적용) |

#### Error Responses

```json
// 400 Bad Request - 잘못된 요청
{
  "detail": "query field is required"
}

// 401 Unauthorized - 인증 실패
{
  "detail": "Invalid or expired token"
}

// 429 Too Many Requests - 요청 제한 초과
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}

// 500 Internal Server Error - 서버 오류
{
  "detail": "Internal server error",
  "error_id": "err_123456"
}

// 504 Gateway Timeout - 타임아웃
{
  "detail": "Query processing timeout"
}
```

---

### 3.2 POST /index - 문서 인덱싱

새로운 문서를 파싱하고 벡터 DB에 인덱싱합니다.

#### Request

```http
POST /api/v1/rag/index
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

```
file: [PDF or HWP file]
document_type: "curriculum" or "school_plan"
metadata: {
  "policy_version": "2022개정",
  "scope_type": "NATIONAL",
  "institution_id": "협성고_2025"  // optional
}
```

**필드 설명:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `file` | file | ✓ | PDF 또는 HWP 파일 (최대 50MB) |
| `document_type` | enum | ✓ | "curriculum" 또는 "school_plan" |
| `metadata` | object | ✓ | 문서 메타데이터 |
| `metadata.policy_version` | string | ✓ | 교육과정 버전 |
| `metadata.scope_type` | enum | ✓ | "NATIONAL" 또는 "SCHOOL" |
| `metadata.institution_id` | string | 조건부 | 학교 ID (SCHOOL인 경우 필수) |

#### Response (202 Accepted)

```json
{
  "status": "processing",
  "job_id": "job_660e8400-e29b-41d4-a716-446655440001",
  "estimated_time_seconds": 120,
  "message": "Document indexing started"
}
```

#### Response (200 OK) - 완료 시

```json
{
  "status": "completed",
  "job_id": "job_660e8400-e29b-41d4-a716-446655440001",
  "chunks_created": 42,
  "processing_time_ms": 118234,
  "document_id": "doc_770e8400-e29b-41d4-a716-446655440002"
}
```

---

### 3.3 GET /status/{job_id} - 인덱싱 상태 확인

인덱싱 작업의 진행 상태를 확인합니다.

#### Request

```http
GET /api/v1/rag/status/{job_id}
Authorization: Bearer <token>
```

#### Response (200 OK)

```json
{
  "job_id": "job_660e8400-e29b-41d4-a716-446655440001",
  "status": "processing",
  "progress": 65,
  "current_step": "embedding_generation",
  "chunks_processed": 27,
  "chunks_total": 42,
  "started_at": "2025-11-20T22:00:00+09:00",
  "estimated_completion": "2025-11-20T22:02:00+09:00"
}
```

**status 값:**
- `pending`: 대기 중
- `processing`: 처리 중
- `completed`: 완료
- `failed`: 실패

---

### 3.4 GET /search - 청크 검색 (개발/디버깅용)

벡터 검색만 수행하고 LLM 생성 없이 결과를 반환합니다.

#### Request

```http
GET /api/v1/rag/search?query=최대공약수&top_k=5&policy_version=2022개정
Authorization: Bearer <token>
```

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `query` | string | ✓ | 검색 질의 |
| `top_k` | integer | ✗ | 결과 수 (기본값: 5) |
| `policy_version` | string | ✗ | 필터: 교육과정 버전 |
| `scope_type` | string | ✗ | 필터: NATIONAL/SCHOOL |
| `grade_level` | string | ✗ | 필터: 학년 |

#### Response (200 OK)

```json
{
  "results": [
    {
      "chunk_id": "chunk_123",
      "content": "최대공약수와 최소공배수는...",
      "score": 0.89,
      "metadata": {...}
    }
  ],
  "total": 5,
  "query_embedding_time_ms": 234
}
```

---

### 3.5 POST /feedback - 답변 피드백

사용자가 답변에 대한 피드백을 제공합니다.

#### Request

```http
POST /api/v1/rag/feedback
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "query_id": "q_550e8400-e29b-41d4-a716-446655440000",
  "rating": 5,
  "feedback_type": "helpful",
  "comment": "정확한 답변이었습니다"
}
```

**필드 설명:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `query_id` | string | ✓ | 질의 ID |
| `rating` | integer | ✓ | 평점 (1~5) |
| `feedback_type` | enum | ✗ | "helpful", "incorrect", "incomplete", "irrelevant" |
| `comment` | string | ✗ | 추가 코멘트 (최대 500자) |

#### Response (200 OK)

```json
{
  "status": "recorded",
  "feedback_id": "fb_880e8400-e29b-41d4-a716-446655440003"
}
```

---

### 3.6 GET /analytics - 사용 통계

RAG 시스템의 사용 통계를 조회합니다.

#### Request

```http
GET /api/v1/rag/analytics?start_date=2025-11-01&end_date=2025-11-20
Authorization: Bearer <token>
```

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `start_date` | string | ✗ | 시작일 (YYYY-MM-DD) |
| `end_date` | string | ✗ | 종료일 (YYYY-MM-DD) |

#### Response (200 OK)

```json
{
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-20"
  },
  "total_queries": 1234,
  "avg_response_time_ms": 2341,
  "avg_confidence": 0.87,
  "top_queries": [
    {
      "query": "최대공약수 소인수분해",
      "count": 45
    }
  ],
  "feedback_summary": {
    "total_feedback": 234,
    "avg_rating": 4.2,
    "helpful_count": 189,
    "incorrect_count": 12
  }
}
```

---

## 4. 데이터 모델

### 4.1 RAGQueryRequest

```typescript
interface RAGQueryRequest {
  query: string;
  filters?: {
    policy_version?: string;
    scope_type?: 'NATIONAL' | 'SCHOOL';
    institution_id?: string;
    grade_level?: string;
    domain?: string;
    curriculum_id?: string;
    node_id?: string;
  };
  top_k?: number;
  include_sources?: boolean;
  stream?: boolean;
}
```

### 4.2 RAGSource

```typescript
interface RAGSource {
  chunk_id: string;
  content: string;
  score: number;
  metadata: {
    policy_version: string;
    scope_type: 'NATIONAL' | 'SCHOOL';
    document_type: string;
    curriculum_code?: string;
    grade_level?: string;
    domain?: string;
    page_number?: number;
    source_file: string;
    [key: string]: any;
  };
}
```

### 4.3 RAGQueryResponse

```typescript
interface RAGQueryResponse {
  answer: string;
  sources: RAGSource[];
  confidence: number;
  processing_time_ms: number;
  query_id: string;
}
```

### 4.4 IndexingJobStatus

```typescript
interface IndexingJobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  chunks_processed: number;
  chunks_total: number;
  started_at: string;
  estimated_completion?: string;
  error_message?: string;
}
```

---

## 5. 에러 코드

### 5.1 HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 202 | Accepted | 비동기 작업 시작됨 |
| 400 | Bad Request | 잘못된 요청 (필수 필드 누락, 형식 오류) |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 422 | Unprocessable Entity | 검증 실패 |
| 429 | Too Many Requests | 요청 제한 초과 |
| 500 | Internal Server Error | 서버 내부 오류 |
| 503 | Service Unavailable | 서비스 일시 중단 (유지보수 등) |
| 504 | Gateway Timeout | 타임아웃 |

### 5.2 커스텀 에러 코드

```json
{
  "detail": "Error message",
  "error_code": "RAG_ERROR_CODE",
  "error_id": "err_123456"
}
```

| 에러 코드 | 설명 |
|----------|------|
| `PARSE_ERROR` | 문서 파싱 실패 |
| `VALIDATION_ERROR` | 메타데이터 검증 실패 |
| `VECTOR_SEARCH_ERROR` | 벡터 검색 실패 |
| `LLM_ERROR` | LLM 호출 실패 |
| `QUOTA_EXCEEDED` | API 할당량 초과 |
| `EMBEDDING_ERROR` | 임베딩 생성 실패 |
| `TIMEOUT_ERROR` | 처리 시간 초과 |

---

## 6. Rate Limiting

### 6.1 제한 정책

| 엔드포인트 | 제한 | 기간 |
|-----------|------|------|
| `/query` | 60 requests | 1분 |
| `/index` | 10 requests | 1시간 |
| `/search` | 100 requests | 1분 |
| `/feedback` | 100 requests | 1분 |

### 6.2 Rate Limit 헤더

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1700567890
```

---

## 7. 스트리밍 응답 (선택 기능)

### 7.1 Request

```json
{
  "query": "...",
  "stream": true
}
```

### 7.2 Response (Server-Sent Events)

```
data: {"type": "start", "query_id": "q_123"}

data: {"type": "source", "chunk_id": "chunk_123", "score": 0.89}

data: {"type": "token", "content": "아닙니다"}

data: {"type": "token", "content": ". "}

data: {"type": "citation", "chunk_id": "chunk_123"}

data: {"type": "done", "confidence": 0.89, "processing_time_ms": 2341}
```

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀  
**OpenAPI 스펙**: [swagger.yaml](./swagger.yaml) (별도 파일)
